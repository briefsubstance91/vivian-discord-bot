#!/usr/bin/env python3
"""
VIVIAN WITH GMAIL & CALENDAR INTEGRATION
Adds work Gmail and calendar access with tighter Discord formatting
Based on proven Rose calendar pattern
"""

import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
import pytz
import base64
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables
load_dotenv()

# Vivian's specific configuration
ASSISTANT_NAME = "Vivian Spencer"
ASSISTANT_ROLE = "PR & Communications"
ALLOWED_CHANNELS = ['social-overview', 'news-feed', 'external-communications', 'general']

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("VIVIAN_DISCORD_TOKEN")
ASSISTANT_ID = os.getenv("VIVIAN_ASSISTANT_ID") or os.getenv("ASSISTANT_ID")
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

# Discord setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# OpenAI setup
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple memory system
user_conversations = {}

# Set your timezone
LOCAL_TIMEZONE = 'America/Toronto'

print(f"📱 Starting {ASSISTANT_NAME} - {ASSISTANT_ROLE} with Gmail & Calendar...")

# ============================================================================
# GOOGLE SERVICES INTEGRATION (Gmail + Calendar)
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
        
        # For Gmail, we need domain-wide delegation with the work email
        if service_name == 'gmail':
            work_email = os.getenv('WORK_GOOGLE_CALENDAR_ID', os.getenv('GOOGLE_CALENDAR_ID', 'primary'))
            if '@' in work_email:  # If it's an actual email address
                credentials = credentials.with_subject(work_email)
                print(f"📧 Gmail access configured for: {work_email}")
            else:
                print(f"⚠️ Using primary Gmail access")
        
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
# GMAIL FUNCTIONS
# ============================================================================

def search_gmail_messages(query, max_results=10):
    """Search Gmail messages"""
    if not gmail_service:
        return get_mock_email_search(query)
    
    try:
        # Search for messages
        search_results = gmail_service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = search_results.get('messages', [])
        
        if not messages:
            return []
        
        # Get details for each message
        email_data = []
        for message in messages[:max_results]:
            try:
                msg_detail = gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg_detail['payload'].get('headers', [])
                
                # Extract header information
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                # Parse date
                try:
                    # Gmail date format parsing
                    email_date = datetime.strptime(date_str.split(' (')[0], '%a, %d %b %Y %H:%M:%S %z')
                except:
                    email_date = datetime.now()
                
                is_unread = 'UNREAD' in msg_detail.get('labelIds', [])
                
                email_data.append({
                    'id': message['id'],
                    'subject': subject[:100],  # Truncate long subjects
                    'sender': from_email.split('<')[0].strip().replace('"', ''),  # Clean sender name
                    'date': email_date,
                    'is_unread': is_unread,
                    'snippet': msg_detail.get('snippet', '')[:150]  # Gmail's snippet
                })
                
            except Exception as e:
                print(f"❌ Error getting message details: {e}")
                continue
        
        return email_data
        
    except Exception as e:
        print(f"❌ Error searching Gmail: {e}")
        return get_mock_email_search(query)

