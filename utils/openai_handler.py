import os
import asyncio
import json
from openai import OpenAI
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Store user threads in memory
user_threads = {}

def get_google_calendar_service():
    """Get authenticated Google Calendar service using service account"""
    try:
        # Get service account JSON from environment variable
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        
        if not service_account_json:
            print("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not found in environment")
            print("⚠️ Please add your service account JSON to Railway environment variables")
            return None
        
        print("🔧 Found service account JSON, parsing...")
        
        # Parse the JSON string
        try:
            service_account_info = json.loads(service_account_json)
            print("✅ Service account JSON parsed successfully")
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse service account JSON: {e}")
            print("💡 Make sure you copied the entire JSON content including { and }")
            return None
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )
        
        # Note: Domain-wide delegation only works with Google Workspace accounts
        # For regular Gmail accounts, skip delegation and share calendar with service account
        
        # Build the service
        service = build('calendar', 'v3', credentials=credentials)
        print("✅ Google Calendar service connected successfully")
        
        # Test the connection
        try:
            calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
            print(f"🔧 Testing connection to calendar: {calendar_id}")
            
            # Try to get calendar info
            calendar = service.calendars().get(calendarId=calendar_id).execute()
            print(f"✅ Connected to calendar: {calendar.get('summary', 'Unknown')}")
            
        except HttpError as e:
            if e.resp.status == 404:
                print(f"❌ Calendar not found: {calendar_id}")
                print("💡 Make sure to share your calendar with the service account email")
            elif e.resp.status == 403:
                print(f"❌ No permission to access calendar: {calendar_id}")
                print("💡 Share your calendar with the service account and give it 'See all event details' permission")
            else:
                print(f"❌ Error accessing calendar: {e}")
        
        return service
        
    except Exception as e:
        print(f"❌ Failed to connect to Google Calendar: {e}")
        print(f"Error type: {type(e).__name__}")
        return None

def get_calendar_events(service, days_ahead=7):
    """Get events from Google Calendar"""
    if not service:
        print("📅 Using mock calendar data (no Google Calendar connection)")
        return get_mock_calendar_events()
    
    try:
        # Get date range
        now = datetime.utcnow()
        start_time = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
        end_time = (now + timedelta(days=days_ahead)).isoformat() + 'Z'
        
        # Use the calendar ID from environment or default to primary
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        print(f"📅 Fetching events from calendar: {calendar_id}")
        print(f"📅 Date range: {days_ahead} days from today")
        
        # Call the Calendar API
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
            
            # Parse start time
            if 'T' in start:  # It's a datetime
                start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            else:  # It's a date
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
                "location": event.get('location', '')
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
        print(f"Error type: {type(e).__name__}")
        return get_mock_calendar_events()

def get_mock_calendar_events():
    """Mock calendar data - fallback when no real calendar available"""
    today = datetime.now()
    
    mock_events = [
        {
            "title": "Team Standup",
            "start_time": today.replace(hour=9, minute=30),
            "duration": "30 min",
            "description": "Daily sync",
            "location": "Zoom"
        },
        {
            "title": "Strategy Review", 
            "start_time": today.replace(hour=14, minute=0),
            "duration": "1 hour",
            "description": "Q4 planning",
            "location": "Conference Room"
        },
        {
            "title": "Client Call - Project Alpha",
            "start_time": today.replace(hour=16, minute=30),
            "duration": "45 min",
            "description": "Progress update",
            "location": "Teams"
        }
    ]
    
    return mock_events

# Initialize Google Calendar service
print("🔧 Initializing Google Calendar connection...")
calendar_service = get_google_calendar_service()

