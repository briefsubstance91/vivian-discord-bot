#!/usr/bin/env python3
"""
VIVIAN SPENCER - DISCORD BOT (COMPLETE ENHANCED VERSION)
PR & Communications Specialist with Full Calendar Integration & Rose Coordination
Based on Rose's proven architecture with work calendar focus and PR specialization
"""
import pytz
import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
import time
import re
from dotenv import load_dotenv
from openai import OpenAI
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import traceback
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Load environment variables
load_dotenv()

# Vivian's PR & Communications configuration
ASSISTANT_NAME = "Vivian Spencer"
ASSISTANT_ROLE = "PR & Communications Specialist (Complete Enhanced)"
ALLOWED_CHANNELS = ['social-overview', 'news-feed', 'external-communications', 'project-overview', 'work-inbox', 'meeting-notes', 'general']

# Environment variables with fallbacks
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("VIVIAN_DISCORD_TOKEN")
ASSISTANT_ID = os.getenv("VIVIAN_ASSISTANT_ID") or os.getenv("ASSISTANT_ID")
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Work Calendar integration (Vivian's specialty)
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
BG_WORK_CALENDAR_ID = os.getenv('BG_WORK_CALENDAR_ID')  # Primary work calendar
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')

# Validate critical environment variables
if not DISCORD_TOKEN:
    print("❌ CRITICAL: DISCORD_TOKEN not found in environment variables")
    exit(1)

if not OPENAI_API_KEY:
    print("❌ CRITICAL: OPENAI_API_KEY not found in environment variables")
    exit(1)

if not ASSISTANT_ID:
    print("❌ CRITICAL: VIVIAN_ASSISTANT_ID not found in environment variables")
    exit(1)

# Discord setup
try:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
except Exception as e:
    print(f"❌ CRITICAL: Discord bot initialization failed: {e}")
    exit(1)

# OpenAI setup
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"❌ CRITICAL: OpenAI client initialization failed: {e}")
    exit(1)

# Google Calendar and Gmail setup
calendar_service = None
gmail_service = None
accessible_calendars = []
service_account_email = None
work_calendar_accessible = False

def test_work_calendar_access(calendar_id, calendar_name):
    """Test work calendar access with comprehensive error handling"""
    if not calendar_service or not calendar_id:
        return False
    
    try:
        calendar_info = calendar_service.calendars().get(calendarId=calendar_id).execute()
        print(f"✅ {calendar_name} accessible: {calendar_info.get('summary', 'Unknown')}")
        
        now = datetime.now(pytz.UTC)
        past_24h = now - timedelta(hours=24)
        
        events_result = calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=past_24h.isoformat(),
            timeMax=now.isoformat(),
            maxResults=5,
            singleEvents=True
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ {calendar_name} events: {len(events)} found")
        
        return True
        
    except HttpError as e:
        error_code = e.resp.status
        print(f"❌ {calendar_name} HTTP Error {error_code}")
        return False
    except Exception as e:
        print(f"❌ {calendar_name} error: {e}")
        return False

# Initialize Google services
try:
    if GOOGLE_SERVICE_ACCOUNT_JSON:
        credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                'https://www.googleapis.com/auth/calendar.readonly',
                'https://www.googleapis.com/auth/gmail.readonly'
            ]
        )
        calendar_service = build('calendar', 'v3', credentials=credentials)
        gmail_service = build('gmail', 'v1', credentials=credentials)
        print("✅ Google services initialized")
        
        service_account_email = credentials_info.get('client_email')
        print(f"📧 Service Account: {service_account_email}")
        
        # Test work calendar access
        if BG_WORK_CALENDAR_ID:
            if test_work_calendar_access(BG_WORK_CALENDAR_ID, "BG Work Calendar"):
                accessible_calendars.append(("BG Work Calendar", BG_WORK_CALENDAR_ID, "work"))
                work_calendar_accessible = True
        
        # Test primary calendar as fallback
        if not work_calendar_accessible:
            if test_work_calendar_access('primary', "Primary Work Calendar"):
                accessible_calendars.append(("Primary Work Calendar", "primary", "work"))
                work_calendar_accessible = True
        
        print(f"\n📅 Work calendars accessible: {len(accessible_calendars)}")
        for name, _, _ in accessible_calendars:
            print(f"   ✅ {name}")
            
    else:
        print("⚠️ Google Calendar credentials not found")
        
except Exception as e:
    print(f"❌ Google services setup error: {e}")
    calendar_service = None
    gmail_service = None
    accessible_calendars = []

# Memory and duplicate prevention systems
user_conversations = {}
processing_messages = set()
last_response_time = {}

print(f"💼 Starting {ASSISTANT_NAME} - {ASSISTANT_ROLE}...")

# ============================================================================
# WORK CALENDAR FUNCTIONS (Vivian's Specialty)
# ============================================================================