def get_recent_emails(max_results=10):
    """Get recent emails"""
    if not gmail_service:
        return get_mock_recent_emails()
    
    try:
        # Get recent messages
        results = gmail_service.users().messages().list(
            userId='me',
            maxResults=max_results,
            q='in:inbox'  # Only inbox messages
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return []
        
        # Process messages (reuse search function logic)
        email_data = []
        for message in messages[:max_results]:
            try:
                msg_detail = gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = msg_detail['payload'].get('headers', [])
                
                from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown sender')
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No subject')
                date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
                
                try:
                    email_date = datetime.strptime(date_str.split(' (')[0], '%a, %d %b %Y %H:%M:%S %z')
                except:
                    email_date = datetime.now()
                
                is_unread = 'UNREAD' in msg_detail.get('labelIds', [])
                
                email_data.append({
                    'id': message['id'],
                    'subject': subject[:100],
                    'sender': from_email.split('<')[0].strip().replace('"', ''),
                    'date': email_date,
                    'is_unread': is_unread,
                    'snippet': msg_detail.get('snippet', '')[:150]
                })
                
            except Exception as e:
                continue
        
        return email_data
        
    except Exception as e:
        print(f"❌ Error getting recent emails: {e}")
        return get_mock_recent_emails()

def get_mock_email_search(query):
    """Mock email search when Gmail unavailable"""
    return [
        {
            'id': 'mock_search',
            'subject': f'Mock search result for: {query}',
            'sender': 'Gmail Setup Needed',
            'date': datetime.now(),
            'is_unread': True,
            'snippet': 'Configure Gmail service account for real email access'
        }
    ]

def get_mock_recent_emails():
    """Mock recent emails when Gmail unavailable"""
    return [
        {
            'id': 'mock_recent',
            'subject': 'Gmail Configuration Required',
            'sender': 'System',
            'date': datetime.now(),
            'is_unread': True,
            'snippet': 'Set up Gmail service account access for real email integration'
        }
    ]

def format_emails_for_discord(emails, title="Email Results"):
    """Format emails for Discord with PR focus"""
    if not emails:
        return f"📧 **{title}**\n\nNo emails found. Perfect time for strategic communications planning!"
    
    formatted_lines = [f"📧 **{title}**"]
    
    for i, email in enumerate(emails[:5], 1):  # Limit to 5 emails
        unread_indicator = "🔵 " if email['is_unread'] else ""
        
        # Format date
        try:
            if email['date'].date() == datetime.now().date():
                date_str = email['date'].strftime('%I:%M %p')
            else:
                date_str = email['date'].strftime('%m/%d')
        except:
            date_str = "Recent"
        
        formatted_lines.append(f"{unread_indicator}**{i}. {email['subject']}**")
        formatted_lines.append(f"From: {email['sender']} • {date_str}")
        
        if email['snippet']:
            formatted_lines.append(f"_{email['snippet']}_")
        
        formatted_lines.append("")  # Empty line between emails
    
    if len(emails) > 5:
        formatted_lines.append(f"📋 *...and {len(emails) - 5} more emails*")
    
    result = "\n".join(formatted_lines)
    
    # Keep within Discord limits
    if len(result) > 1500:
        result = result[:1500] + "\n\n📧 *Email list truncated for Discord*"
    
    return result

# ============================================================================
# CALENDAR FUNCTIONS (Reusing Rose's proven pattern)
# ============================================================================

def get_calendar_events(days_ahead=7):
    """Get events from Google Calendar"""
    if not calendar_service:
        return get_mock_calendar_events()
    
    try:
        local_tz = pytz.timezone(LOCAL_TIMEZONE)
        now = datetime.now(local_tz)
        
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_of_today + timedelta(days=days_ahead)
        
        start_time_utc = start_of_today.astimezone(pytz.UTC).isoformat()
        end_time_utc = end_time.astimezone(pytz.UTC).isoformat()
        
        # Use work calendar ID if available
        calendar_id = os.getenv('WORK_GOOGLE_CALENDAR_ID', os.getenv('GOOGLE_CALENDAR_ID', 'primary'))
        
        events_result = calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=start_time_utc,
            timeMax=end_time_utc,
            maxResults=50,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return []
        
        calendar_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
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
        
        return calendar_events
        
    except Exception as e:
        print(f"❌ Error fetching Google Calendar events: {e}")
        return get_mock_calendar_events()

def get_mock_calendar_events():
    """Mock calendar data when Google Calendar is not available"""
    local_tz = pytz.timezone(LOCAL_TIMEZONE)
    today = datetime.now(local_tz)
    
    return [
        {
            "title": "Work calendar setup needed",
            "start_time": today.replace(hour=9, minute=0),
            "duration": "Setup required",
            "description": "Configure work Google Calendar access",
            "location": "",
            "attendees": [],
            "event_id": "setup_needed"
        }
    ]

def format_calendar_events(events, title="Calendar Events"):
    """Format calendar events for Discord with PR perspective"""
    if not events:
        return f"📅 **{title}**\n\nClear schedule - perfect for strategic PR planning!"
    
    formatted_lines = [f"📅 **{title}**"]
    
    local_tz = pytz.timezone(LOCAL_TIMEZONE)
    today = datetime.now(local_tz).date()
    
    for event in events[:5]:  # Limit to 5 events
        try:
            if hasattr(event['start_time'], 'strftime'):
                event_date = event['start_time'].date()
                time_str = event['start_time'].strftime('%I:%M %p')
                
                if event_date == today:
                    day_str = "Today"
                elif event_date == today + timedelta(days=1):
                    day_str = "Tomorrow"
                else:
                    day_str = event['start_time'].strftime('%a %m/%d')
                
                event_line = f"• **{day_str} {time_str}**: {event['title']}"
                if event['duration'] != "All day":
                    event_line += f" ({event['duration']})"
                
                formatted_lines.append(event_line)
                
                if event['location']:
                    formatted_lines.append(f"  📍 {event['location']}")
                    
        except Exception as e:
            formatted_lines.append(f"• {event.get('title', 'Event')}")
    
    if len(events) > 5:
        formatted_lines.append(f"📋 *...and {len(events) - 5} more events*")
    
    result = "\n".join(formatted_lines)
    
    # Keep within Discord limits
    if len(result) > 1500:
        result = result[:1500] + "\n\n📅 *Calendar summary truncated*"
    
    return result

# ============================================================================
# WEB SEARCH (Existing)
# ============================================================================

async def web_search_fixed(query, search_type="general", num_results=5):
    """FIXED web search - simple queries that work with Brave API"""
    try:
        if not BRAVE_API_KEY:
            return "🔍 Web search unavailable - no API key configured"
        
        # CLEAN, SIMPLE QUERY - no complex additions that cause 422 errors
        clean_query = query.strip()
        
        # Only add simple modifiers
        if search_type == "news":
            clean_query += " news"
        elif search_type == "local" and "toronto" not in clean_query.lower():
            clean_query += " Toronto"
        
        headers = {
            'Accept': 'application/json',
            'X-Subscription-Token': BRAVE_API_KEY
        }
        
        # MINIMAL parameters to avoid 422 errors
        params = {
            'q': clean_query,
            'count': min(num_results, 5),  # Keep small
            'safesearch': 'moderate'
        }
        
        url = "https://api.search.brave.com/res/v1/web/search"
        
        print(f"🔍 CLEAN SEARCH: '{clean_query}'")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                print(f"🔍 API Response: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    results = data.get('web', {}).get('results', [])
                    
                    if not results:
                        return f"🔍 No results found for '{query}'"
                    
                    # Simple, clean formatting for Discord
                    formatted = [f"🔍 **Search Results: '{query}'**"]
                    
                    for i, result in enumerate(results[:3], 1):  # Max 3 results
                        title = result.get('title', 'No title')[:80]  # Shorter titles
                        snippet = result.get('description', 'No description')[:120]  # Shorter snippets
                        url_link = result.get('url', '')
                        
                        formatted.append(f"**{i}. {title}**")
                        formatted.append(f"{snippet}")
                        formatted.append(f"🔗 {url_link}")
                        if i < len(results[:3]):  # Add space between results except last
                            formatted.append("")
                    
                    result_text = "\n".join(formatted)
                    
                    # Ensure Discord length limit
                    if len(result_text) > 1800:
                        result_text = result_text[:1800] + "\n\n💬 *Results truncated for Discord*"
                    
                    return result_text
                    
                elif response.status == 422:
                    return f"🔍 Search query too complex. Try simpler terms for '{query}'"
                else:
                    return f"🔍 Search error (status {response.status})"
                    
    except Exception as e:
        print(f"❌ Search error: {e}")
        return f"🔍 Search error: {str(e)}"

# ============================================================================
# VIVIAN'S OPENAI INTEGRATION WITH EMAIL & CALENDAR
# ============================================================================

def get_user_thread(user_id):
    """Get or create thread for user"""
    if user_id not in user_conversations:
        thread = client.beta.threads.create()
        user_conversations[user_id] = thread.id
        print(f"📝 Created thread for user {user_id}")
    return user_conversations[user_id]

async def get_vivian_response(message, user_id):
    """Get response from Vivian's OpenAI assistant with email/calendar integration"""
    try:
        if not ASSISTANT_ID:
            return "⚠️ Vivian not configured - check VIVIAN_ASSISTANT_ID environment variable"
        
        # Get user's thread
        thread_id = get_user_thread(user_id)
        
        # Clean message
        clean_message = message.replace(f'<@{bot.user.id}>', '').strip()
        
        # PR-focused message to assistant with email/calendar context
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f"USER REQUEST: {clean_message}\n\nRespond as Vivian Spencer, PR specialist with email and calendar access. Use your functions for information requests. Keep response under 1200 characters for Discord. Focus on PR strategy and external communications."
        )
        
        # Run assistant
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions="You are Vivian Spencer, PR specialist with email/calendar access. Use your functions for information and schedule requests. Keep responses under 1200 characters. Focus on strategic communications and external relations."
        )
        
        print(f"🏃 Vivian run created: {run.id}")
        
        # Wait for completion
        for attempt in range(20):
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            print(f"🔄 Status: {run_status.status} (attempt {attempt + 1})")
            
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                await handle_vivian_functions(run_status, thread_id)
                continue
            elif run_status.status in ["failed", "cancelled", "expired"]:
                return f"❌ Request {run_status.status}"
            
            await asyncio.sleep(1)
        else:
            return "⏱️ Request timed out - try a simpler question"
        
        # Get response
        messages = client.beta.threads.messages.list(thread_id=thread_id, limit=5)
        for msg in messages.data:
            if msg.role == "assistant":
                response = msg.content[0].text.value
                return format_for_discord_vivian_tight(response)
        
        return "⚠️ No response received"
        
    except Exception as e:
        print(f"❌ Vivian error: {e}")
        return "❌ Something went wrong with PR consultation. Please try again."

