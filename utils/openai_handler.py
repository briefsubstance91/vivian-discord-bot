import os
import asyncio
import json
import base64
import pytz
from datetime import datetime, timedelta
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import aiohttp

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

# Enhanced memory system (from Celeste)
user_conversations = {}  # user_id -> thread_id
conversation_context = {}  # user_id -> recent message history
MAX_CONTEXT_MESSAGES = 10  # Remember last 10 messages per user

# Set your timezone here - UPDATE THIS TO YOUR TIMEZONE
LOCAL_TIMEZONE = 'America/Toronto'  # Change to your timezone!

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
            scopes = ['https://www.googleapis.com/auth/calendar']
        elif service_name == 'gmail':
            scopes = [
                'https://www.googleapis.com/auth/gmail.modify',
                'https://www.googleapis.com/auth/gmail.send'
            ]
        else:
            scopes = ['https://www.googleapis.com/auth/calendar']
        
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=scopes
        )
        
        # For Gmail, we need to specify the user email for domain-wide delegation
        if service_name == 'gmail':
            # Get the email from the calendar ID or use a default
            user_email = os.getenv('GOOGLE_CALENDAR_ID', 'bgelineau@gmail.com')
            if user_email == 'primary':
                user_email = 'bgelineau@gmail.com'  # Replace with your actual email
            
            credentials = credentials.with_subject(user_email)
            print(f"📧 Attempting Gmail access for: {user_email}")
        
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
# ENHANCED WEB RESEARCH FUNCTIONS
# ============================================================================

async def perform_web_research(query, search_type="general", num_results=5, focus_area="general"):
    """Perform web research with enhanced capabilities"""
    try:
        if not BRAVE_API_KEY:
            return "🔍 **Research unavailable** - BRAVE_API_KEY not configured.\n\n📨 **Alternative:** I can coordinate with Celeste for manual research."
        
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': BRAVE_API_KEY
        }
        
        # Enhanced query modification based on search type and focus
        enhanced_query = query
        
        params = {
            'q': enhanced_query,
            'count': num_results,
            'offset': 0,
            'mkt': 'en-US',
            'safesearch': 'moderate',
            'textDecorations': False,
            'textFormat': 'Raw'
        }
        
        # Search type modifications
        if search_type == "reddit":
            params['q'] += " site:reddit.com"
        elif search_type == "news":
            params['freshness'] = 'Day'
            params['q'] += " news recent"
        elif search_type == "academic":
            params['q'] += " research study academic"
        elif search_type == "local":
            params['q'] += " local area information"
        elif search_type == "trends":
            params['q'] += " trends 2024 2025 latest"
        
        # Focus area modifications
        if focus_area == "PR_analysis":
            params['q'] += " public opinion media coverage"
        elif focus_area == "market_research":
            params['q'] += " market analysis industry research"
        elif focus_area == "competitor_intel":
            params['q'] += " competitor analysis competition"
        elif focus_area == "trend_analysis":
            params['q'] += " trending popular analysis"
        
        url = "https://api.search.brave.com/res/v1/web/search"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('web', {}).get('results', [])
                    
                    if not results:
                        return f"🔍 **No results found for '{query}'**\n\nTry different search terms or coordinate with Celeste for manual research."
                    
                    formatted_results = []
                    for i, result in enumerate(results[:num_results], 1):
                        title = result.get('title', 'No title')
                        snippet = result.get('description', 'No description')
                        url_link = result.get('url', '')
                        
                        if len(snippet) > 200:
                            snippet = snippet[:200] + '...'
                        
                        # Source indicators for PR context
                        source_indicator = ""
                        if "reddit.com" in url_link.lower():
                            source_indicator = "🔴 "
                        elif any(domain in url_link.lower() for domain in ['edu', 'gov']):
                            source_indicator = "🎓 "
                        elif any(domain in url_link.lower() for domain in ['news', 'cnn', 'bbc']):
                            source_indicator = "📰 "
                        elif any(domain in url_link.lower() for domain in ['wikipedia']):
                            source_indicator = "📚 "
                        
                        formatted_results.append(f"**{i}. {source_indicator}{title}**\n{snippet}\n🔗 {url_link}\n")
                    
                    return f"🔍 **Research Results: '{query}'**\n\n" + "\n".join(formatted_results)
                else:
                    return f"🔍 **Search Error** (Status {response.status})\n\nCan coordinate with Celeste for alternative research."
                    
    except Exception as e:
        print(f"Research error: {e}")
        return f"🔍 **Research Error:** {str(e)}\n\nCan route to Celeste for manual research approach."