def execute_function(function_name, arguments):
    """Execute the called function and return results"""
    
    if function_name == "get_today_schedule":
        # Get all events for the next 7 days
        events = get_calendar_events(calendar_service, days_ahead=1)
        
        # Filter for today only
        today = datetime.now().date()
        today_events = [e for e in events if e['start_time'].date() == today]
        
        if not today_events:
            return "No events scheduled for today"
        
        event_list = []
        for event in today_events:
            time_str = event['start_time'].strftime('%I:%M %p')
            event_list.append(f"• {time_str}: {event['title']} ({event['duration']})")
        
        return "📅 Today's Schedule:\n" + "\n".join(event_list)
    
    elif function_name == "get_tomorrow_schedule":
        # Get events for next 2 days
        events = get_calendar_events(calendar_service, days_ahead=2)
        
        # Filter for tomorrow only
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        tomorrow_events = [e for e in events if e['start_time'].date() == tomorrow]
        
        if not tomorrow_events:
            return "No events scheduled for tomorrow"
        
        event_list = []
        for event in tomorrow_events:
            time_str = event['start_time'].strftime('%I:%M %p')
            event_list.append(f"• {time_str}: {event['title']} ({event['duration']})")
        
        return "📅 Tomorrow's Schedule:\n" + "\n".join(event_list)
    
    elif function_name == "get_upcoming_events":
        days = arguments.get('days', 7)
        events = get_calendar_events(calendar_service, days_ahead=days)
        
        if not events:
            return f"No events found in the next {days} days"
        
        event_list = []
        today = datetime.now().date()
        
        for event in events:
            event_date = event['start_time'].date()
            
            if event_date == today:
                time_str = f"Today at {event['start_time'].strftime('%I:%M %p')}"
            elif event_date == today + timedelta(days=1):
                time_str = f"Tomorrow at {event['start_time'].strftime('%I:%M %p')}"
            else:
                time_str = event['start_time'].strftime('%m/%d at %I:%M %p')
            
            event_list.append(f"• {event['title']} - {time_str}")
        
        # Limit to first 10 events for readability
        if len(event_list) > 10:
            event_list = event_list[:10]
            event_list.append("... and more")
        
        return f"📅 Upcoming Events (Next {days} days):\n" + "\n".join(event_list)
    
    elif function_name == "find_free_time":
        duration = arguments.get('duration', 60)
        date_str = arguments.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Parse the date
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            target_date = datetime.now()
        
        # Get events for the target date
        days_ahead = max(1, (target_date.date() - datetime.now().date()).days + 1)
        events = get_calendar_events(calendar_service, days_ahead=days_ahead)
        
        # Filter events for the target date
        target_events = [e for e in events if e['start_time'].date() == target_date.date()]
        
        # Find free slots
        free_slots = []
        business_start = target_date.replace(hour=9, minute=0)
        business_end = target_date.replace(hour=18, minute=0)
        
        # Sort events by start time
        target_events.sort(key=lambda x: x['start_time'])
        
        current_time = business_start
        
        for event in target_events:
            event_start = event['start_time']
            
            # Check if there's a gap before this event
            if current_time < event_start:
                gap_minutes = (event_start - current_time).total_seconds() / 60
                if gap_minutes >= duration:
                    free_slots.append(f"{current_time.strftime('%I:%M %p')} - {event_start.strftime('%I:%M %p')}")
            
            # Move current time to after this event
            duration_min = 60  # default
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
        
        # Check time after last event
        if current_time < business_end:
            gap_minutes = (business_end - current_time).total_seconds() / 60
            if gap_minutes >= duration:
                free_slots.append(f"{current_time.strftime('%I:%M %p')} - {business_end.strftime('%I:%M %p')}")
        
        if not free_slots:
            return f"No free blocks of {duration}+ minutes found on {target_date.strftime('%Y-%m-%d')}"
        
        return f"⏰ Free time slots on {target_date.strftime('%Y-%m-%d')} ({duration}+ min blocks):\n" + "\n".join([f"• {slot}" for slot in free_slots])
    
    else:
        return f"Unknown function: {function_name}"

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

