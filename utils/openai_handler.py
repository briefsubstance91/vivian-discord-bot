import os
import asyncio
import json
from openai import OpenAI
from datetime import datetime, timedelta
from caldav import DAVClient
from icalendar import Calendar
import requests
from requests.auth import HTTPBasicAuth

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Store user threads in memory
user_threads = {}

def debug_caldav_connection():
    """Debug CalDAV connection issues"""
    email = os.getenv('GOOGLE_EMAIL')
    app_password = os.getenv('GOOGLE_APP_PASSWORD')
    
    print(f"🔧 Debug CalDAV Connection:")
    print(f"   Email: {email}")
    print(f"   Password: {'*' * len(app_password) if app_password else 'None'}")
    
    if not email:
        print("❌ GOOGLE_EMAIL environment variable not set")
        return False
    
    if not app_password:
        print("❌ GOOGLE_APP_PASSWORD environment variable not set")
        return False
    
    if len(app_password) != 16:
        print(f"⚠️ App password length is {len(app_password)}, should be 16 characters")
    
    # Test the CalDAV URL
    caldav_url = f"https://apidata.googleusercontent.com/caldav/v2/{email}/events/"
    print(f"🔗 CalDAV URL: {caldav_url}")
    
    try:
        # Test basic auth
        response = requests.get(caldav_url, auth=HTTPBasicAuth(email, app_password), timeout=10)
        print(f"📡 HTTP Response: {response.status_code}")
        
        if response.status_code == 401:
            print("❌ Authentication failed - check email/password")
        elif response.status_code == 200:
            print("✅ Basic auth working")
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
    
    return True

def setup_caldav_calendar():
    """Setup CalDAV connection to Google Calendar with enhanced debugging"""
    
    # Add debug call
    if not debug_caldav_connection():
        return None
    
    try:
        email = os.getenv('GOOGLE_EMAIL')
        app_password = os.getenv('GOOGLE_APP_PASSWORD')
        
        if not email or not app_password:
            print("⚠️ No CalDAV credentials found - using mock data")
            print("ℹ️ Add GOOGLE_EMAIL and GOOGLE_APP_PASSWORD environment variables")
            return None
        
        # Google's CalDAV URL
        caldav_url = f"https://apidata.googleusercontent.com/caldav/v2/{email}/events/"
        
        print(f"🔗 Attempting CalDAV connection to: {caldav_url}")
        
        # Create DAV client
        client_dav = DAVClient(
            url=caldav_url,
            username=email,
            password=app_password
        )
        
        print("🔧 DAV Client created, getting principal...")
        
        # Get principal and calendars
        principal = client_dav.principal()
        print("🔧 Principal obtained, getting calendars...")
        
        calendars = principal.calendars()
        print(f"🔧 Found {len(calendars)} calendars")
        
        if calendars:
            print("✅ CalDAV Google Calendar connected successfully")
            calendar = calendars[0]
            
            # Test getting events
            print("🔧 Testing event retrieval...")
            test_events = calendar.search(
                start=datetime.now(),
                end=datetime.now() + timedelta(days=1),
                event=True
            )
            print(f"🔧 Test search returned {len(test_events)} events")
            
            return calendar
        else:
            print("❌ No calendars found via CalDAV")
            return None
            
    except Exception as e:
        print(f"❌ CalDAV setup failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        print("💡 Make sure you have 2FA enabled and created an app password")
        return None

def get_caldav_events(calendar, days_ahead=1):
    """Get events from CalDAV calendar"""
    if not calendar:
        print("📅 Using mock calendar data (no CalDAV connection)")
        return get_mock_calendar_events()
    
    try:
        # Get date range
        start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=days_ahead)
        
        print(f"📅 Fetching events from {start.date()} to {end.date()}")
        
        # Search for events
        events = calendar.search(
            start=start,
            end=end,
            event=True,
            expand=True
        )
        
        calendar_events = []
        
        for event in events:
            try:
                # Parse the iCalendar data
                cal_data = Calendar.from_ical(event.data)
                
                for component in cal_data.walk():
                    if component.name == "VEVENT":
                        summary = str(component.get('summary', 'Untitled'))
                        dtstart = component.get('dtstart')
                        dtend = component.get('dtend')
                        
                        if dtstart and dtstart.dt:
                            start_time = dtstart.dt
                            
                            # Handle timezone-aware datetime
                            if hasattr(start_time, 'replace'):
                                # Calculate duration
                                if dtend and dtend.dt:
                                    duration = dtend.dt - start_time
                                    duration_str = f"{int(duration.total_seconds() / 60)} min"
                                else:
                                    duration_str = "Unknown"
                                
                                calendar_events.append({
                                    "title": summary,
                                    "start_time": start_time,
                                    "duration": duration_str
                                })
                                
            except Exception as e:
                print(f"⚠️ Error parsing event: {e}")
                continue
        
        print(f"✅ Found {len(calendar_events)} calendar events")
        return calendar_events if calendar_events else get_mock_calendar_events()
        
    except Exception as e:
        print(f"❌ Error fetching CalDAV events: {e}")
        return get_mock_calendar_events()

def get_mock_calendar_events():
    """Mock calendar data - fallback when no real calendar available"""
    today = datetime.now()
    
    mock_events = [
        {
            "title": "Team Standup",
            "start_time": today.replace(hour=9, minute=30),
            "duration": "30 min"
        },
        {
            "title": "Strategy Review", 
            "start_time": today.replace(hour=14, minute=0),
            "duration": "1 hour"
        },
        {
            "title": "Client Call - Project Alpha",
            "start_time": today.replace(hour=16, minute=30),
            "duration": "45 min"
        }
    ]
    
    return mock_events

