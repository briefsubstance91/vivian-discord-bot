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
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.auth.transport.requests import Request
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

# Vivian configuration for Universal Status System
VIVIAN_CONFIG = {
    "name": "Vivian Spencer",
    "role": "PR & Communications Specialist",
    "description": "Strategic communications expert with work calendar integration, PR research, and Rose coordination capabilities",
    "emoji": "💼",
    "color": 0x0F4C75,  # Sapphire blue for PR/Communications
    "specialties": [
        "💼 PR Strategy & Communications",
        "📅 Work Calendar Integration", 
        "📊 Media Relations & Research",
        "🎯 Stakeholder Management",
        "🤝 Rose Executive Coordination"
    ],
    "capabilities": [
        "Work-focused calendar coordination with PR context",
        "Strategic PR research and news monitoring",
        "Communications planning and stakeholder messaging",
        "Meeting preparation and media intelligence",
        "Rose integration for comprehensive executive assistance"
    ],
    "example_requests": [
        "@Vivian give me my work briefing with PR context",
        "@Vivian research crisis communication strategies",
        "@Vivian what's on my work calendar today?",
        "@Vivian monitor news about our industry",
        "@Vivian export my work data for Rose",
        "@Vivian help me prepare for today's stakeholder meeting"
    ],
    "commands": [
        "!work-briefing - Work morning briefing with PR context",
        "!work-today - Today's work schedule",
        "!work-upcoming [days] - Upcoming work events (default: 7)",
        "!work-schedule [timeframe] - Flexible work schedule view",
        "!pr-research <query> - Strategic PR research",
        "!news-monitor <query> - News monitoring and analysis",
        "!communications <topic> - Communications strategy insights",
        "!export-for-rose - Export work data for Rose coordination",
        "!status - Show system status",
        "!ping - Test connectivity",
        "!help - Show this help message"
    ],
    "channels": ['social-overview', 'news-feed', 'external-communications', 'project-overview', 'work-inbox', 'meeting-notes', 'general']
}

# Constants for reducing redundant messaging
CALENDAR_UNAVAILABLE_MSG = "Work calendar integration not available"

ASSISTANT_CONFIG = VIVIAN_CONFIG

# Environment variables with fallbacks
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("VIVIAN_DISCORD_TOKEN")
ASSISTANT_ID = os.getenv("VIVIAN_ASSISTANT_ID") or os.getenv("ASSISTANT_ID")
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Work Calendar integration (OAuth2 like Rose)
GMAIL_TOKEN_JSON = os.getenv('GMAIL_TOKEN_JSON')
GMAIL_WORK_CALENDAR_ID = os.getenv('GMAIL_WORK_CALENDAR_ID')  # Work calendar only

# OAuth scopes (same as Rose to avoid token refresh issues)
CALENDAR_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar'
]

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

# Google Calendar setup (OAuth2 like Rose, calendar only)
calendar_service = None
accessible_calendars = []

def initialize_google_services():
    """Initialize Google Calendar service using OAuth2 credentials (work calendar only)"""
    global calendar_service, accessible_calendars
    
    print("🔧 Initializing Google Calendar with OAuth2...")
    
    if not GMAIL_TOKEN_JSON:
        print("❌ No OAuth token found - Calendar service disabled")
        print("   Use Rose's OAuth token (GMAIL_TOKEN_JSON)")
        return False
    
    try:
        # Parse OAuth token (same as Rose)
        token_info = json.loads(GMAIL_TOKEN_JSON)
        
        # Create OAuth credentials for calendar only
        oauth_credentials = OAuthCredentials.from_authorized_user_info(
            token_info, CALENDAR_SCOPES
        )
        
        if not oauth_credentials:
            print("❌ Failed to create OAuth credentials")
            return False
        
        # Handle token refresh if needed
        if oauth_credentials.expired and oauth_credentials.refresh_token:
            try:
                print("🔄 Refreshing OAuth token...")
                oauth_credentials.refresh(Request())
                print("✅ OAuth token refreshed successfully")
            except Exception as refresh_error:
                print(f"❌ Token refresh failed: {refresh_error}")
                print("ℹ️  This is likely because the token was created with different scopes")
                print("ℹ️  Continuing with existing token (may still work)...")
                # Don't return False - try to continue with existing token
        
        # Check if credentials are valid (even if refresh failed)
        if not oauth_credentials.valid:
            if oauth_credentials.expired:
                print("❌ OAuth credentials are expired and refresh failed")
                print("ℹ️  You may need to re-authorize Rose's OAuth token")
            else:
                print("❌ OAuth credentials are invalid")
            return False
        
        # Initialize calendar service only
        calendar_service = build('calendar', 'v3', credentials=oauth_credentials)
        print("✅ OAuth Calendar service initialized")
        
        # Test work calendar access only
        test_work_calendar_access()
        
        return True
        
    except json.JSONDecodeError:
        print("❌ Invalid JSON in GMAIL_TOKEN_JSON")
        return False
    except Exception as e:
        print(f"❌ Google Calendar initialization error: {e}")
        return False