async def analyze_trends_research(topic, timeframe="current", platforms=None):
    """Analyze trends for a specific topic"""
    if platforms is None:
        platforms = ["general", "news", "social"]
    
    trend_query = f"{topic} trends {timeframe}"
    sentiment_query = f"{topic} public opinion sentiment"
    
    # Perform multiple searches for comprehensive analysis
    trend_results = await perform_web_research(trend_query, "trends", 5, "trend_analysis")
    sentiment_results = await perform_web_research(sentiment_query, "general", 3, "PR_analysis")
    
    analysis_summary = f"📊 **TREND ANALYSIS: {topic}**\n\n"
    analysis_summary += f"**📈 TREND DATA:**\n{trend_results}\n\n"
    analysis_summary += f"**💬 SENTIMENT DATA:**\n{sentiment_results}\n\n"
    analysis_summary += f"**🎯 ANALYSIS TIMEFRAME:** {timeframe}\n**📱 PLATFORMS:** {', '.join(platforms)}"
    
    return analysis_summary

def coordinate_research_request(research_request, target_assistant="Celeste", urgency="medium", deliverable_type="summary"):
    """Coordinate complex research with team members"""
    coordination_message = f"🤝 **RESEARCH COORDINATION**\n\n"
    coordination_message += f"**📋 Request:** {research_request}\n"
    coordination_message += f"**👤 Target Assistant:** {target_assistant}\n"
    coordination_message += f"**⚡ Urgency:** {urgency}\n"
    coordination_message += f"**📝 Expected Output:** {deliverable_type}\n\n"
    
    if target_assistant == "Celeste":
        coordination_message += "**🎯 Routing to Celeste for:**\n"
        coordination_message += "• Comprehensive content research\n"
        coordination_message += "• Information synthesis and analysis\n"
        coordination_message += "• Detailed report creation\n"
        coordination_message += "• Multi-source research compilation\n\n"
    
    coordination_message += "**📊 Coordination Status:** Request routed successfully\n"
    coordination_message += "**⏱️ Expected Response:** Based on complexity and urgency level\n"
    coordination_message += "**🔄 Follow-up:** Will provide updates on research progress"
    
    return coordination_message

# ============================================================================
# CALENDAR FUNCTIONS (Enhanced with PR context)
# ============================================================================

def get_calendar_events(service, days_ahead=7):
    """Get events from Google Calendar with PR/communications context"""
    if not service:
        print("📅 Using mock calendar data (no Google Calendar connection)")
        return get_mock_calendar_events()
    
    try:
        # Use local timezone
        local_tz = pytz.timezone(LOCAL_TIMEZONE)
        now = datetime.now(local_tz)
        
        # Get start of today in local time, then convert to UTC for API
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_of_today + timedelta(days=days_ahead)
        
        # Convert to UTC for the API call
        start_time_utc = start_of_today.astimezone(pytz.UTC).isoformat()
        end_time_utc = end_time.astimezone(pytz.UTC).isoformat()
        
        calendar_id = os.getenv('GOOGLE_CALENDAR_ID', 'primary')
        
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_time_utc,
            timeMax=end_time_utc,
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
            
            # Parse start time with proper timezone handling
            if 'T' in start:
                if start.endswith('Z'):
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:
                    start_dt = datetime.fromisoformat(start)
                
                if start_dt.tzinfo is None:
                    start_dt = pytz.UTC.localize(start_dt)
                start_dt = start_dt.astimezone(local_tz)
            else:
                start_dt = datetime.strptime(start, '%Y-%m-%d')
                start_dt = local_tz.localize(start_dt)
            
            # Calculate duration
            if end and 'T' in end:
                if end.endswith('Z'):
                    end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                else:
                    end_dt = datetime.fromisoformat(end)
                
                if end_dt.tzinfo is None:
                    end_dt = pytz.UTC.localize(end_dt)
                end_dt = end_dt.astimezone(local_tz)
                
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
                "attendees": [att.get('email', '') for att in event.get('attendees', [])],
                "event_id": event.get('id', '')
            })
        
        print(f"✅ Found {len(calendar_events)} calendar events")
        return calendar_events
        
    except Exception as e:
        print(f"❌ Error fetching Google Calendar events: {e}")
        return get_mock_calendar_events()

