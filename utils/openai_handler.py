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
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            # Extract body text
            body = extract_email_body(message['payload'])
            
            # Parse date
            try:
                from email.utils import parsedate_to_datetime
                parsed_date = parsedate_to_datetime(date)
            except:
                parsed_date = datetime.now()
            
            email_list.append({
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'date': parsed_date,
                'body_preview': body[:200] + '...' if len(body) > 200 else body,
                'full_body': body
            })
        
        print(f"✅ Found {len(email_list)} email messages")
        return email_list
        
    except Exception as e:
        print(f"❌ Error searching Gmail: {e}")
        return get_mock_email_data()

def extract_email_body(payload):
    """Extract text from email payload"""
    body = ""
    
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                body = base64.urlsafe_b64decode(data).decode('utf-8')
                break
            elif part['mimeType'] == 'text/html':
                # Fallback to HTML if no plain text
                data = part['body']['data']
                html_body = base64.urlsafe_b64decode(data).decode('utf-8')
                # Simple HTML to text conversion
                import re
                body = re.sub('<[^<]+?>', '', html_body)
                break
    elif payload['mimeType'] == 'text/plain':
        data = payload['body']['data']
        body = base64.urlsafe_b64decode(data).decode('utf-8')
    
    return body.strip()

def get_recent_emails(service, max_results=10):
    """Get recent emails"""
    if not service:
        return get_mock_email_data()
    
    try:
        # Get recent messages
        results = service.users().messages().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        email_list = []
        for msg in messages:
            message = service.users().messages().get(
                userId='me',
                id=msg['id'],
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            body = extract_email_body(message['payload'])
            
            try:
                from email.utils import parsedate_to_datetime
                parsed_date = parsedate_to_datetime(date)
            except:
                parsed_date = datetime.now()
            
            # Check if unread
            labels = message.get('labelIds', [])
            is_unread = 'UNREAD' in labels
            
            email_list.append({
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'date': parsed_date,
                'body_preview': body[:150] + '...' if len(body) > 150 else body,
                'is_unread': is_unread
            })
        
        return email_list
        
    except Exception as e:
        print(f"❌ Error getting recent emails: {e}")
        return get_mock_email_data()

def get_mock_email_data():
    """Mock email data - fallback when no Gmail connection"""
    today = datetime.now()
    
    mock_emails = [
        {
            'id': 'mock1',
            'subject': 'Project Alpha Update',
            'sender': 'john.doe@company.com',
            'date': today - timedelta(hours=2),
            'body_preview': 'Hi, just wanted to update you on the progress of Project Alpha. We\'ve completed the first phase...',
            'is_unread': True
        },
        {
            'id': 'mock2', 
            'subject': 'Meeting Follow-up',
            'sender': 'sarah.smith@partner.com',
            'date': today - timedelta(hours=5),
            'body_preview': 'Thank you for the productive meeting today. As discussed, here are the next steps...',
            'is_unread': False
        },
        {
            'id': 'mock3',
            'subject': 'Q4 Budget Review',
            'sender': 'finance@company.com',
            'date': today - timedelta(days=1),
            'body_preview': 'Please review the attached Q4 budget proposal and provide your feedback by Friday...',
            'is_unread': True
        }
    ]
    
    return mock_emails

def send_email(service, to, subject, body, sender_email=None):
    """Send an email via Gmail"""
    if not service:
        return "📧 Email sending not available (no Gmail connection). Draft saved to your notes."
    
    try:
        import email.mime.text
        import email.mime.multipart
        
        # Create message
        message = email.mime.multipart.MIMEMultipart()
        message['to'] = to
        message['subject'] = subject
        
        if sender_email:
            message['from'] = sender_email
        
        # Add body
        msg_body = email.mime.text.MIMEText(body)
        message.attach(msg_body)
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send message
        send_message = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return f"✅ Email sent successfully to {to}"
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return f"❌ Failed to send email: {str(e)}"

# ============================================================================
# FUNCTION EXECUTION (Enhanced with Debug)
# ============================================================================

def execute_function(function_name, arguments):
    """Execute the called function and return results"""
    
    # Calendar functions
    if function_name == "get_today_schedule":
        events = get_calendar_events(calendar_service, days_ahead=1)
        today = datetime.now().date()
        today_events = [e for e in events if e['start_time'].date() == today]
        
        print(f"🔍 DEBUG: Found {len(events)} total events, {len(today_events)} today events")
        for event in today_events:
            print(f"🔍 DEBUG: Today event - {event['title']} at {event['start_time']}")
        
        if not today_events:
            result = "No events scheduled for today"
        else:
            event_list = []
            for event in today_events:
                time_str = event['start_time'].strftime('%I:%M %p')
                attendee_info = f" (with {len(event['attendees'])} attendees)" if event['attendees'] else ""
                event_list.append(f"• {time_str}: {event['title']} ({event['duration']}){attendee_info}")
                if event['location']:
                    event_list.append(f"  📍 {event['location']}")
            
            result = "📅 Today's Schedule:\n" + "\n".join(event_list)
        
        print(f"🔍 DEBUG: get_today_schedule returning: {result[:200]}...")
        return result
    
    elif function_name == "get_tomorrow_schedule":
        events = get_calendar_events(calendar_service, days_ahead=2)
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        tomorrow_events = [e for e in events if e['start_time'].date() == tomorrow]
        
        print(f"🔍 DEBUG: Found {len(events)} total events, {len(tomorrow_events)} tomorrow events")
        for event in tomorrow_events:
            print(f"🔍 DEBUG: Tomorrow event - {event['title']} at {event['start_time']}")
        
        if not tomorrow_events:
            result = "No events scheduled for tomorrow"
        else:
            event_list = []
            for event in tomorrow_events:
                time_str = event['start_time'].strftime('%I:%M %p')
                attendee_info = f" (with {len(event['attendees'])} attendees)" if event['attendees'] else ""
                event_list.append(f"• {time_str}: {event['title']} ({event['duration']}){attendee_info}")
                if event['location']:
                    event_list.append(f"  📍 {event['location']}")
            
            result = "📅 Tomorrow's Schedule:\n" + "\n".join(event_list)
        
        print(f"🔍 DEBUG: get_tomorrow_schedule returning: {result[:200]}...")
        return result
    
    elif function_name == "get_upcoming_events":
        days = arguments.get('days', 7)
        events = get_calendar_events(calendar_service, days_ahead=days)
        
        print(f"🔍 DEBUG: Found {len(events)} events for next {days} days")
        
        if not events:
            result = f"No events found in the next {days} days"
        else:
            event_list = []
            today = datetime.now().date()
            
            for event in events[:10]:
                event_date = event['start_time'].date()
                
                if event_date == today:
                    time_str = f"Today at {event['start_time'].strftime('%I:%M %p')}"
                elif event_date == today + timedelta(days=1):
                    time_str = f"Tomorrow at {event['start_time'].strftime('%I:%M %p')}"
                else:
                    time_str = event['start_time'].strftime('%m/%d at %I:%M %p')
                
                event_list.append(f"• {event['title']} - {time_str}")
            
            if len(event_list) > 10:
                event_list = event_list[:10]
                event_list.append("... and more")
            
            result = f"📅 Upcoming Events (Next {days} days):\n" + "\n".join(event_list)
        
        print(f"🔍 DEBUG: get_upcoming_events returning: {result[:200]}...")
        return result
    
    elif function_name == "find_free_time":
        duration = arguments.get('duration', 60)
        date_str = arguments.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            target_date = datetime.now()
        
        days_ahead = max(1, (target_date.date() - datetime.now().date()).days + 1)
        events = get_calendar_events(calendar_service, days_ahead=days_ahead)
        
        target_events = [e for e in events if e['start_time'].date() == target_date.date()]
        
        # Simple free time finding logic
        free_slots = []
        business_start = target_date.replace(hour=9, minute=0)
        business_end = target_date.replace(hour=18, minute=0)
        
        target_events.sort(key=lambda x: x['start_time'])
        
        current_time = business_start
        
        for event in target_events:
            event_start = event['start_time']
            
            if current_time < event_start:
                gap_minutes = (event_start - current_time).total_seconds() / 60
                if gap_minutes >= duration:
                    free_slots.append(f"{current_time.strftime('%I:%M %p')} - {event_start.strftime('%I:%M %p')}")
            
            # Move current time to after this event
            duration_min = 60
            if "min" in event['duration']:
                try:
                    duration_min = int(event['duration'].split()[0])
                except:
                    pass
            elif "hour" in event['duration']:
                try:
                    hours = int(event['duration'].split()[0])
                    duration_min = hours * 60
                except:
                    pass
            
            current_time = event_start + timedelta(minutes=duration_min)
        
        if current_time < business_end:
            gap_minutes = (business_end - current_time).total_seconds() / 60
            if gap_minutes >= duration:
                free_slots.append(f"{current_time.strftime('%I:%M %p')} - {business_end.strftime('%I:%M %p')}")
        
        if not free_slots:
            result = f"No free blocks of {duration}+ minutes found on {target_date.strftime('%Y-%m-%d')}"
        else:
            result = f"⏰ Free time slots on {target_date.strftime('%Y-%m-%d')} ({duration}+ min blocks):\n" + "\n".join([f"• {slot}" for slot in free_slots])
        
        print(f"🔍 DEBUG: find_free_time returning: {result[:200]}...")
        return result
    
    # Gmail functions
    elif function_name == "search_emails":
        query = arguments.get('query', '')
        max_results = arguments.get('max_results', 10)
        
        emails = search_gmail_messages(gmail_service, query, max_results)
        
        print(f"🔍 DEBUG: Found {len(emails)} emails for query '{query}'")
        
        if not emails:
            result = f"No emails found matching '{query}'"
        else:
            email_list = []
            for email in emails:
                date_str = email['date'].strftime('%m/%d %I:%M %p')
                unread_indicator = "🔵 " if email.get('is_unread') else ""
                email_list.append(f"• {unread_indicator}{email['subject']}\n  From: {email['sender']} ({date_str})\n  Preview: {email['body_preview']}")
            
            result = f"📧 Email Search Results for '{query}':\n\n" + "\n\n".join(email_list)
        
        print(f"🔍 DEBUG: search_emails returning: {result[:200]}...")
        return result
    
    elif function_name == "get_recent_emails":
        max_results = arguments.get('max_results', 10)
        
        emails = get_recent_emails(gmail_service, max_results)
        
        print(f"🔍 DEBUG: Found {len(emails)} recent emails")
        
        if not emails:
            result = "No recent emails found"
        else:
            email_list = []
            unread_count = 0
            
            for email in emails:
                date_str = email['date'].strftime('%m/%d %I:%M %p')
                unread_indicator = "🔵 " if email.get('is_unread') else ""
                if email.get('is_unread'):
                    unread_count += 1
                
                email_list.append(f"• {unread_indicator}{email['subject']}\n  From: {email['sender']} ({date_str})\n  Preview: {email['body_preview']}")
            
            result = f"📧 Recent Emails ({unread_count} unread):\n\n" + "\n\n".join(email_list)
        
        print(f"🔍 DEBUG: get_recent_emails returning: {result[:200]}...")
        return result
    
    elif function_name == "send_email":
        to = arguments.get('to', '')
        subject = arguments.get('subject', '')
        body = arguments.get('body', '')
        
        if not to or not subject or not body:
            result = "Missing required email fields: to, subject, and body are all required"
        else:
            result = send_email(gmail_service, to, subject, body)
        
        print(f"🔍 DEBUG: send_email returning: {result[:200]}...")
        return result
    
    else:
        result = f"Unknown function: {function_name}"
        print(f"🔍 DEBUG: Unknown function {function_name}")
        return result

async def handle_function_calls(run, thread_id):
    """Handle function calls from the assistant"""
    tool_outputs = []
    
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        print(f"🔧 Executing function: {function_name} with args: {arguments}")
        
        # Execute the function
        output = execute_function(function_name, arguments)
        
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": output
        })
    
    # Submit the function outputs back to the assistant
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run.id,
        tool_outputs=tool_outputs
    )