def should_refresh_thread(thread_data):
    """Check if thread should be refreshed (24 hours old or 50+ messages)"""
    max_age = timedelta(hours=24)
    max_messages = 50
    
    return (datetime.now() - thread_data['created'] > max_age) or \
           (thread_data['message_count'] > max_messages)

def get_or_create_thread(user_id):
    """Get existing thread for user or create a new one"""
    thread_key = f"thread_{user_id}"
    
    # Check if thread should be refreshed
    if thread_key in user_threads and should_refresh_thread(user_threads[thread_key]):
        print(f"🔄 Refreshing thread for user {user_id}")
        del user_threads[thread_key]
    
    # Create new thread if needed
    if thread_key not in user_threads:
        thread = client.beta.threads.create()
        user_threads[thread_key] = {
            'id': thread.id,
            'created': datetime.now(),
            'message_count': 0
        }
        print(f"✨ Created new thread: {thread.id} for user {user_id}")
    
    return user_threads[thread_key]

def should_give_detailed_response(user_message):
    """Check if user is asking for a detailed/comprehensive response"""
    detail_triggers = [
        'deep dive', 'detailed', 'comprehensive', 'tell me more', 'elaborate',
        'break it down', 'full breakdown', 'in depth', 'thorough', 'complete',
        'everything about', 'walk me through', 'explain fully'
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
        max_length = 1200  # Keep casual responses tight
    
    if len(response) > max_length:
        # Find a good breaking point
        sentences = response.split('. ')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence + '. ') < (max_length - 100):
                truncated += sentence + '. '
            else:
                if is_detailed:
                    truncated += "\n\n*This is just the foundation - want me to go deeper on any specific aspect?*"
                else:
                    truncated += "\n\n*Want the detailed breakdown?*"
                break
        response = truncated
    
    return response.strip()

async def get_openai_response(user_message: str, user_id: int) -> str:
    try:
        # TEMPORARY FIX: Force new thread every message to avoid caching issues
        user_threads.clear()
        
        # Get or create thread for this specific user
        thread_data = get_or_create_thread(user_id)
        thread_id = thread_data['id']
        
        print(f"📨 Sending message to OpenAI Assistant (Thread: {thread_id}, User: {user_id})")
        
        # Clean the user message (remove bot mentions)
        clean_message = user_message.replace(f'<@1373036719930085567>', '').strip()
        
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=clean_message
        )
        
        # Increment message count
        thread_data['message_count'] += 1
        print(f"✅ Message added to thread: {message.id}")
        
        # Check if user wants detailed response
        wants_detail = should_give_detailed_response(clean_message)
        
        # Create run with dynamic instructions based on request type
        if wants_detail:
            instructions = "You are Vivian Spencer. Provide comprehensive strategic insights but cut the fluff. Every paragraph should add new value. Write conversationally but efficiently - no rambling or repetitive explanations. Pack strategic insights densely. When analyzing calendar data, focus on strategic patterns and time management insights."
            additional = "FORBIDDEN: Filler phrases, repetitive concepts, obvious statements. REQUIRED: Each sentence should deliver strategic value. Comprehensive but concise. Use calendar functions when users ask about schedule, meetings, or time management."
        else:
            instructions = "You are Vivian Spencer. Keep this conversational and strategic (800-1200 chars). Write like you're texting a smart friend - no formal language or corporate speak. Weave insights together naturally. End with strategic perspective or question. When users ask about calendar/schedule, use the available functions to get their real data, then provide strategic insights."
            additional = "Sound like Vivian - strategic, composed, insightful. Avoid phrases like 'The key is' or 'It's also smart to'. More like 'Here's what I see working' or 'The pattern I notice'. Strategic advisor voice, not generic advice. Use calendar functions for schedule queries, then analyze patterns strategically."

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
                
                # Apply Discord formatting and return
                return format_for_discord(response, wants_detail)
        
        return "⚠️ No assistant response found."
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "An error occurred while communicating with the assistant."