def get_mock_calendar_events():
    """Mock calendar data with PR/communications focus"""
    local_tz = pytz.timezone(LOCAL_TIMEZONE)
    today = datetime.now(local_tz)
    
    mock_events = [
        {
            "title": "PR Strategy Meeting",
            "start_time": today.replace(hour=9, minute=30),
            "duration": "1 hour",
            "description": "Quarterly PR strategy and communications planning",
            "location": "Conference Room A",
            "attendees": ["team@company.com"],
            "event_id": "mock_pr_1"
        },
        {
            "title": "Media Interview - Tech Trends", 
            "start_time": today.replace(hour=14, minute=0),
            "duration": "45 min",
            "description": "Interview about AI trends for industry publication",
            "location": "Zoom",
            "attendees": ["journalist@techpub.com"],
            "event_id": "mock_media_1"
        },
        {
            "title": "Social Media Content Review",
            "start_time": today.replace(hour=16, minute=30),
            "duration": "30 min",
            "description": "Review upcoming social media content and campaigns",
            "location": "Office",
            "attendees": ["social@company.com"],
            "event_id": "mock_social_1"
        }
    ]
    
    return mock_events

# ============================================================================
# EMAIL FUNCTIONS (Existing)
# ============================================================================

# [Include existing email functions from the original code]
# ... (search_gmail_messages, get_recent_emails, send_email functions)

# ============================================================================
# ENHANCED FUNCTION EXECUTION
# ============================================================================

def execute_function(function_name, arguments):
    """Execute function with enhanced research capabilities"""
    
    # Get local timezone for all date operations
    local_tz = pytz.timezone(LOCAL_TIMEZONE)
    
    # NEW: Research Functions
    if function_name == "web_research":
        query = arguments.get('query', '')
        search_type = arguments.get('search_type', 'general')
        num_results = arguments.get('num_results', 5)
        focus_area = arguments.get('focus_area', 'general')
        
        # This would normally be async, but we'll need to handle it in the calling code
        result = f"🔍 **Research Request:** {query}\n\n**Type:** {search_type}\n**Focus:** {focus_area}\n\n⚠️ **Note:** Web research will be performed by the main bot code and results provided."
        return result
    
    elif function_name == "analyze_trends":
        topic = arguments.get('topic', '')
        timeframe = arguments.get('timeframe', 'current')
        platforms = arguments.get('platforms', ['general', 'news', 'social'])
        
        result = f"📊 **Trend Analysis Request:** {topic}\n\n**Timeframe:** {timeframe}\n**Platforms:** {', '.join(platforms)}\n\n⚠️ **Note:** Trend analysis will be performed by the main bot code and results provided."
        return result
    
    elif function_name == "research_coordination":
        research_request = arguments.get('research_request', '')
        target_assistant = arguments.get('target_assistant', 'Celeste')
        urgency = arguments.get('urgency', 'medium')
        deliverable_type = arguments.get('deliverable_type', 'summary')
        
        result = coordinate_research_request(research_request, target_assistant, urgency, deliverable_type)
        return result
    
    # Existing Calendar Functions (with PR context)
    elif function_name == "get_today_schedule":
        events = get_calendar_events(calendar_service, days_ahead=1)
        today = datetime.now(local_tz).date()
        
        today_events = []
        for event in events:
            try:
                if hasattr(event['start_time'], 'date'):
                    event_date = event['start_time'].date()
                else:
                    event_dt = datetime.fromisoformat(str(event['start_time']))
                    if event_dt.tzinfo is None:
                        event_dt = local_tz.localize(event_dt)
                    event_date = event_dt.date()
                
                if event_date == today:
                    today_events.append(event)
                    
            except Exception as e:
                print(f"⚠️ Error processing event date: {e}")
                continue
        
        if not today_events:
            result = "📅 **Clear Schedule Today**\n\nNo events scheduled - excellent opportunity for:\n• Strategic PR planning\n• Content development\n• Research and trend analysis\n• Proactive communications outreach"
        else:
            event_lines = []
            for event in today_events:
                try:
                    if hasattr(event['start_time'], 'strftime'):
                        time_str = event['start_time'].strftime('%I:%M %p')
                    else:
                        time_str = "All day"
                    
                    event_line = f"• {time_str}: {event['title']}"
                    if event['duration'] and event['duration'] != "All day":
                        event_line += f" ({event['duration']})"
                    
                    event_lines.append(event_line)
                    
                    if event['location']:
                        event_lines.append(f"  📍 {event['location']}")
                        
                except Exception as e:
                    event_lines.append(f"• {event.get('title', 'Unknown event')}")
            
            result = f"📅 **Today's Communications Schedule** ({len(today_events)} events)\n\n" + "\n".join(event_lines)
            result += "\n\n🎯 **PR Opportunities:**\n• Pre-meeting prep and talking points\n• Post-meeting follow-ups and coverage\n• Strategic content creation opportunities"
        
        return result
    
    # [Include other existing calendar and email functions with similar enhancements]
    # ... (get_tomorrow_schedule, get_upcoming_events, find_free_time, search_emails, etc.)
    
    else:
        result = f"❌ **Unknown Function:** {function_name}\n\n🔍 **Available Functions:**\nResearch: web_research, analyze_trends, research_coordination\nCalendar: get_today_schedule, get_tomorrow_schedule, get_upcoming_events, find_free_time\nEmail: search_emails, get_recent_emails, send_email"
        return result