def should_give_detailed_response(user_message):
    """Check if user is asking for a detailed/comprehensive response"""
    detail_triggers = [
        'deep dive', 'detailed', 'comprehensive', 'tell me more', 'elaborate',
        'break it down', 'full breakdown', 'in depth', 'thorough', 'complete',
        'everything about', 'walk me through', 'explain fully', 'analysis'
    ]
    
    return any(trigger in user_message.lower() for trigger in detail_triggers)

def format_for_discord(response, is_detailed=False):
    """Clean up response for Discord formatting"""
    
    # Remove excessive line breaks
    response = response.replace('\n\n\n', '\n\n')
    response = response.replace('\n\n\n\n', '\n\n')
    
    # Remove bold from every concept (too much bolding)
    bold_count = response.count('**')
    if bold_count > 6:  # More than 3 bold phrases
        # Keep only the first 2 bold phrases
        parts = response.split('**')
        new_response = parts[0]
        bold_used = 0
        for i in range(1, len(parts)):
            if bold_used < 4:  # Keep first 2 bold phrases (4 asterisks)
                new_response += '**' + parts[i]
                bold_used += 1
            else:
                new_response += parts[i]
        response = new_response
    
    # Different length limits based on detail level
    if is_detailed:
        max_length = 3000  # Allow longer responses when details requested
    else:
        max_length = 1500  # Keep responses focused for productivity
    
    if len(response) > max_length:
        # Find a good breaking point
        sentences = response.split('. ')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence + '. ') < (max_length - 100):
                truncated += sentence + '. '
            else:
                if is_detailed:
                    truncated += "\n\n*Want me to continue with more details on any specific aspect?*"
                else:
                    truncated += "\n\n*Need more details? Just ask!*"
                break
        response = truncated
    
    return response.strip()

