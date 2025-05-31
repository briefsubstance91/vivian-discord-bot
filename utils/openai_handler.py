import os
import asyncio
import json
import base64
from openai import OpenAI
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Enhanced memory system (from Celeste)
user_conversations = {}  # user_id -> thread_id
conversation_context = {}  # user_id -> recent message history
MAX_CONTEXT_MESSAGES = 10  # Remember last 10 messages per user

# ============================================================================
# MEMORY SYSTEM (Enhanced from Celeste)
# ============================================================================

def get_user_thread(user_id):
    """Get or create a persistent thread for a user"""
    if user_id not in user_conversations:
        thread = client.beta.threads.create()
        user_conversations[user_id] = thread.id
        conversation_context[user_id] = []
        print(f"📝 Created new conversation thread for user {user_id}")
    return user_conversations[user_id]

def add_to_context(user_id, message_content, is_user=True):
    """Add message to user's conversation context"""
    if user_id not in conversation_context:
        conversation_context[user_id] = []
    
    role = "User" if is_user else "Vivian"
    timestamp = datetime.now().strftime("%H:%M")
    
    conversation_context[user_id].append({
        'role': role,
        'content': message_content,
        'timestamp': timestamp
    })
    
    if len(conversation_context[user_id]) > MAX_CONTEXT_MESSAGES:
        conversation_context[user_id] = conversation_context[user_id][-MAX_CONTEXT_MESSAGES:]

def get_conversation_context(user_id):
    """Get formatted conversation context for a user"""
    if user_id not in conversation_context or not conversation_context[user_id]:
        return "No previous conversation context."
    
    context_lines = []
    for msg in conversation_context[user_id][-5:]:
        content_preview = msg['content'][:100]
        if len(msg['content']) > 100:
            content_preview += "..."
        context_lines.append(f"{msg['timestamp']} {msg['role']}: {content_preview}")
    
    return "RECENT CONVERSATION:\n" + "\n".join(context_lines)

def clear_user_memory(user_id):
    """Clear conversation memory for a user"""
    if user_id in user_conversations:
        del user_conversations[user_id]
    if user_id in conversation_context:
        del conversation_context[user_id]
    print(f"🧹 Cleared memory for user {user_id}")

# ============================================================================
# GOOGLE SERVICES (Calendar + Gmail)
# ============================================================================

def get_google_service(service_name='calendar', version='v3'):
    """Get authenticated Google service (Calendar or Gmail)"""
    try:
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if not service_account_json:
            print(f"⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not found for {service_name}")
            return None
        
        service_account_info = json.loads(service_account_json)
        
        # Define scopes based on service
        if service_name == 'calendar':
            scopes = ['https://www.googleapis.com/auth/calendar.readonly']
        elif service_name == 'gmail':
            scopes = [
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.send',
                'https://www.googleapis.com/auth/gmail.compose'
            ]
        else:
            scopes = ['https://www.googleapis.com/auth/calendar.readonly']
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )
        
        service = build(service_name, version, credentials=credentials)
        print(f"✅ Google {service_name.title()} service connected successfully")
        return service
        
    except Exception as e:
        print(f"❌ Failed to connect to Google {service_name}: {e}")
        return None

# Initialize services
calendar_service = get_google_service('calendar', 'v3')
gmail_service = get_google_service('gmail', 'v1')

# ============================================================================
# CALENDAR FUNCTIONS (Enhanced from existing)
# ============================================================================

def get_calendar_events(service, days_ahead=7):
    """Get events from Google Calendar"""
    if not service:
        print("📅 Using mock calendar data (no Google Calendar connection)")
        return get_mock_calendar_events()
    
    try:
        now = datetime.utcnow()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        end_time = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        print(f"📅 Fetching events from calendar: {calendar_id}")
        print(f"📅 Date range: {days_ahead} days from today")
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time,
            timeMax=end_time,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            print('📅 No upcoming events found in calendar')
            return []
        
        calendar_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            if 'T' in start:
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:
                start_dt = datetime.strptime(start, '%Y-%m-%d')
            
            # Calculate duration
            if end and 'T' in end:
                end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                duration = end_dt - start_dt
                duration_min = int(duration.total_seconds() / 60)
                if duration_min < 60:
                    duration_str = f"{duration_min} min"
                else:
                    hours = duration_min // 60
                    mins = duration_min % 60
                    if mins > 0:
                        duration_str = f"{hours}h {mins}min"
                    else:
                        duration_str = f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                duration_str = "All day"
            
            calendar_events.append({
                "title": event.get('summary', 'Untitled'),
                "start_time": start_dt,
                "duration": duration_str,
                "description": event.get('description', ''),
                "location": event.get('location', ''),
                "attendees": [att.get('email', '') for att in event.get('attendees', [])]
            })
        
        print(f"✅ Found {len(calendar_events)} calendar events")
        return calendar_events
        
    except HttpError as e:
        if e.resp.status == 404:
            print(f"❌ Calendar not found. Make sure you've shared your calendar with the service account")
        elif e.resp.status == 403:
            print(f"❌ No permission to read calendar. Check that the service account has access")
        else:
            print(f"❌ HTTP error fetching events: {e}")
        return get_mock_calendar_events()
    except Exception as e:
        print(f"❌ Error fetching Google Calendar events: {e}")
        return get_mock_calendar_events()

def get_mock_calendar_events():
    """Mock calendar data - fallback when no real calendar available"""
    today = datetime.now()
    
    mock_events = [
        {
            "title": "Team Standup",
            "start_time": today.replace(hour=9, minute=30),
            "duration": "30 min",
            "description": "Daily sync with development team",
            "location": "Zoom",
            "attendees": ["team@company.com"]
        },
        {
            "title": "Strategy Review", 
            "start_time": today.replace(hour=14, minute=0),
            "duration": "1 hour",
            "description": "Q4 planning and roadmap review",
            "location": "Conference Room A",
            "attendees": ["manager@company.com", "strategy@company.com"]
        },
        {
            "title": "Client Call - Project Alpha",
            "start_time": today.replace(hour=16, minute=30),
            "duration": "45 min",
            "description": "Progress update and next steps",
            "location": "Teams",
            "attendees": ["client@clientcompany.com"]
        }
    ]
    
    return mock_events

# ============================================================================
# GMAIL FUNCTIONS (New)
# ============================================================================

def search_gmail_messages(service, query, max_results=10):
    """Search Gmail messages"""
    if not service:
        print("📧 Using mock email data (no Gmail connection)")
        return get_mock_email_data()
    
    try:
        # Use Gmail's search to find messages
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return []
        
        email_list = []
        for msg in messages[:max_results]:
            # Get full message details
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            # Extract headers
            headers = message['payload'].get