# Initialize CalDAV calendar
print("🔧 Setting up CalDAV calendar connection...")
caldav_calendar = setup_caldav_calendar()

def execute_function(function_name, arguments):
    """Execute the called function and return results"""
    
    if function_name == "get_today_schedule":
        events = get_caldav_events(caldav_calendar, days_ahead=1)
        
        if not events:
            return "No events scheduled for today"
        
        event_list = []
        for event in events:
            # Handle both timezone-aware and naive datetime
            if hasattr(event['start_time'], 'strftime'):
                time_str = event['start_time'].strftime('%I:%M %p')
            else:
                time_str = str(event['start_time'])
            event_list.append(f"• {time_str}: {event['title']} ({event['duration']})")
        
        return "📅 Today's Schedule:\n" + "\n".join(event_list)
    
    elif function_name == "get_tomorrow_schedule":
        tomorrow = datetime.now() + timedelta(days=1)
        tomorrow_start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_end = tomorrow_start + timedelta(days=1)
        
        # Get tomorrow's events specifically
        events = get_caldav_events_for_date(caldav_calendar, tomorrow_start, tomorrow_end)
        
        if not events:
            return "No events scheduled for tomorrow"
        
        event_list = []
        for event in events:
            if hasattr(event['start_time'], 'strftime'):
                time_str = event['start_time'].strftime('%I:%M %p')
            else:
                time_str = str(event['start_time'])
            event_list.append(f"• {time_str}: {event['title']} ({event['duration']})")
        
        return "📅 Tomorrow's Schedule:\n" + "\n".join(event_list)
    
    elif function_name == "get_upcoming_events":
        days = arguments.get('days', 7)
        events = get_caldav_events(caldav_calendar, days_ahead=days)
        
        if not events:
            return f"No events found in the next {days} days"
        
        event_list = []
        today = datetime.now().date()
        
        for event in events:
            event_date = event['start_time'].date() if hasattr(event['start_time'], 'date') else today
            
            if event_date == today:
                time_str = f"Today at {event['start_time'].strftime('%I:%M %p')}"
            elif event_date == today + timedelta(days=1):
                time_str = f"Tomorrow at {event['start_time'].strftime('%I:%M %p')}"
            else:
                time_str = event['start_time'].strftime('%m/%d at %I:%M %p')
            
            event_list.append(f"• {event['title']} - {time_str}")
        
        return f"📅 Upcoming Events (Next {days} days):\n" + "\n".join(event_list)
    
    elif function_name == "find_free_time":
        duration = arguments.get('duration', 60)
        date = arguments.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        events = get_caldav_events(caldav_calendar, days_ahead=1)
        
        # Simple free time logic
        free_slots = []
        
        # Business hours (9 AM to 6 PM)
        start_hour = 9
        end_hour = 18
        
        # Sort events by time
        events.sort(key=lambda x: x['start_time'])
        
        current_time = datetime.now().replace(hour=start_hour, minute=0)
        end_of_day = datetime.now().replace(hour=end_hour, minute=0)
        
        for event in events:
            event_start = event['start_time']
            
            # Check if there's a gap before this event
            if current_time < event_start:
                gap_minutes = (event_start - current_time).total_seconds() / 60
                if gap_minutes >= duration:
                    free_slots.append(f"{current_time.strftime('%I:%M %p')} - {event_start.strftime('%I:%M %p')}")
            
            # Move current time to after this event (assume 1 hour if duration unknown)
            event_end = event_start + timedelta(hours=1)
            current_time = max(current_time, event_end)
        
        # Check time after last event
        if current_time < end_of_day:
            gap_minutes = (end_of_day - current_time).total_seconds() / 60
            if gap_minutes >= duration:
                free_slots.append(f"{current_time.strftime('%I:%M %p')} - {end_of_day.strftime('%I:%M %p')}")
        
        if not free_slots:
            free_slots = ["No significant free blocks found"]
        
        return f"⏰ Free time slots on {date} ({duration}+ min blocks):\n" + "\n".join([f"• {slot}" for slot in free_slots])
    
    else:
        return f"Unknown function: {function_name}"

def get_caldav_events_for_date(calendar, start_date, end_date):
    """Get events for a specific date range"""
    if not calendar:
        return []
    
    try:
        print(f"📅 Fetching events from {start_date.date()} to {end_date.date()}")
        
        # Search for events in date range
        events = calendar.search(
            start=start_date,
            end=end_date,
            event=True,
            expand=True
        )
        
        calendar_events = []
        
        for event in events:
            try:
                # Parse the iCalendar data
                cal_data = Calendar.from_ical(event.data)
                
                for component in cal_data.walk():
                    if component.name == "VEVENT":
                        summary = str(component.get('summary', 'Untitled'))
                        dtstart = component.get('dtstart')
                        dtend = component.get('dtend')
                        
                        if dtstart and dtstart.dt:
                            start_time = dtstart.dt
                            
                            # Handle timezone-aware datetime
                            if hasattr(start_time, 'replace'):
                                # Calculate duration
                                if dtend and dtend.dt:
                                    duration = dtend.dt - start_time
                                    duration_str = f"{int(duration.total_seconds() / 60)} min"
                                else:
                                    duration_str = "Unknown"
                                
                                calendar_events.append({
                                    "title": summary,
                                    "start_time": start_time,
                                    "duration": duration_str
                                })
                                
            except Exception as e:
                print(f"⚠️ Error parsing event: {e}")
                continue
        
        print(f"✅ Found {len(calendar_events)} calendar events for date range")
        return calendar_events
        
    except Exception as e:
        print(f"❌ Error fetching CalDAV events for date range: {e}")
        return []

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