async def handle_vivian_functions(run, thread_id):
    """Handle Vivian's function calls with email/calendar integration"""
    tool_outputs = []
    
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        function_name = tool_call.function.name
        
        try:
            arguments = json.loads(tool_call.function.arguments)
        except:
            arguments = {}
        
        print(f"🔧 Vivian Function: {function_name}")
        
        # Handle email functions
        if function_name == "search_emails":
            query = arguments.get('query', '')
            max_results = arguments.get('max_results', 5)
            
            if query:
                emails = search_gmail_messages(query, max_results)
                output = format_emails_for_discord(emails, f"Email Search: '{query}'")
            else:
                output = "📧 No email search query provided"
                
        elif function_name == "get_recent_emails":
            max_results = arguments.get('max_results', 10)
            emails = get_recent_emails(max_results)
            output = format_emails_for_discord(emails, "Recent Emails")
            
        # Handle calendar functions
        elif function_name == "get_today_schedule":
            today_events = []
            all_events = get_calendar_events(days_ahead=1)
            
            local_tz = pytz.timezone(LOCAL_TIMEZONE)
            today = datetime.now(local_tz).date()
            
            for event in all_events:
                try:
                    if hasattr(event['start_time'], 'date'):
                        event_date = event['start_time'].date()
                    else:
                        continue
                    
                    if event_date == today:
                        today_events.append(event)
                        
                except Exception as e:
                    continue
            
            output = format_calendar_events(today_events, "Today's Communications Schedule")
            
        elif function_name == "get_upcoming_events":
            days = arguments.get('days', 7)
            upcoming_events = get_calendar_events(days_ahead=days)
            output = format_calendar_events(upcoming_events, f"Upcoming Events ({days} days)")
            
        # Handle web search
        elif function_name == "web_search":
            query = arguments.get('query', '')
            search_type = arguments.get('search_type', 'general')
            num_results = arguments.get('num_results', 5)
            
            if query:
                search_results = await web_search_fixed(query, search_type, num_results)
                output = search_results
            else:
                output = "🔍 No search query provided"
        
        else:
            output = f"📋 Function '{function_name}' executed"
        
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": output
        })
    
    # Submit outputs
    client.beta.threads.runs.submit_tool_outputs(
        thread_id=thread_id,
        run_id=run.id,
        tool_outputs=tool_outputs
    )
    
    print(f"✅ Submitted {len(tool_outputs)} function outputs")