def test_work_calendar_access():
    """Test access to work calendar only"""
    global accessible_calendars
    
    if not calendar_service:
        return
    
    accessible_calendars = []
    
    if not GMAIL_WORK_CALENDAR_ID:
        print("⚠️ 💼 Work Calendar: No calendar ID configured (GMAIL_WORK_CALENDAR_ID)")
        return
        
    try:
        # Test work calendar access
        calendar_info = calendar_service.calendars().get(calendarId=GMAIL_WORK_CALENDAR_ID).execute()
        accessible_calendars.append(("💼 Work Calendar", GMAIL_WORK_CALENDAR_ID))
        print(f"✅ 💼 Work Calendar accessible: {calendar_info.get('summary', 'Work Calendar')}")
        
    except HttpError as e:
        if e.resp.status == 404:
            print(f"❌ 💼 Work Calendar: Calendar not found (404)")
        elif e.resp.status == 403:
            print(f"❌ 💼 Work Calendar: Access forbidden (403)")
        else:
            print(f"❌ 💼 Work Calendar: HTTP error {e.resp.status}")
    except Exception as e:
        print(f"❌ 💼 Work Calendar: Error testing access - {e}")
    
    print(f"📅 Work calendar accessible: {'✅ Yes' if accessible_calendars else '❌ No'}")

# Initialize Google services on startup
initialize_google_services()

# Memory and duplicate prevention systems
user_conversations = {}
processing_messages = set()
last_response_time = {}

print(f"💼 Starting {ASSISTANT_NAME} - {ASSISTANT_ROLE}...")

# ============================================================================
# WORK CALENDAR FUNCTIONS (Vivian's Specialty)
# ============================================================================