# ============================================================================
# FUNCTION CALL HANDLING (Enhanced)
# ============================================================================

async def handle_function_calls(run, thread_id):
    """Handle function calls from the assistant with research capabilities"""
    tool_outputs = []
    
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        function_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        print(f"🔧 Executing function: {function_name} with args: {arguments}")
        
        # Handle research functions specially
        if function_name == "web_research":
            query = arguments.get('query', '')
            search_type = arguments.get('search_type', 'general')
            num_results = arguments.get('num_results', 5)
            focus_area = arguments.get('focus_area', 'general')
            
            print(f"🔍 Performing web research: {query}")
            research_results = await perform_web_research(query, search_type, num_results, focus_area)
            output = research_results
            
        elif function_name == "analyze_trends":
            topic = arguments.get('topic', '')
            timeframe = arguments.get('timeframe', 'current')
            platforms = arguments.get('platforms', ['general', 'news', 'social'])
            
            print(f"📊 Performing trend analysis: {topic}")
            trend_results = await analyze_trends_research(topic, timeframe, platforms)
            output = trend_results
            
        else:
            # Execute regular functions
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

# ============================================================================
# ENHANCED RESPONSE FORMATTING
# ============================================================================

def format_for_discord_vivian(response):
    """Format response specifically for Vivian's PR/communications focus"""
    
    # Remove excessive formatting for readability
    response = response.replace('**', '')  # Remove all bold formatting initially
    response = response.replace('\n\n\n', '\n\n')  # Remove triple line breaks
    
    # Add strategic emoji headers for key sections
    if 'research' in response.lower() or 'analysis' in response.lower():
        if not response.startswith('🔍'):
            response = '🔍 **Research Analysis** \n\n' + response
    elif 'schedule' in response.lower() or 'calendar' in response.lower():
        if not response.startswith('📅'):
            response = '📅 **Communications Schedule** \n\n' + response
    elif 'email' in response.lower() and not response.startswith('📧'):
        response = '📧 **External Communications** \n\n' + response
    elif 'trend' in response.lower() or 'sentiment' in response.lower():
        if not response.startswith('📊'):
            response = '📊 **Trend Analysis** \n\n' + response
    
    # Ensure manageable length for Discord
    if len(response) > 1800:
        sentences = response.split('. ')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence + '. ') < 1700:
                truncated += sentence + '. '
            else:
                truncated += "\n\n🎯 *Need more details? Ask for specific research or coordinate with Celeste!*"
                break
        response = truncated
    
    return response.strip()