async def get_openai_response(user_message: str, user_id: int, clear_memory: bool = False) -> str:
    """Enhanced OpenAI response with memory and function calling"""
    try:
        # Handle memory clearing
        if clear_memory:
            clear_user_memory(user_id)
            return "🧹 **Memory cleared!** Starting fresh conversation."
        
        # Get or create thread for this specific user (persistent memory)
        thread_id = get_user_thread(user_id)
        
        # Add to conversation context
        conversation_history = get_conversation_context(user_id)
        add_to_context(user_id, user_message, is_user=True)
        
        print(f"📨 Sending message to OpenAI Assistant (Thread: {thread_id}, User: {user_id})")
        
        # Clean the user message (remove bot mentions)
        clean_message = user_message.replace(f'<@{os.getenv("BOT_USER_ID", "")}>', '').strip()
        
        # Enhanced message with conversation context
        enhanced_message = f"""CONVERSATION CONTEXT:
{conversation_history}

CURRENT REQUEST: {clean_message}

INSTRUCTIONS:
- This is a continuing conversation - refer to previous context when relevant
- You are Vivian, a strategic productivity assistant
- For calendar/schedule questions, use calendar functions
- For email questions, use email functions  
- Provide actionable insights focused on productivity and efficiency
- Be conversational but strategic
- Remember our conversation history and build on previous discussions"""
        
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=enhanced_message
        )
        
        print(f"✅ Message added to thread: {message.id}")
        
        # Check if user wants detailed response
        wants_detail = should_give_detailed_response(clean_message)
        
        # Create run with dynamic instructions
        if wants_detail:
            instructions = "You are Vivian Spencer, a strategic productivity assistant. Provide comprehensive insights but stay focused and actionable. Every point should add strategic value. Use calendar and email functions when users ask about schedule, meetings, or email management. Focus on productivity patterns and strategic time management."
            additional = "REQUIRED: Each sentence should deliver strategic value. Comprehensive but focused on productivity. Use available functions for calendar and email queries, then provide strategic analysis."
        else:
            instructions = "You are Vivian Spencer, a strategic productivity assistant. Keep responses conversational and focused (800-1500 chars). Think like a smart executive assistant - strategic but approachable. When users ask about calendar/schedule/emails, use the available functions, then provide strategic insights about their time and communication patterns."
            additional = "Sound strategic but human. Focus on actionable productivity insights. Use functions for calendar/email queries, then analyze patterns strategically. Less corporate speak, more strategic friend."

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions=instructions,
            additional_instructions=additional
        )
        
        print(f"🏃 Run created: {run.id}")
        
        # Wait for completion with function call handling
        for _ in range(30):  # Wait up to ~30 seconds
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            print(f"🔄 Run status: {run_status.status}")
            
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                print("🔧 Function call required")
                await handle_function_calls(run_status, thread_id)
                continue
            elif run_status.status == "failed":
                print(f"❌ Run failed: {run_status.last_error}")
                raise Exception("❌ Run failed.")
            
            await asyncio.sleep(1)
        else:
            raise TimeoutError("⏱️ Timed out waiting for assistant to complete.")
        
        # Get response
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                response = msg.content[0].text.value
                print(f"✅ Got response: {response[:100]}...")
                
                # Add to conversation context
                add_to_context(user_id, response, is_user=False)
                
                # Apply Discord formatting and return
                return format_for_discord(response, wants_detail)
        
        return "⚠️ No assistant response found."
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "An error occurred while communicating with the assistant."