def get_work_calendar_events(start_time, end_time, max_results=100):
    """Get work calendar events with enhanced error handling"""
    if not calendar_service or not accessible_calendars:
        return []
    
    try:
        # Use the work calendar ID from accessible_calendars
        calendar_name, calendar_id = accessible_calendars[0]  # Only one work calendar
        
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
        print(f"❌ Error getting work events: {e}")
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
        return f"📅 **Today's Work Schedule:** {CALENDAR_UNAVAILABLE_MSG}\n\n💼 **PR Focus:** Review calendar manually for meeting prep and stakeholder communications"
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        
        today_toronto = datetime.now(toronto_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_toronto = today_toronto.replace(hour=23, minute=59, second=59)
        
        today_utc = today_toronto.astimezone(pytz.UTC)
        tomorrow_utc = tomorrow_toronto.astimezone(pytz.UTC)
        
        # Get events from work calendar only
        events = get_work_calendar_events(today_utc, tomorrow_utc)
        
        if not events:
            return "📅 **Today's Work Schedule:** No work meetings scheduled\n\n💼 **PR Opportunity:** Perfect day for strategic communications, content creation, and stakeholder outreach"
        
        # Format events
        formatted_events = []
        for event in events:
            formatted = format_work_event(event, toronto_tz)
            formatted_events.append(formatted)
        
        # Sort by time
        def get_event_time(event):
            start = event['start'].get('dateTime', event['start'].get('date'))
            try:
                if 'T' in start:
                    utc_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    return utc_time.astimezone(toronto_tz)
                else:
                    return datetime.fromisoformat(start)
            except:
                return datetime.now(toronto_tz)
        
        events.sort(key=get_event_time)
        formatted_events = [format_work_event(event, toronto_tz) for event in events]
        
        header = f"📅 **Today's Work Schedule:** {len(events)} meetings/events"
        
        return header + "\n\n" + "\n".join(formatted_events[:15])
        
    except Exception as e:
        print(f"❌ Work calendar error: {e}")
        return "📅 **Today's Work Schedule:** Error retrieving work calendar data"

def get_work_upcoming_events(days=7):
    """Get upcoming work events with PR planning context"""
    if not calendar_service or not accessible_calendars:
        return f"📅 **Upcoming Work Events ({days} days):** {CALENDAR_UNAVAILABLE_MSG}"
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        
        start_toronto = datetime.now(toronto_tz)
        end_toronto = start_toronto + timedelta(days=days)
        
        start_utc = start_toronto.astimezone(pytz.UTC)
        end_utc = end_toronto.astimezone(pytz.UTC)
        
        # Get events from work calendar only
        events = get_work_calendar_events(start_utc, end_utc)
        
        if not events:
            return f"📅 **Upcoming Work Events ({days} days):** No work meetings scheduled\n\n💼 **PR Strategy:** Clear calendar for strategic planning and stakeholder engagement"
        
        events_by_date = defaultdict(list)
        
        for event in events:
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
        total_events = len(events)
        
        for date, day_events in list(events_by_date.items())[:7]:
            formatted.append(f"**{date}**")
            formatted.extend(day_events[:6])
        
        header = f"📅 **Upcoming Work Events ({days} days):** {total_events} total"
        
        return header + "\n\n" + "\n".join(formatted)
        
    except Exception as e:
        print(f"❌ Work calendar error: {e}")
        return f"📅 **Upcoming Work Events ({days} days):** Error retrieving work calendar data"

def get_work_morning_briefing():
    """Work-focused morning briefing with PR intelligence - includes weekend mode"""
    toronto_tz = pytz.timezone('America/Toronto')
    current_day = datetime.now(toronto_tz).weekday()
    is_weekend = current_day >= 5  # Saturday=5, Sunday=6
    current_time = datetime.now(toronto_tz).strftime('%A, %B %d')
    
    # Weekend mode - focus on personal time instead of work
    if is_weekend:
        if not calendar_service or not accessible_calendars:
            return f"📺 **Vivian's Weekend Brief - {current_time}**\n\n✨ **Weekend Mode:** Work coordination paused for personal time\n\n📅 **Personal Calendar:** Calendar integration not available\n\n💡 **Weekend Wisdom:** This is your time for rest, creativity, and personal fulfillment. Work coordination resumes Monday!"
        
        try:
            # Get any weekend events (might be personal)
            today_toronto = datetime.now(toronto_tz).replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_toronto = today_toronto.replace(hour=23, minute=59, second=59)
            
            today_utc = today_toronto.astimezone(pytz.UTC)
            tomorrow_utc = tomorrow_toronto.astimezone(pytz.UTC)
            
            weekend_events = get_work_calendar_events(today_utc, tomorrow_utc)
            
            weekend_schedule = ""
            if weekend_events:
                formatted_events = []
                for event in weekend_events[:3]:
                    # Format without work context for weekends
                    title = event.get('summary', 'Untitled Event')
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    
                    if 'T' in start:
                        utc_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        local_time = utc_time.astimezone(toronto_tz)
                        time_str = local_time.strftime('%I:%M %p')
                        formatted_events.append(f"• {time_str}: 🌿 {title}")
                    else:
                        formatted_events.append(f"• All Day: 🌿 {title}")
                
                weekend_schedule = "📅 **Today's Personal Schedule:**\n" + "\n".join(formatted_events)
            else:
                weekend_schedule = "📅 **Today's Personal Schedule:** No events scheduled - perfect for relaxation!"
            
            briefing = f"📺 **Vivian's Weekend Coordination - {current_time}**\n\n"
            briefing += "Good morning! Weekend personal coordination and leisure planning:\n\n"
            briefing += f"{weekend_schedule}\n\n"
            briefing += "✨ **Weekend Priorities:**\n"
            briefing += "• Rest and recharge for the week ahead\n"
            briefing += "• Personal projects and creative pursuits\n" 
            briefing += "• Quality time with family and friends\n"
            briefing += "• Self-care and wellness activities\n\n"
            briefing += "💡 **Weekend Wisdom:** This is your time for rest, creativity, and personal fulfillment. Work coordination resumes Monday!"
            
            return briefing
            
        except Exception as e:
            print(f"❌ Weekend briefing error: {e}")
            return f"📺 **Vivian's Weekend Brief - {current_time}**\n\n✨ **Weekend Mode:** Work coordination paused for personal time\n\n❌ **Error:** Unable to load personal schedule\n\n💡 **Weekend Wisdom:** This is your time for rest, creativity, and personal fulfillment. Work coordination resumes Monday!"
    
    # Weekday mode - regular work focus
    if not calendar_service or not accessible_calendars:
        return f"🌅 **Work Morning Briefing:** {CALENDAR_UNAVAILABLE_MSG}"
    
    try:
        today_schedule = get_work_schedule_today()
        
        # Get tomorrow's work events
        today_toronto = datetime.now(toronto_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_toronto = today_toronto + timedelta(days=1)
        day_after_toronto = tomorrow_toronto + timedelta(days=1)
        
        tomorrow_utc = tomorrow_toronto.astimezone(pytz.UTC)
        day_after_utc = day_after_toronto.astimezone(pytz.UTC)
        
        # Get tomorrow's work events from work calendar only
        tomorrow_events = get_work_calendar_events(tomorrow_utc, day_after_utc)
        
        if tomorrow_events:
            tomorrow_formatted = []
            for event in tomorrow_events[:4]:
                formatted = format_work_event(event, toronto_tz)
                tomorrow_formatted.append(formatted)
            tomorrow_preview = "📅 **Tomorrow's Work Preview:**\n" + "\n".join(tomorrow_formatted)
        else:
            tomorrow_preview = "📅 **Tomorrow's Work Preview:** Clear schedule - strategic PR planning opportunity"
        
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
            'message': CALENDAR_UNAVAILABLE_MSG,
            'work_events': [],
            'pr_insights': []
        }
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        now = datetime.now(toronto_tz)
        
        # Get next 7 days of work events for Rose
        end_time = now + timedelta(days=7)
        
        # Get events from work calendar only
        events = get_work_calendar_events(now, end_time)
        
        formatted_events = []
        pr_insights = []
        
        for event in events:
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
                    'calendar': '💼 Work Calendar'
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
    """Bot startup sequence"""
    print(f"🚀 Starting {ASSISTANT_NAME}...")
    
    # PR Research API test
    if BRAVE_API_KEY:
        print("🔧 PR Research API Configuration Status:")
        print(f" API Key: ✅ Configured")
        print(f" Search Functionality: ✅ PR Research & News Monitoring Ready")
    
    # Initialize Google services (call again in case of startup timing issues)
    initialize_google_services()
    
    # Final status
    print(f"📅 Work Calendar Service: {'✅ Ready' if accessible_calendars else '❌ Not available'}")
    print(f"✅ {ASSISTANT_NAME} is online!")
    print(f"🤖 Connected as {bot.user.name}#{bot.user.discriminator} (ID: {bot.user.id})")
    print(f"📅 Work Calendar Status: {'✅ Integrated' if accessible_calendars else '❌ Disabled'}")
    print(f"🔍 PR Research: {'✅ Available' if BRAVE_API_KEY else '⚠️ Limited'}")
    print(f"🎯 Allowed Channels: {', '.join(ALLOWED_CHANNELS)}")
    
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="💼 PR Strategy & Work Calendar"
        )
    )

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
        
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        # Check if bot is mentioned and in allowed channel (matching Rose's pattern)
        if bot.user.mentioned_in(message) and (is_dm or message.channel.name in ALLOWED_CHANNELS):
            
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
    try:
        latency = round(bot.latency * 1000)
        await ctx.send(f"💼 Pong! PR response time: {latency}ms")
    except Exception as e:
        print(f"❌ Ping command error: {e}")
        await ctx.send("💼 PR ping experiencing issues.")