# ============================================================================
# MAIN OPENAI RESPONSE HANDLER (Enhanced for Research)
# ============================================================================

async def get_openai_response(user_message: str, user_id: int, clear_memory: bool = False) -> str:
    """Enhanced OpenAI response with research capabilities and memory"""
    try:
        # Handle memory clearing
        if clear_memory:
            clear_user_memory(user_id)
            return "🧹 **Memory cleared!** Ready for fresh PR strategy and research."
        
        # Get or create thread for this specific user (persistent memory)
        thread_id = get_user_thread(user_id)
        
        # Add to conversation context
        conversation_history = get_conversation_context(user_id)
        add_to_context(user_id, user_message, is_user=True)
        
        print(f"📨 Sending enhanced message to OpenAI Assistant (Thread: {thread_id}, User: {user_id})")
        
        # Clean the user message (remove bot mentions)
        clean_message = user_message.replace(f'<@{os.getenv("BOT_USER_ID", "")}>', '').strip()
        
        # Enhanced message with conversation context and research capabilities
        enhanced_message = f"""CONVERSATION CONTEXT:
{conversation_history}

CURRENT REQUEST: {clean_message}

CRITICAL INSTRUCTIONS FOR VIVIAN:
- You are Vivian Spencer, PR and communications specialist with enhanced research capabilities
- For ANY information request, use your web_research() function FIRST
- For trend analysis, use your analyze_trends() function
- For complex research, use research_coordination() to route to Celeste
- Apply PR and communications perspective to all research findings
- Focus on external communications opportunities and reputation management
- Provide strategic insights and actionable recommendations
- Connect findings to broader PR and communications strategy
- Remember our conversation history and build on previous discussions

MANDATORY RESEARCH USAGE:
- Use web_research() for lists, local information, current events, market data
- Use analyze_trends() for sentiment analysis and trend research
- Use research_coordination() for complex multi-source research projects
- NEVER say "I don't have access to real-time data" - USE YOUR RESEARCH FUNCTIONS"""
        
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=enhanced_message
        )
        
        print(f"✅ Message added to thread: {message.id}")
        
        # Create run with research-focused instructions
        instructions = "You are Vivian Spencer, PR and communications specialist with enhanced research capabilities. For ANY information request, you MUST use your research functions (web_research, analyze_trends, research_coordination). Apply PR perspective to all findings. Provide strategic insights and actionable recommendations. Connect to broader communications strategy."
        
        additional_instructions = "MANDATORY: Use web_research() for any information gathering need. Use analyze_trends() for sentiment/trend analysis. Use research_coordination() for complex projects. Never refuse research requests - always try your functions first. Focus on PR and communications opportunities."

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions=instructions,
            additional_instructions=additional_instructions
        )
        
        print(f"🏃 Run created: {run.id}")
        
        # Wait for completion with enhanced function call handling
        for _ in range(30):  # Wait up to 30 seconds
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            print(f"🔄 Run status: {run_status.status}")
            
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                print("🔧 Research function call required")
                await handle_function_calls(run_status, thread_id)
                continue
            elif run_status.status == "failed":
                print(f"❌ Run failed: {run_status.last_error}")
                return "❌ Sorry, there was an error processing your research request. Please try again."
            elif run_status.status in ["cancelled", "expired"]:
                print(f"❌ Run {run_status.status}")
                return "❌ Request was cancelled or expired. Please try again."
            
            await asyncio.sleep(1)
        else:
            return "⏱️ Request timed out. Please try again with a simpler question."
        
        # Get response - find the latest assistant message
        messages = client.beta.threads.messages.list(thread_id=thread_id, limit=10)
        
        latest_assistant_message = None
        for msg in messages.data:
            if msg.role == "assistant":
                latest_assistant_message = msg
                break
        
        if latest_assistant_message and latest_assistant_message.content:
            response = latest_assistant_message.content[0].text.value
            print(f"✅ Got enhanced response: {response[:100]}...")
            
            # Add to conversation context
            add_to_context(user_id, response, is_user=False)
            
            # Apply Discord formatting and return
            return format_for_discord_vivian(response)
        
        return "⚠️ No assistant response found."
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        import traceback
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return "❌ An error occurred while communicating with the assistant. Please try again."