def format_for_discord_vivian_tight(response):
    """Format response for Discord - TIGHT spacing like Maeve"""
    
    # Remove excessive spacing - make it tighter
    response = response.replace('\n\n\n', '\n')      # Triple to single
    response = response.replace('\n\n', '\n')        # Double to single
    
    # Remove bold formatting that can make responses longer
    response = response.replace('**', '')
    
    # Ensure Discord limit
    if len(response) > 1900:
        response = response[:1900] + "\n\n📱 *More PR insights available!*"
    
    return response.strip()

# ============================================================================
# DISCORD BOT COMMANDS
# ============================================================================

@bot.command(name='ping')
async def ping(ctx):
    """Test connectivity"""
    latency = round(bot.latency * 1000)
    await ctx.send(f"📱 Pong! {ASSISTANT_NAME} online ({latency}ms)")

@bot.command(name='status')
async def status(ctx):
    """Show status"""
    embed = discord.Embed(
        title=f"📱 {ASSISTANT_NAME} - {ASSISTANT_ROLE}",
        description="PR Strategy + Email & Calendar Access",
        color=0x4dabf7
    )
    
    embed.add_field(
        name="🔗 OpenAI Assistant",
        value="✅ Connected" if ASSISTANT_ID else "❌ Not configured",
        inline=True
    )
    
    embed.add_field(
        name="📧 Gmail Access",
        value="✅ Connected" if gmail_service else "❌ Not configured",
        inline=True
    )
    
    embed.add_field(
        name="📅 Calendar Access",
        value="✅ Connected" if calendar_service else "❌ Not configured",
        inline=True
    )
    
    embed.add_field(
        name="🔍 Web Search",
        value="✅ Available" if BRAVE_API_KEY else "❌ Not configured",
        inline=True
    )
    
    embed.add_field(
        name="📱 Specialties",
        value="Email • Calendar • PR Strategy • Web Research",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='emails')