@bot.command(name='help')
async def help_command(ctx):
    """Enhanced help command with Discord embeds"""
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
    try:
        config = ASSISTANT_CONFIG
        
        embed = discord.Embed(
            title=f"{config['emoji']} {config['name']} - PR & Communications Commands",
            description=config['description'],
            color=config['color']
        )
        
        # Main usage
        embed.add_field(
            name="💬 AI Assistant",
            value=f"• Mention @{config['name']} for advanced PR assistance\n• Work calendar management with communications context\n• Strategic PR research and stakeholder coordination",
            inline=False
        )
        
        # Commands - Split into sections for better organization
        calendar_commands = [
            "!work-briefing - Work morning briefing with PR context",
            "!work-today - Today's work schedule", 
            "!work-upcoming [days] - Upcoming work events (default: 7)",
            "!work-schedule [timeframe] - Flexible work schedule view",
            "!work-agenda - Comprehensive work agenda overview"
        ]
        
        pr_commands = [
            "!pr-research <query> - Strategic PR research",
            "!news-monitor <query> - News monitoring and analysis",
            "!communications <topic> - Communications strategy insights"
        ]
        
        integration_commands = [
            "!export-for-rose - Export work data for Rose coordination",
            "!coordinate-with-rose - Coordinate scheduling with Rose"
        ]
        
        system_commands = [
            "!status - System status",
            "!ping - Test response time",
            "!help - This message"
        ]
        
        embed.add_field(
            name="📅 Work Calendar & Scheduling",
            value="\n".join([f"• {cmd}" for cmd in calendar_commands]),
            inline=False
        )
        
        embed.add_field(
            name="🔍 PR & Communications Research",
            value="\n".join([f"• {cmd}" for cmd in pr_commands]),
            inline=False
        )
        
        embed.add_field(
            name="🤝 Rose Integration",
            value="\n".join([f"• {cmd}" for cmd in integration_commands]),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ System",
            value="\n".join([f"• {cmd}" for cmd in system_commands]),
            inline=False
        )
        
        # Example requests
        embed.add_field(
            name="💡 Example AI Requests",
            value="\n".join([f"• {req}" for req in config['example_requests'][:3]]),
            inline=False
        )
        
        # Channels
        embed.add_field(
            name="🎯 Active Channels",
            value=", ".join([f"#{ch}" for ch in config['channels']]),
            inline=False
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Help command error: {e}")
        await ctx.send("💼 Help system needs calibration. Please try again.")

@bot.command(name='status')
async def status_command(ctx):
    """PR system status with comprehensive diagnostics using Discord embeds"""
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
    try:
        config = ASSISTANT_CONFIG
        
        embed = discord.Embed(
            title=f"{config['emoji']} {config['name']} - System Status",
            description=config['description'],
            color=config['color']
        )
        
        # Core Systems
        assistant_status = "✅ Connected" if ASSISTANT_ID else "❌ Not configured"
        embed.add_field(
            name="🤖 Core Systems",
            value=f"✅ Discord Connected\n{assistant_status} OpenAI Assistant\n{'✅' if BRAVE_API_KEY else '❌'} PR Research API",
            inline=True
        )
        
        # Work Calendar Integration
        calendar_status = '✅' if accessible_calendars else '❌'
        embed.add_field(
            name="📅 Work Calendar Integration",
            value=f"{calendar_status} Calendar Service\n{'✅' if GMAIL_WORK_CALENDAR_ID else '❌'} Work Calendar ID\n💼 Work Calendar Focus Only",
            inline=True
        )
        
        # External APIs
        search_status = '✅' if BRAVE_API_KEY else '❌'
        embed.add_field(
            name="🔍 External APIs", 
            value=f"{search_status} Brave Search\n{search_status} News Monitoring\n🌐 PR Research Ready",
            inline=True
        )
        
        # Specialties
        embed.add_field(
            name="🎯 PR Specialties",
            value="\n".join([f"• {spec}" for spec in config['specialties']]),
            inline=False
        )
        
        # Performance & Usage
        embed.add_field(
            name="💼 PR Performance",
            value=f"• Active conversations: {len(user_conversations)}\n• Rose Integration: {'✅ Available' if accessible_calendars else '❌ Limited'}\n• Work Calendar Focus: 🇨🇦 Toronto timezone",
            inline=True
        )
        
        # Usage
        embed.add_field(
            name="💡 Usage",
            value=f"• Mention @{config['name']} for PR assistance\n• Use commands for quick work calendar functions\n• Active in: {', '.join([f'#{ch}' for ch in config['channels'][:3]])}{'...' if len(config['channels']) > 3 else ''}",
            inline=True
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Status command error: {e}")
        await ctx.send("💼 Status diagnostics experiencing issues. Please try again.")

@bot.command(name='work-today')
async def work_today_command(ctx):
    """Today's work schedule command"""
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
    if ctx.channel.name not in ALLOWED_CHANNELS:
        return
    
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
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ CRITICAL: Bot failed to start: {e}")
        exit(1)