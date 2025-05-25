import os
import asyncio
import json
from openai import OpenAI
from datetime import datetime, timedelta

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Store user threads in memory
user_threads = {}

# Mock calendar data (replace with real calendar integration later)
def get_mock_calendar_events():
    """Mock calendar data - you can replace this with real calendar API later"""
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

def execute_function(function_name, arguments):
    """Execute the called function and return results"""
    
    if function_name == "get_today_schedule":
        events = get_mock_calendar_events()
        
        if not events:
            return "No events scheduled for today"
        
        event_list = []
        for event in events:
            time_str = event['start_time'].strftime('%I:%M %p')
            event_list.append(f"• {time_str}: {event['title']} ({event['duration']})")
        
        return "Today's Schedule:\n" + "\n".join(event_list)
    
    elif function_name == "get_upcoming_events":
        days = arguments.get('days', 7)
        events = get_mock_calendar_events()  # In real version, fetch for date range
        
        if not events:
            return f"No events found in the next {days} days"
        
        event_list = []
        for event in events:
            if event['start_time'].date() == datetime.now().date():
                time_str = f"Today at {event['start_time'].strftime('%I:%M %p')}"
            else:
                time_str = event['start_time'].strftime('%m/%d at %I:%M %p')
            
            event_list.append(f"• {event['title']} - {time_str}")
        
        return f"Upcoming Events (Next {days} days):\n" + "\n".join(event_list)
    
    elif function_name == "find_free_time":
        duration = arguments.get('duration', 60)
        date = arguments.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Mock free time logic
        free_slots = [
            "10:00 AM - 11:30 AM",
            "2:00 PM - 3:00 PM", 
            "4:30 PM - 6:00 PM"
        ]
        
        return f"Free time slots on {date} (for {duration} min blocks):\n" + "\n".join([f"• {slot}" for slot in free_slots])
    
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
                raise Exception("❌ Run failed.")
            elif run_status.status == "requires_action":
                raise Exception("⚠️ Run requires action (not handled).")
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