async def emails_command(ctx, *, query=None):
    """Search or get recent emails"""
    async with ctx.typing():
        if query:
            emails = search_gmail_messages(query, 5)
            result = format_emails_for_discord(emails, f"Email Search: '{query}'")
        else:
            emails = get_recent_emails(10)
            result = format_emails_for_discord(emails, "Recent Emails")
        await send_long_message(ctx, result)

@bot.command(name='calendar')
async def calendar_command(ctx, days: int = 7):
    """Get calendar events"""
    async with ctx.typing():
        events = get_calendar_events(days_ahead=days)
        result = format_calendar_events(events, f"Calendar ({days} days)")
        await send_long_message(ctx, result)

@bot.command(name='search')
async def search_command(ctx, *, query):
    """Direct web search"""
    async with ctx.typing():
        results = await web_search_fixed(query)
        await send_long_message(ctx, results)

@bot.command(name='help')
async def help_command(ctx):
    """Show help"""
    embed = discord.Embed(
        title=f"📱 {ASSISTANT_NAME} - {ASSISTANT_ROLE}",
        description="PR Strategy with Email & Calendar Integration",
        color=0x4dabf7
    )
    
    embed.add_field(
        name="💬 How to Use",
        value=f"• Mention @{ASSISTANT_NAME} for PR advice\n• Ask about emails, calendar, trends\n• DM me directly",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Commands",
        value="• `!emails [query]` - Search or get recent emails\n• `!calendar [days]` - Get calendar events\n• `!search [query]` - Web search\n• `!ping` - Test\n• `!status` - Status\n• `!help` - This help",
        inline=False
    )
    
    embed.add_field(
        name="📱 Enhanced Features",
        value="• **Gmail Integration** - Search and review work emails\n• **Calendar Access** - Check schedule and meetings\n• **PR Strategy** - Communications and social media insights\n• **Web Research** - Current trends and information",
        inline=False
    )
    
    await ctx.send(embed=embed)

# ============================================================================
# MESSAGE HANDLING
# ============================================================================

@bot.event
async def on_ready():
    print(f"📱 {ASSISTANT_NAME} is online as {bot.user}")
    print(f"🔗 Connected to {len(bot.guilds)} server(s)")
    print(f"👀 Monitoring: {', '.join(ALLOWED_CHANNELS)}")
    print(f"🔧 Assistant: {'✅' if ASSISTANT_ID else '❌'}")
    print(f"📧 Gmail: {'✅' if gmail_service else '❌'}")
    print(f"📅 Calendar: {'✅' if calendar_service else '❌'}")
    print(f"🔍 Search: {'✅' if BRAVE_API_KEY else '❌'}")
    print(f"📱 Ready for PR consultation with email & calendar access!")

@bot.event
async def on_message(message):
    # Skip bot's own messages
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Only respond in allowed channels or DMs
    if not isinstance(message.channel, discord.DMChannel) and message.channel.name not in ALLOWED_CHANNELS:
        return

    # Respond to mentions or DMs
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        try:
            async with message.channel.typing():
                response = await get_vivian_response(message.content, message.author.id)
                await send_long_message(message, response)
        except Exception as e:
            print(f"❌ Message error: {e}")
            await message.reply("❌ Something went wrong with PR consultation. Please try again.")

async def send_long_message(target, content):
    """Send long messages in chunks"""
    if len(content) <= 2000:
        if hasattr(target, 'send'):
            await target.send(content)
        else:
            await target.reply(content)
    else:
        chunks = [content[i:i+1800] for i in range(0, len(content), 1800)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                if hasattr(target, 'send'):
                    await target.send(chunk)
                else:
                    await target.reply(chunk)
            else:
                await target.channel.send(f"*(Part {i+1})*\n{chunk}")
            await asyncio.sleep(0.5)

@bot.event
async def on_command_error(ctx, error):
    """Handle errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    else:
        await ctx.send(f"❌ Error: {str(error)}")

# ============================================================================
# START THE BOT
# ============================================================================

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables")
        exit(1)
    
    print(f"📱 Starting {ASSISTANT_NAME} with Gmail & Calendar Integration...")
    bot.run(DISCORD_TOKEN)