def get_work_calendar_events(calendar_id, start_time, end_time, max_results=100):
    """Get work calendar events with enhanced error handling"""
    if not calendar_service:
        return []
    
    try:
        events_result = calendar_service.events().list(
            calendarId=calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
        
    except Exception as e:
        print(f"❌ Error getting work events from {calendar_id}: {e}")
        return []

def format_work_event(event, user_timezone=None):
    """Format a work calendar event with PR context"""
    if user_timezone is None:
        user_timezone = pytz.timezone('America/Toronto')
    
    start = event['start'].get('dateTime', event['start'].get('date'))
    title = event.get('summary', 'Untitled Meeting')
    location = event.get('location', '')
    description = event.get('description', '')
    
    # Add work context with PR intelligence
    if any(keyword in title.lower() for keyword in ['meeting', 'call', 'sync', 'standup', 'review']):
        title = f"💼 {title}"
    elif any(keyword in title.lower() for keyword in ['interview', 'media', 'press', 'pr']):
        title = f"📺 {title}"
    elif any(keyword in title.lower() for keyword in ['presentation', 'demo', 'launch']):
        title = f"🎯 {title}"
    else:
        title = f"📅 {title}"
    
    if 'T' in start:  # Has time
        try:
            utc_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            local_time = utc_time.astimezone(user_timezone)
            time_str = local_time.strftime('%I:%M %p')
            
            location_str = f" ({location})" if location else ""
            return f"• {time_str}: {title}{location_str}"
        except Exception as e:
            print(f"❌ Error formatting work event: {e}")
            return f"• {title}"
    else:  # All day event
        location_str = f" ({location})" if location else ""
        return f"• All Day: {title}{location_str}"

def get_work_schedule_today():
    """Get today's work schedule with PR context"""
    if not calendar_service or not accessible_calendars:
        return "📅 **Today's Work Schedule:** Work calendar integration not available\n\n💼 **PR Focus:** Review calendar manually for meeting prep and stakeholder communications"
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        
        today_toronto = datetime.now(toronto_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_toronto = today_toronto.replace(hour=23, minute=59, second=59)
        
        today_utc = today_toronto.astimezone(pytz.UTC)
        tomorrow_utc = tomorrow_toronto.astimezone(pytz.UTC)
        
        all_events = []
        
        for calendar_name, calendar_id, calendar_type in accessible_calendars:
            events = get_work_calendar_events(calendar_id, today_utc, tomorrow_utc)
            for event in events:
                formatted = format_work_event(event, toronto_tz)
                all_events.append((event, formatted, calendar_type, calendar_name))
        
        if not all_events:
            return "📅 **Today's Work Schedule:** No work meetings scheduled\n\n💼 **PR Opportunity:** Perfect day for strategic communications, content creation, and stakeholder outreach"
        
        def get_event_time(event_tuple):
            event = event_tuple[0]
            start = event['start'].get('dateTime', event['start'].get('date'))
            try:
                if 'T' in start:
                    utc_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    return utc_time.astimezone(toronto_tz)
                else:
                    return datetime.fromisoformat(start)
            except:
                return datetime.now(toronto_tz)
        
        all_events.sort(key=get_event_time)
        
        formatted_events = [event_tuple[1] for event_tuple in all_events]
        
        header = f"📅 **Today's Work Schedule:** {len(all_events)} meetings/events"
        
        return header + "\n\n" + "\n".join(formatted_events[:15])
        
    except Exception as e:
        print(f"❌ Work calendar error: {e}")
        return "📅 **Today's Work Schedule:** Error retrieving work calendar data"

def get_work_upcoming_events(days=7):
    """Get upcoming work events with PR planning context"""
    if not calendar_service or not accessible_calendars:
        return f"📅 **Upcoming Work Events ({days} days):** Work calendar integration not available"
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        
        start_toronto = datetime.now(toronto_tz)
        end_toronto = start_toronto + timedelta(days=days)
        
        start_utc = start_toronto.astimezone(pytz.UTC)
        end_utc = end_toronto.astimezone(pytz.UTC)
        
        all_events = []
        
        for calendar_name, calendar_id, calendar_type in accessible_calendars:
            events = get_work_calendar_events(calendar_id, start_utc, end_utc)
            for event in events:
                all_events.append((event, calendar_type, calendar_name))
        
        if not all_events:
            return f"📅 **Upcoming Work Events ({days} days):** No work meetings scheduled\n\n💼 **PR Strategy:** Clear calendar for strategic planning and stakeholder engagement"
        
        events_by_date = defaultdict(list)
        
        for event, calendar_type, calendar_name in all_events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            try:
                if 'T' in start:
                    utc_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    toronto_time = utc_time.astimezone(toronto_tz)
                    date_str = toronto_time.strftime('%a %m/%d')
                    formatted = format_work_event(event, toronto_tz)
                    events_by_date[date_str].append(formatted)
                else:
                    date_obj = datetime.fromisoformat(start)
                    date_str = date_obj.strftime('%a %m/%d')
                    formatted = format_work_event(event, toronto_tz)
                    events_by_date[date_str].append(formatted)
            except Exception as e:
                print(f"❌ Date parsing error: {e}")
                continue
        
        formatted = []
        total_events = len(all_events)
        
        for date, day_events in list(events_by_date.items())[:7]:
            formatted.append(f"**{date}**")
            formatted.extend(day_events[:6])
        
        header = f"📅 **Upcoming Work Events ({days} days):** {total_events} total"
        
        return header + "\n\n" + "\n".join(formatted)
        
    except Exception as e:
        print(f"❌ Work calendar error: {e}")
        return f"📅 **Upcoming Work Events ({days} days):** Error retrieving work calendar data"

def get_work_morning_briefing():
    """Work-focused morning briefing with PR intelligence"""
    if not calendar_service or not accessible_calendars:
        return "🌅 **Work Morning Briefing:** Work calendar integration not available"
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        
        today_schedule = get_work_schedule_today()
        
        # Get tomorrow's work events
        today_toronto = datetime.now(toronto_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_toronto = today_toronto + timedelta(days=1)
        day_after_toronto = tomorrow_toronto + timedelta(days=1)
        
        tomorrow_utc = tomorrow_toronto.astimezone(pytz.UTC)
        day_after_utc = day_after_toronto.astimezone(pytz.UTC)
        
        tomorrow_events = []
        
        for calendar_name, calendar_id, calendar_type in accessible_calendars:
            events = get_work_calendar_events(calendar_id, tomorrow_utc, day_after_utc)
            tomorrow_events.extend([(event, calendar_type, calendar_name) for event in events])
        
        if tomorrow_events:
            tomorrow_formatted = []
            for event, calendar_type, calendar_name in tomorrow_events[:4]:
                formatted = format_work_event(event, toronto_tz)
                tomorrow_formatted.append(formatted)
            tomorrow_preview = "📅 **Tomorrow's Work Preview:**\n" + "\n".join(tomorrow_formatted)
        else:
            tomorrow_preview = "📅 **Tomorrow's Work Preview:** Clear schedule - strategic PR planning opportunity"
        
        current_time = datetime.now(toronto_tz).strftime('%A, %B %d')
        briefing = f"🌅 **Good Morning! Work & PR Briefing for {current_time}**\n\n{today_schedule}\n\n{tomorrow_preview}\n\n💼 **PR Focus:** Prioritize stakeholder communications and strategic messaging"
        
        return briefing
        
    except Exception as e:
        print(f"❌ Work morning briefing error: {e}")
        return "🌅 **Work Morning Briefing:** Error generating briefing"

def export_work_data_for_rose():
    """Export work calendar data for Rose's executive briefings"""
    if not calendar_service or not accessible_calendars:
        return {
            'status': 'unavailable',
            'message': 'Work calendar integration not available',
            'work_events': [],
            'pr_insights': []
        }
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        now = datetime.now(toronto_tz)
        
        # Get next 7 days of work events for Rose
        end_time = now + timedelta(days=7)
        
        all_events = []
        
        for calendar_name, calendar_id, calendar_type in accessible_calendars:
            events = get_work_calendar_events(calendar_id, now, end_time)
            all_events.extend([(event, calendar_name) for event in events])
        
        formatted_events = []
        pr_insights = []
        
        for event, calendar_name in all_events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            title = event.get('summary', 'Untitled Meeting')
            location = event.get('location', '')
            description = event.get('description', '')
            
            # Format for Rose consumption
            if 'T' in start:
                utc_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                toronto_time = utc_time.astimezone(toronto_tz)
                date_str = toronto_time.strftime('%A, %B %d')
                time_str = toronto_time.strftime('%I:%M %p')
                
                formatted_events.append({
                    'date': date_str,
                    'time': time_str,
                    'title': title,
                    'location': location,
                    'type': 'work_meeting',
                    'calendar': calendar_name
                })
                
                # Generate PR insights
                if any(keyword in title.lower() for keyword in ['interview', 'media', 'press', 'pr']):
                    pr_insights.append({
                        'date': date_str,
                        'time': time_str,
                        'insight': f"Media/PR event: {title}",
                        'preparation': 'Prepare talking points, media kit, and follow-up materials'
                    })
                elif any(keyword in title.lower() for keyword in ['presentation', 'demo', 'launch']):
                    pr_insights.append({
                        'date': date_str,
                        'time': time_str,
                        'insight': f"High-visibility event: {title}",
                        'preparation': 'Coordinate communications strategy and stakeholder updates'
                    })
        
        return {
            'status': 'success',
            'message': f'Work calendar data for next 7 days ({len(formatted_events)} events)',
            'work_events': formatted_events,
            'pr_insights': pr_insights,
            'calendar_source': 'Vivian Spencer - PR & Communications',
            'exported_at': now.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error exporting work data for Rose: {e}")
        return {
            'status': 'error',
            'message': f'Error exporting work data: {str(e)}',
            'work_events': [],
            'pr_insights': []
        }

# ============================================================================
# PR & COMMUNICATIONS RESEARCH FUNCTIONS
# ============================================================================

async def pr_research_enhanced(query, focus_area="pr", num_results=3):
    """Enhanced PR and communications research with comprehensive error handling"""
    if not BRAVE_API_KEY:
        return "🔍 PR research requires Brave Search API configuration", []
    
    try:
        pr_query = f"{query} {focus_area} communications PR strategy media relations 2025"
        
        headers = {
            'X-Subscription-Token': BRAVE_API_KEY,
            'Accept': 'application/json'
        }
        
        params = {
            'q': pr_query,
            'count': num_results,
            'country': 'US',
            'search_lang': 'en',
            'ui_lang': 'en',
            'safesearch': 'moderate'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.search.brave.com/res/v1/web/search', 
                                   headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('web', {}).get('results', [])
                    
                    if not results:
                        return "🔍 No PR research results found for this query", []
                    
                    formatted_results = []
                    sources = []
                    
                    for i, result in enumerate(results[:num_results]):
                        title = result.get('title', 'No title')
                        snippet = result.get('description', 'No description')
                        url = result.get('url', '')
                        
                        domain = url.split('/')[2] if len(url.split('/')) > 2 else 'Unknown'
                        
                        formatted_results.append(f"**{i+1}. {title}**\n{snippet}")
                        sources.append({
                            'number': i+1,
                            'title': title,
                            'url': url,
                            'domain': domain
                        })
                    
                    return "\n\n".join(formatted_results), sources
                else:
                    return f"🔍 PR search error: HTTP {response.status}", []
                    
    except asyncio.TimeoutError:
        return "🔍 PR search timed out", []
    except Exception as e:
        print(f"❌ PR search error: {e}")
        return f"🔍 PR search error: Please try again", []

async def news_monitoring_search(query, num_results=5):
    """News monitoring for PR awareness"""
    if not BRAVE_API_KEY:
        return "📰 News monitoring requires Brave Search API configuration", []
    
    try:
        news_query = f"{query} news recent 2025"
        
        headers = {
            'X-Subscription-Token': BRAVE_API_KEY,
            'Accept': 'application/json'
        }
        
        params = {
            'q': news_query,
            'count': num_results,
            'country': 'US',
            'search_lang': 'en',
            'ui_lang': 'en',
            'safesearch': 'moderate',
            'freshness': 'pd'  # Past day for fresh news
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get('https://api.search.brave.com/res/v1/web/search', 
                                   headers=headers, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('web', {}).get('results', [])
                    
                    if not results:
                        return "📰 No recent news found for this query", []
                    
                    formatted_results = []
                    sources = []
                    
                    for i, result in enumerate(results[:num_results]):
                        title = result.get('title', 'No title')
                        snippet = result.get('description', 'No description')
                        url = result.get('url', '')
                        
                        domain = url.split('/')[2] if len(url.split('/')) > 2 else 'Unknown'
                        
                        formatted_results.append(f"**{i+1}. {title}**\n{snippet}")
                        sources.append({
                            'number': i+1,
                            'title': title,
                            'url': url,
                            'domain': domain
                        })
                    
                    return "\n\n".join(formatted_results), sources
                else:
                    return f"📰 News search error: HTTP {response.status}", []
                    
    except asyncio.TimeoutError:
        return "📰 News search timed out", []
    except Exception as e:
        print(f"❌ News search error: {e}")
        return f"📰 News search error: Please try again", []

# ============================================================================
# ENHANCED FUNCTION HANDLING
# ============================================================================

async def handle_vivian_functions_enhanced(run, thread_id):
    """Enhanced function handling with work calendar and PR functions"""
    
    if not run or not hasattr(run, 'required_action') or not run.required_action:
        return
        
    if not hasattr(run.required_action, 'submit_tool_outputs') or not run.required_action.submit_tool_outputs:
        return
    
    if not hasattr(run.required_action.submit_tool_outputs, 'tool_calls') or not run.required_action.submit_tool_outputs.tool_calls:
        return
    
    tool_outputs = []
    
    for tool_call in run.required_action.submit_tool_outputs.tool_calls:
        function_name = getattr(tool_call.function, 'name', 'unknown')
        
        try:
            arguments_str = getattr(tool_call.function, 'arguments', '{}')
            arguments = json.loads(arguments_str) if arguments_str else {}
        except (json.JSONDecodeError, AttributeError) as e:
            print(f"❌ Error parsing function arguments: {e}")
            arguments = {}
        
        print(f"💼 Vivian Function: {function_name}")
        print(f"📋 Arguments: {arguments}")
        
        try:
            # WORK CALENDAR FUNCTIONS
            if function_name == "get_work_schedule_today":
                output = get_work_schedule_today()
                
            elif function_name == "get_work_upcoming_events":
                days = arguments.get('days', 7)
                output = get_work_upcoming_events(days)
                
            elif function_name == "get_work_morning_briefing":
                output = get_work_morning_briefing()
                
            elif function_name == "export_work_data_for_rose":
                export_data = export_work_data_for_rose()
                if export_data['status'] == 'success':
                    output = f"📊 **Work Data Export:** {export_data['message']}\n\n"
                    if export_data['work_events']:
                        output += "**Sample Work Events:**\n"
                        for event in export_data['work_events'][:3]:
                            output += f"• {event['date']} at {event['time']}: {event['title']}\n"
                    if export_data['pr_insights']:
                        output += "\n**PR Insights:**\n"
                        for insight in export_data['pr_insights'][:2]:
                            output += f"• {insight['insight']}\n"
                    output += f"\n🤝 **Rose Integration:** Data exported for executive briefing"
                else:
                    output = f"❌ **Export Failed:** {export_data['message']}"
            
            # PR RESEARCH FUNCTIONS
            elif function_name == "pr_research":
                query = arguments.get('query', '')
                focus = arguments.get('focus', 'pr')
                num_results = arguments.get('num_results', 3)
                
                if query:
                    search_results, sources = await pr_research_enhanced(query, focus, num_results)
                    output = f"💼 **PR Research:** {query}\n\n{search_results}"
                    
                    if sources:
                        output += "\n\n📚 **Sources:**\n"
                        for source in sources:
                            output += f"({source['number']}) {source['title']} - {source['domain']}\n"
                else:
                    output = "🔍 No PR research query provided"
                    
            elif function_name == "news_monitoring":
                query = arguments.get('query', '')
                num_results = arguments.get('num_results', 5)
                
                if query:
                    search_results, sources = await news_monitoring_search(query, num_results)
                    output = f"📰 **News Monitoring:** {query}\n\n{search_results}"
                    
                    if sources:
                        output += "\n\n📚 **News Sources:**\n"
                        for source in sources:
                            output += f"({source['number']}) {source['title']} - {source['domain']}\n"
                else:
                    output = "📰 No news monitoring query provided"
                
            else:
                output = f"❓ Function {function_name} not implemented yet"
                
        except Exception as e:
            print(f"❌ Function execution error: {e}")
            output = f"❌ Error executing {function_name}: {str(e)}"
        
        tool_outputs.append({
            "tool_call_id": tool_call.id,
            "output": output[:1500]  # Keep within reasonable limits
        })
    
    # Submit tool outputs
    try:
        if tool_outputs:
            client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print(f"✅ Submitted {len(tool_outputs)} tool outputs successfully")
    except Exception as e:
        print(f"❌ Error submitting tool outputs: {e}")

# ============================================================================
# MAIN CONVERSATION HANDLER
# ============================================================================

async def get_vivian_response(message, user_id):
    """Get response from Vivian's enhanced OpenAI assistant"""
    try:
        if not ASSISTANT_ID:
            return "⚠️ Vivian not configured - check VIVIAN_ASSISTANT_ID environment variable"
        
        if user_id in user_conversations and user_conversations[user_id].get('active', False):
            return "💼 Vivian is currently analyzing your PR strategy. Please wait a moment..."
        
        if user_id not in user_conversations:
            thread = client.beta.threads.create()
            user_conversations[user_id] = {'thread_id': thread.id, 'active': False}
            print(f"💼 Created PR thread for user {user_id}")
        
        user_conversations[user_id]['active'] = True
        thread_id = user_conversations[user_id]['thread_id']
        
        clean_message = message.replace(f'<@{bot.user.id}>', '').strip() if hasattr(bot, 'user') and bot.user else message.strip()
        
        # Get current date context for Vivian
        toronto_tz = pytz.timezone('America/Toronto')
        now = datetime.now(toronto_tz)
        today_formatted = now.strftime('%A, %B %d, %Y')
        today_date = now.strftime('%Y-%m-%d')
        tomorrow = now + timedelta(days=1)
        tomorrow_formatted = tomorrow.strftime('%A, %B %d, %Y') 
        tomorrow_date = tomorrow.strftime('%Y-%m-%d')

        enhanced_message = f"""USER PR & COMMUNICATIONS REQUEST: {clean_message}

CURRENT DATE & TIME CONTEXT:
- TODAY: {today_formatted} ({today_date})
- TOMORROW: {tomorrow_formatted} ({tomorrow_date})
- TIMEZONE: America/Toronto

RESPONSE GUIDELINES:
- Use professional PR/communications formatting with strategic headers
- AVAILABLE WORK CALENDARS: {[name for name, _, _ in accessible_calendars]}
- Apply PR specialist tone: strategic, media-savvy, stakeholder-focused
- Keep main content under 1200 characters for Discord efficiency
- Use headers like: 💼 **PR Strategy:** or 📊 **Communications Analysis:**
- When user says "tomorrow" use {tomorrow_date} ({tomorrow_formatted})
- When user says "today" use {today_date} ({today_formatted})
- All times are in Toronto timezone (America/Toronto)
- Focus on work calendar for meeting prep and stakeholder coordination"""
        
        try:
            client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=enhanced_message
            )
        except Exception as e:
            if "while a run" in str(e) and "is active" in str(e):
                print("⏳ Waiting for previous PR analysis to complete...")
                await asyncio.sleep(3)
                try:
                    client.beta.threads.messages.create(
                        thread_id=thread_id,
                        role="user",
                        content=enhanced_message
                    )
                except Exception as e2:
                    print(f"❌ Still can't add message: {e2}")
                    return "💼 PR office is busy. Please try again in a moment."
            else:
                print(f"❌ Message creation error: {e}")
                return "❌ Error creating PR message. Please try again."
        
        try:
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=ASSISTANT_ID,
                instructions="""You are Vivian Spencer, PR & Communications specialist with work calendar integration and Rose coordination.

PR & COMMUNICATIONS APPROACH:
- Use work calendar functions to provide meeting prep and stakeholder coordination
- Apply strategic communications perspective with media intelligence
- Include actionable PR recommendations with timeline coordination

FORMATTING: Use professional PR formatting with strategic headers (💼 📊 📰 🎯 📱) and provide organized, media-savvy guidance.

STRUCTURE:
💼 **PR Strategy:** [strategic overview with work calendar insights]
📊 **Communications Analysis:** [research-backed PR recommendations]
🎯 **Action Items:** [specific next steps with timing and stakeholder focus]

Keep core content focused and always provide strategic context with work calendar coordination. Coordinate with Rose for comprehensive executive assistance."""
            )
        except Exception as e:
            print(f"❌ Run creation error: {e}")
            return "❌ Error starting PR analysis. Please try again."
        
        print(f"💼 Vivian run created: {run.id}")
        
        for attempt in range(20):
            try:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )
            except Exception as e:
                print(f"❌ Error retrieving run status: {e}")
                await asyncio.sleep(2)
                continue
            
            print(f"🔄 Status: {run_status.status} (attempt {attempt + 1})")
            
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                await handle_vivian_functions_enhanced(run_status, thread_id)
            elif run_status.status in ["failed", "cancelled", "expired"]:
                print(f"❌ Run {run_status.status}")
                return "❌ PR analysis interrupted. Please try again."
            
            await asyncio.sleep(2)
        else:
            print("⏱️ Run timed out")
            return "⏱️ PR office is busy. Please try again in a moment."
        
        try:
            messages = client.beta.threads.messages.list(thread_id=thread_id, limit=5)
            for msg in messages.data:
                if msg.role == "assistant":
                    response = msg.content[0].text.value
                    return format_for_discord_vivian(response)
        except Exception as e:
            print(f"❌ Error retrieving messages: {e}")
            return "❌ Error retrieving PR guidance. Please try again."
        
        return "💼 PR analysis unclear. Please try again with a different approach."
        
    except Exception as e:
        print(f"❌ Vivian error: {e}")
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return "❌ Something went wrong with PR strategy. Please try again!"
    finally:
        if user_id in user_conversations:
            user_conversations[user_id]['active'] = False

def format_for_discord_vivian(response):
    """Format response for Discord with error handling"""
    try:
        if not response or not isinstance(response, str):
            return "💼 PR strategy processing. Please try again."
        
        response = response.replace('\n\n\n\n', '\n\n')
        response = response.replace('\n\n\n', '\n\n')
        
        if len(response) > 1900:
            response = response[:1900] + "\n\n💼 *(PR insights continue)*"
        
        return response.strip()
        
    except Exception as e:
        print(f"❌ Discord formatting error: {e}")
        return "💼 PR message needs refinement. Please try again."

# ============================================================================
# ENHANCED MESSAGE HANDLING
# ============================================================================

async def send_long_message(original_message, response):
    """Send response with length handling and error recovery"""
    try:
        if len(response) <= 2000:
            await original_message.reply(response)
        else:
            chunks = []
            current_chunk = ""
            
            for line in response.split('\n'):
                if len(current_chunk + line + '\n') > 1900:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = line + '\n'
                else:
                    current_chunk += line + '\n'
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await original_message.reply(chunk)
                else:
                    await original_message.channel.send(chunk)
                    
    except discord.HTTPException as e:
        print(f"❌ Discord HTTP error: {e}")
        try:
            await original_message.reply("💼 PR guidance too complex for Discord. Please try a more specific request.")
        except:
            pass
    except Exception as e:
        print(f"❌ Message sending error: {e}")

# ============================================================================
# DISCORD BOT EVENT HANDLERS
# ============================================================================

@bot.event
async def on_ready():
    """Bot startup with comprehensive initialization"""
    try:
        print(f"✅ {ASSISTANT_NAME} has awakened!")
        print(f"🤖 Connected as: {bot.user.name} (ID: {bot.user.id})")
        print(f"🎯 Role: {ASSISTANT_ROLE}")
        print(f"📅 Work Calendar Status: {len(accessible_calendars)} accessible calendars")
        print(f"🔍 PR Research: {'Enabled' if BRAVE_API_KEY else 'Disabled'}")
        print(f"🏢 Allowed channels: {', '.join(ALLOWED_CHANNELS)}")
        
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="💼 Work Calendar & PR Strategy"
            )
        )
        print("💼 Vivian is ready for complete PR & communications assistance!")
        
    except Exception as e:
        print(f"❌ Startup error: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler"""
    print(f"❌ Discord error in {event}: {traceback.format_exc()}")

@bot.event
async def on_message(message):
    """Enhanced message handling following team patterns"""
    try:
        if message.author == bot.user:
            return
        
        await bot.process_commands(message)
        
        channel_name = message.channel.name.lower() if hasattr(message.channel, 'name') else 'dm'
        is_dm = isinstance(message.channel, discord.DMChannel)
        is_allowed_channel = any(allowed in channel_name for allowed in ALLOWED_CHANNELS)
        
        if not (is_dm or is_allowed_channel):
            return

        if bot.user.mentioned_in(message) or is_dm:
            
            message_key = f"{message.author.id}_{message.content[:50]}"
            current_time = time.time()
            
            if message_key in processing_messages:
                return
            
            if message.author.id in last_response_time:
                if current_time - last_response_time[message.author.id] < 5:
                    return
            
            processing_messages.add(message_key)
            last_response_time[message.author.id] = current_time
            
            try:
                async with message.channel.typing():
                    response = await get_vivian_response(message.content, message.author.id)
                    await send_long_message(message, response)
            except Exception as e:
                print(f"❌ Message error: {e}")
                print(f"📋 Message traceback: {traceback.format_exc()}")
                try:
                    await message.reply("❌ Something went wrong with PR consultation. Please try again!")
                except:
                    pass
            finally:
                processing_messages.discard(message_key)
                    
    except Exception as e:
        print(f"❌ Message event error: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")

# ============================================================================
# ENHANCED COMMANDS
# ============================================================================

@bot.command(name='ping')
async def ping_command(ctx):
    """Test Vivian's connectivity with PR flair"""
    try:
        latency = round(bot.latency * 1000)
        await ctx.send(f"💼 Pong! PR response time: {latency}ms")
    except Exception as e:
        print(f"❌ Ping command error: {e}")
        await ctx.send("💼 PR ping experiencing issues.")

@bot.command(name='help')
async def help_command(ctx):
    """Enhanced help command"""
    try:
        help_text = f"""💼 **{ASSISTANT_NAME} - PR & Communications Commands**

**📅 Work Calendar & Scheduling:**
• `!work-today` - Today's work schedule with PR context
• `!work-upcoming [days]` - Upcoming work events (default 7 days)
• `!work-briefing` / `!work-daily` / `!work-morning` - Work morning briefing
• `!work-schedule [timeframe]` - Flexible work schedule view
• `!work-agenda` - Comprehensive work agenda overview

**🔍 PR & Communications Research:**
• `!pr-research <query>` - Strategic PR research
• `!news-monitor <query>` - News monitoring and analysis
• `!communications <topic>` - Communications strategy insights

**🤝 Rose Integration:**
• `!export-for-rose` - Export work data for Rose's executive briefings
• `!coordinate-with-rose` - Coordinate scheduling with Rose

**💼 PR Functions:**
• `!status` - System and work calendar status
• `!ping` - Test connectivity
• `!help` - This command menu

**📱 Usage:**
• Mention @{bot.user.name if bot.user else 'Vivian'} in any message
• Available in: {', '.join(ALLOWED_CHANNELS)}

**💡 Example Commands:**
• `!work-briefing` - Get comprehensive work morning briefing
• `!work-today` - See today's work schedule with PR context
• `!work-upcoming 3` - See next 3 days of work events
• `!pr-research crisis communication` - Research PR strategies
• "What's my work schedule today?" - Natural language request
"""
        
        await ctx.send(help_text)
        
    except Exception as e:
        print(f"❌ Help command error: {e}")
        await ctx.send("💼 Help system needs calibration. Please try again.")

@bot.command(name='status')
async def status_command(ctx):
    """PR system status with comprehensive diagnostics"""
    try:
        calendar_status = "❌ No work calendars accessible"
        if accessible_calendars:
            calendar_names = [name for name, _, _ in accessible_calendars]
            calendar_status = f"✅ {len(accessible_calendars)} work calendars: {', '.join(calendar_names)}"
        
        research_status = "✅ Enabled" if BRAVE_API_KEY else "❌ Disabled"
        assistant_status = "✅ Connected" if ASSISTANT_ID else "❌ Not configured"
        
        sa_info = "Not configured"
        if service_account_email:
            sa_info = f"✅ {service_account_email}"
        
        status_text = f"""💼 **{ASSISTANT_NAME} PR Status**

**🤖 Core Systems:**
• Discord: ✅ Connected as {bot.user.name if bot.user else 'Unknown'}
• OpenAI Assistant: {assistant_status}
• Service Account: {sa_info}

**📅 Work Calendar Integration:**
• Status: {calendar_status}
• Timezone: 🇨🇦 Toronto (America/Toronto)
• Gmail Access: {'✅ Connected' if gmail_service else '❌ Not configured'}

**🔍 PR Research:**
• Brave Search API: {research_status}
• News Monitoring: {research_status}

**💼 PR Features:**
• Active conversations: {len(user_conversations)}
• Channels: {', '.join(ALLOWED_CHANNELS)}
• Rose Integration: {'✅ Available' if accessible_calendars else '❌ Limited'}

**⚡ Performance:**
• Uptime: Ready for PR assistance
• Memory: {len(processing_messages)} processing"""
        
        await ctx.send(status_text)
        
    except Exception as e:
        print(f"❌ Status command error: {e}")
        await ctx.send("💼 Status diagnostics experiencing issues. Please try again.")

@bot.command(name='work-today')
async def work_today_command(ctx):
    """Today's work schedule command"""
    try:
        async with ctx.typing():
            schedule = get_work_schedule_today()
            await ctx.send(schedule)
    except Exception as e:
        print(f"❌ Work today command error: {e}")
        await ctx.send("💼 Today's work schedule unavailable. Please try again.")

@bot.command(name='work-upcoming')
async def work_upcoming_command(ctx, days: int = 7):
    """Upcoming work events command"""
    try:
        async with ctx.typing():
            days = max(1, min(days, 30))
            events = get_work_upcoming_events(days)
            await ctx.send(events)
    except Exception as e:
        print(f"❌ Work upcoming command error: {e}")
        await ctx.send("💼 Upcoming work events unavailable. Please try again.")

@bot.command(name='work-briefing')
async def work_briefing_command(ctx):
    """Work morning briefing command"""
    try:
        async with ctx.typing():
            briefing = get_work_morning_briefing()
            await ctx.send(briefing)
    except Exception as e:
        print(f"❌ Work briefing command error: {e}")
        await ctx.send("💼 Work briefing unavailable. Please try again.")

@bot.command(name='work-daily')
async def work_daily_command(ctx):
    """Work daily briefing - alias for work-briefing"""
    try:
        async with ctx.typing():
            briefing = get_work_morning_briefing()
            await ctx.send(briefing)
    except Exception as e:
        print(f"❌ Work daily command error: {e}")
        await ctx.send("💼 Work daily briefing unavailable. Please try again.")

@bot.command(name='work-morning')
async def work_morning_command(ctx):
    """Work morning briefing - alias for work-briefing"""
    try:
        async with ctx.typing():
            briefing = get_work_morning_briefing()
            await ctx.send(briefing)
    except Exception as e:
        print(f"❌ Work morning command error: {e}")
        await ctx.send("💼 Work morning briefing unavailable. Please try again.")

@bot.command(name='work-schedule')
async def work_schedule_command(ctx, *, timeframe: str = "today"):
    """Flexible work schedule command"""
    try:
        async with ctx.typing():
            timeframe_lower = timeframe.lower()
            
            if any(word in timeframe_lower for word in ["today", "now", "current"]):
                response = get_work_schedule_today()
            elif any(word in timeframe_lower for word in ["tomorrow", "next"]):
                response = get_work_upcoming_events(1)
            elif any(word in timeframe_lower for word in ["week", "7"]):
                response = get_work_upcoming_events(7)
            elif any(word in timeframe_lower for word in ["month", "30"]):
                response = get_work_upcoming_events(30)
            elif timeframe_lower.isdigit():
                days = int(timeframe_lower)
                days = max(1, min(days, 30))
                response = get_work_upcoming_events(days)
            else:
                response = get_work_schedule_today()
            
            await ctx.send(response)
    except Exception as e:
        print(f"❌ Work schedule command error: {e}")
        await ctx.send("💼 Work schedule view unavailable. Please try again.")

@bot.command(name='work-agenda')
async def work_agenda_command(ctx):
    """Work agenda command"""
    try:
        async with ctx.typing():
            today_schedule = get_work_schedule_today()
            tomorrow_events = get_work_upcoming_events(1)
            
            agenda = f"📋 **Work Agenda Overview**\n\n{today_schedule}\n\n**Tomorrow:**\n{tomorrow_events}"
            
            if len(agenda) > 1900:
                agenda = agenda[:1900] + "\n\n💼 *Use `!work-today` and `!work-upcoming` for detailed views*"
            
            await ctx.send(agenda)
    except Exception as e:
        print(f"❌ Work agenda command error: {e}")
        await ctx.send("💼 Work agenda unavailable. Please try again.")

@bot.command(name='export-for-rose')
async def export_for_rose_command(ctx):
    """Export work calendar data for Rose integration"""
    try:
        async with ctx.typing():
            export_data = export_work_data_for_rose()
            
            if export_data['status'] == 'success':
                response = f"📊 **Work Data Export for Rose:**\n\n{export_data['message']}\n\n"
                
                if export_data['work_events']:
                    response += "**Sample Work Events:**\n"
                    for event in export_data['work_events'][:3]:
                        response += f"• {event['date']} at {event['time']}: {event['title']}\n"
                    
                    if len(export_data['work_events']) > 3:
                        response += f"\n*...and {len(export_data['work_events']) - 3} more events*"
                
                if export_data['pr_insights']:
                    response += "\n\n**PR Insights:**\n"
                    for insight in export_data['pr_insights'][:2]:
                        response += f"• {insight['insight']}\n"
                        
                response += f"\n\n🤝 **Rose Integration:** Data ready for executive briefing coordination"
            else:
                response = f"❌ **Export Failed:** {export_data['message']}"
            
            await ctx.send(response)
    except Exception as e:
        print(f"❌ Export for Rose command error: {e}")
        await ctx.send("💼 Export for Rose unavailable. Please try again.")

@bot.command(name='pr-research')
async def pr_research_command(ctx, *, query: str = None):
    """PR research command"""
    try:
        if not query:
            await ctx.send("💼 **PR Research Usage:** `!pr-research <your PR query>`\n\nExamples:\n• `!pr-research crisis communication strategies`\n• `!pr-research media relations best practices`")
            return
        
        async with ctx.typing():
            results, sources = await pr_research_enhanced(query, "pr communications", 3)
            
            response = f"💼 **PR Research:** {query}\n\n{results}"
            
            if sources:
                response += "\n\n📚 **PR Sources:**\n"
                for source in sources:
                    response += f"({source['number']}) {source['title']} - {source['domain']}\n"
            
            await send_long_message(ctx.message, response)
            
    except Exception as e:
        print(f"❌ PR research command error: {e}")
        await ctx.send("💼 PR research unavailable. Please try again.")

@bot.command(name='news-monitor')
async def news_monitor_command(ctx, *, query: str = None):
    """News monitoring command"""
    try:
        if not query:
            await ctx.send("📰 **News Monitor Usage:** `!news-monitor <your news query>`\n\nExamples:\n• `!news-monitor technology industry trends`\n• `!news-monitor crisis communication examples`")
            return
        
        async with ctx.typing():
            results, sources = await news_monitoring_search(query, 5)
            
            response = f"📰 **News Monitor:** {query}\n\n{results}"
            
            if sources:
                response += "\n\n📚 **News Sources:**\n"
                for source in sources:
                    response += f"({source['number']}) {source['title']} - {source['domain']}\n"
            
            await send_long_message(ctx.message, response)
            
    except Exception as e:
        print(f"❌ News monitor command error: {e}")
        await ctx.send("📰 News monitoring unavailable. Please try again.")

@bot.command(name='communications')
async def communications_command(ctx, *, topic: str = None):
    """Communications strategy insights command"""
    try:
        if not topic:
            await ctx.send("💼 **Communications Usage:** `!communications <communications topic>`\n\nExamples:\n• `!communications stakeholder engagement`\n• `!communications internal communications`")
            return
        
        async with ctx.typing():
            user_id = str(ctx.author.id)
            comms_query = f"communications strategy insights for {topic} stakeholder engagement PR"
            response = await get_vivian_response(comms_query, user_id)
            await send_long_message(ctx.message, response)
            
    except Exception as e:
        print(f"❌ Communications command error: {e}")
        await ctx.send("💼 Communications insights unavailable. Please try again.")

@bot.command(name='coordinate-with-rose')
async def coordinate_with_rose_command(ctx):
    """Coordinate with Rose command"""
    try:
        async with ctx.typing():
            user_id = str(ctx.author.id)
            coordination_query = "coordinate my work calendar with Rose for executive briefing integration"
            response = await get_vivian_response(coordination_query, user_id)
            await send_long_message(ctx.message, response)
            
    except Exception as e:
        print(f"❌ Coordinate with Rose command error: {e}")
        await ctx.send("💼 Rose coordination unavailable. Please try again.")

# ============================================================================
# ERROR HANDLING
# ============================================================================

@bot.event
async def on_command_error(ctx, error):
    """Enhanced error handling for all commands"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required information. Use `!help` for command usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument. Use `!help` for command usage.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"💼 PR office is busy. Please wait {error.retry_after:.1f} seconds.")
    else:
        print(f"❌ Command error: {error}")
        await ctx.send("❌ Command error occurred. Please try again.")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    try:
        print(f"🚀 Launching {ASSISTANT_NAME}...")
        print(f"📅 Work Calendar API: {bool(accessible_calendars)} work calendars accessible")
        print(f"🔍 PR Research: {bool(BRAVE_API_KEY)}")
        print(f"📧 Gmail Integration: {bool(gmail_service)}")
        print(f"🇨🇦 Timezone: Toronto (America/Toronto)")
        print("🎯 Starting Discord bot...")
        
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        print("\n🛑 Vivian shutdown requested")
    except Exception as e:
        print(f"❌ Critical error starting Vivian: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
    finally:
        print("💼 Vivian Spencer shutting down gracefully...")