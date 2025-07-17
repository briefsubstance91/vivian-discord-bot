#!/usr/bin/env python3
"""
VIVIAN SPENCER - DISCORD BOT (ENHANCED WORK CALENDAR INTEGRATION)
PR & Communications Specialist with Work Calendar Focus & Rose Integration
PHASES 1-4: Work Calendar + Enhanced Functions + OpenAI Integration + Rose Communication
"""

import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
import time
import re
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import traceback
from collections import defaultdict

# Load environment variables
load_dotenv()

# Vivian's PR configuration
ASSISTANT_NAME = "Vivian Spencer"
ASSISTANT_ROLE = "PR & Communications (Work Calendar Enhanced)"
ALLOWED_CHANNELS = ['social-overview', 'news-feed', 'external-communications', 'general']

# Environment variables with fallbacks
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("VIVIAN_DISCORD_TOKEN")
ASSISTANT_ID = os.getenv("VIVIAN_ASSISTANT_ID") or os.getenv("ASSISTANT_ID")
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Work Calendar integration (NEW - Phase 1)
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
BG_WORK_CALENDAR_ID = os.getenv('BG_WORK_CALENDAR_ID')  # Work calendar specific
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

# Discord setup with error handling
try:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)
except Exception as e:
    print(f"❌ CRITICAL: Discord bot initialization failed: {e}")
    exit(1)

# OpenAI setup with error handling
try:
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    print(f"❌ CRITICAL: OpenAI client initialization failed: {e}")
    exit(1)

# Work Calendar setup (ENHANCED - Phase 1)
gmail_service = None
calendar_service = None
work_calendar_accessible = False
service_account_email = None

def test_work_calendar_access():
    """Test BG work calendar access specifically"""
    global work_calendar_accessible
    
    if not calendar_service or not BG_WORK_CALENDAR_ID:
        print("⚠️ Work calendar not configured")
        return False
    
    try:
        calendar_info = calendar_service.calendars().get(calendarId=BG_WORK_CALENDAR_ID).execute()
        print(f"✅ BG Work Calendar accessible: {calendar_info.get('summary', 'Unknown')}")
        
        # Test recent events access
        now = datetime.now(pytz.UTC)
        past_24h = now - timedelta(hours=24)
        
        events_result = calendar_service.events().list(
            calendarId=BG_WORK_CALENDAR_ID,
            timeMin=past_24h.isoformat(),
            timeMax=now.isoformat(),
            maxResults=5,
            singleEvents=True
        ).execute()
        
        events = events_result.get('items', [])
        print(f"✅ BG Work Calendar events: {len(events)} found in last 24h")
        
        work_calendar_accessible = True
        return True
        
    except HttpError as e:
        error_code = e.resp.status
        print(f"❌ BG Work Calendar HTTP Error {error_code}")
        if error_code == 403:
            print("   Check if service account has access to BG work calendar")
        elif error_code == 404:
            print("   Check if BG_WORK_CALENDAR_ID is correct")
        work_calendar_accessible = False
        return False
    except Exception as e:
        print(f"❌ BG Work Calendar error: {e}")
        work_calendar_accessible = False
        return False

# Initialize Google services (ENHANCED - Phase 1)
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
        
        service_account_email = credentials_info.get('client_email')
        print(f"✅ Google services initialized")
        print(f"📧 Service Account: {service_account_email}")
        
        # Test work calendar access
        if BG_WORK_CALENDAR_ID:
            test_work_calendar_access()
        else:
            print("⚠️ BG_WORK_CALENDAR_ID not configured - work calendar features disabled")
        
    else:
        print("⚠️ Google credentials not found - calendar/email functions disabled")
        
except Exception as e:
    print(f"❌ Google services setup error: {e}")
    gmail_service = None
    calendar_service = None
    work_calendar_accessible = False

# Memory and duplicate prevention systems
user_conversations = {}
processing_messages = set()
last_response_time = {}
active_runs = {}

print(f"📱 Starting {ASSISTANT_NAME} - {ASSISTANT_ROLE}...")

# ============================================================================
# ENHANCED WORK CALENDAR FUNCTIONS (Phase 2)
# ============================================================================

def get_work_calendar_events(start_time, end_time, max_results=100):
    """Get events from BG work calendar with enhanced error handling"""
    if not calendar_service or not work_calendar_accessible:
        return []
    
    try:
        events_result = calendar_service.events().list(
            calendarId=BG_WORK_CALENDAR_ID,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        return events
        
    except Exception as e:
        print(f"❌ Error getting work calendar events: {e}")
        return []

def format_work_event(event, user_timezone=None):
    """Format a work calendar event with Toronto timezone"""
    if user_timezone is None:
        user_timezone = pytz.timezone('America/Toronto')
    
    start = event['start'].get('dateTime', event['start'].get('date'))
    title = event.get('summary', 'Untitled Meeting')
    location = event.get('location', '')
    
    # Add work context emoji
    title = f"💼 {title}"
    
    if 'T' in start:  # Has time
        try:
            utc_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
            local_time = utc_time.astimezone(user_timezone)
            time_str = local_time.strftime('%I:%M %p')
            
            if location:
                return f"• {time_str}: {title} ({location})"
            else:
                return f"• {time_str}: {title}"
        except Exception as e:
            print(f"❌ Error formatting work event: {e}")
            return f"• {title}"
    else:  # All day event
        if location:
            return f"• All Day: {title} ({location})"
        else:
            return f"• All Day: {title}"

def get_work_schedule_today():
    """Get today's work schedule for PR planning"""
    if not calendar_service or not work_calendar_accessible:
        return "📅 **Today's Work Schedule:** Work calendar integration not available\n\n💼 **PR Planning:** Review calendar manually for meeting prep and communications timing"
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        
        today_toronto = datetime.now(toronto_tz).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_toronto = today_toronto.replace(hour=23, minute=59, second=59)
        
        today_utc = today_toronto.astimezone(pytz.UTC)
        tomorrow_utc = tomorrow_toronto.astimezone(pytz.UTC)
        
        events = get_work_calendar_events(today_utc, tomorrow_utc)
        
        if not events:
            return "📅 **Today's Work Schedule:** No work meetings scheduled\n\n💼 **PR Opportunity:** Perfect day for strategic communications, content creation, and outreach"
        
        formatted_events = []
        for event in events:
            formatted = format_work_event(event, toronto_tz)
            formatted_events.append(formatted)
        
        header = f"📅 **Today's Work Schedule:** {len(events)} meetings/events"
        
        return header + "\n\n" + "\n".join(formatted_events[:10])  # Limit to 10 events
        
    except Exception as e:
        print(f"❌ Work calendar error: {e}")
        return "📅 **Today's Work Schedule:** Error retrieving work calendar data"

def export_work_calendar_for_rose():
    """Export work calendar data for Rose integration (Phase 4)"""
    if not calendar_service or not work_calendar_accessible:
        return {
            'status': 'unavailable',
            'message': 'Work calendar integration not available',
            'events': []
        }
    
    try:
        toronto_tz = pytz.timezone('America/Toronto')
        now = datetime.now(toronto_tz)
        
        # Get next 3 days of work events for Rose's briefings
        end_time = now + timedelta(days=3)
        
        events = get_work_calendar_events(now, end_time)
        
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            title = event.get('summary', 'Untitled Meeting')
            location = event.get('location', '')
            
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
                    'type': 'work_meeting'
                })
            else:
                date_obj = datetime.fromisoformat(start)
                date_str = date_obj.strftime('%A, %B %d')
                
                formatted_events.append({
                    'date': date_str,
                    'time': 'All Day',
                    'title': title,
                    'location': location,
                    'type': 'work_event'
                })
        
        return {
            'status': 'success',
            'message': f'Work calendar data for next 3 days ({len(formatted_events)} events)',
            'events': formatted_events,
            'calendar_name': 'BG Work Calendar',
            'exported_at': now.isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error exporting work calendar for Rose: {e}")
        return {
            'status': 'error',
            'message': f'Error exporting work calendar: {str(e)}',
            'events': []
        }

# ============================================================================
# DISCORD BOT COMMANDS
# ============================================================================

@bot.command(name='work-today')
async def work_today_command(ctx):
    """Today's work schedule command"""
    try:
        async with ctx.typing():
            schedule = get_work_schedule_today()
            await ctx.send(schedule)
    except Exception as e:
        print(f"❌ Work today command error: {e}")
        await ctx.send("❌ Error retrieving today's work schedule.")

@bot.command(name='export-for-rose')
async def export_for_rose_command(ctx):
    """Export work calendar data for Rose integration"""
    try:
        async with ctx.typing():
            export_data = export_work_calendar_for_rose()
            
            if export_data['status'] == 'success':
                response = f"📅 **Work Calendar Export for Rose:**\n\n{export_data['message']}\n\n"
                
                if export_data['events']:
                    response += "**Sample Events:**\n"
                    for event in export_data['events'][:3]:  # Show first 3 events
                        response += f"• {event['date']} at {event['time']}: {event['title']}\n"
                    
                    if len(export_data['events']) > 3:
                        response += f"\n*...and {len(export_data['events']) - 3} more events*"
                else:
                    response += "No work events found for next 3 days."
                    
                response += f"\n\n🤝 **Rose Integration:** Data ready for executive briefing"
            else:
                response = f"❌ **Export Failed:** {export_data['message']}"
            
            await ctx.send(response)
    except Exception as e:
        print(f"❌ Export for Rose command error: {e}")
        await ctx.send("❌ Error exporting work calendar for Rose.")

@bot.command(name='status')
async def status_command(ctx):
    """Executive system status with comprehensive diagnostics"""
    try:
        embed = discord.Embed(
            title="👑 Rose Ashcombe - Executive Assistant (Complete Enhanced)",
            description="Executive Calendar & Task Management with Google Integration",
            color=0xd4af37  # Gold color for executive
        )
        
        # Core Systems Section
        core_systems = []
        core_systems.append(f"• OpenAI Assistant: {'✅ Connected' if ASSISTANT_ID else '❌ Not configured'}")
        core_systems.append(f"• Discord: ✅ Connected as {bot.user.name if bot.user else 'Unknown'}")
        
        if service_account_email:
            core_systems.append(f"• Service Account: ✅ {service_account_email}")
        else:
            core_systems.append("• Service Account: ❌ Not configured")
            
        embed.add_field(
            name="🤖 Core Systems:",
            value="
".join(core_systems),
            inline=False
        )
        
        # Calendar Integration
        calendar_status = "❌ No calendars accessible"
        if accessible_calendars:
            calendar_names = [name for name, _, _ in accessible_calendars]
            calendar_status = f"✅ {len(accessible_calendars)} calendars: {', '.join(calendar_names)}"
        
        embed.add_field(
            name="📅 Calendar Integration:",
            value=f"{calendar_status}
🇨🇦 Timezone: Toronto (America/Toronto)",
            inline=False
        )
        
        # Executive Features
        exec_features = [
            "• Complete calendar management & scheduling",
            "• Executive briefings & strategic planning", 
            "• Task coordination across calendars",
            "• Meeting preparation & follow-up",
            "• Free time optimization",
            "• Strategic research & productivity insights"
        ]
        embed.add_field(
            name="💼 Executive Features:",
            value="
".join(exec_features),
            inline=False
        )
        
        # Specialties
        specialties = [
            "👑 Executive Planning",
            "📊 Strategic Analysis", 
            "📅 Calendar Mastery",
            "🎯 Productivity Optimization",
            "💼 Meeting Management",
            "📋 Task Coordination"
        ]
        embed.add_field(
            name="🎯 Specialties:",
            value=" • ".join(specialties),
            inline=False
        )
        
        # Performance Metrics
        embed.add_field(
            name="⚡ Performance:",
            value=f"👥 Active conversations: {len(user_conversations)}
🏢 Allowed channels: {', '.join(ALLOWED_CHANNELS)}
📊 Processing: {len(processing_messages)} messages",
            inline=False
        )
        
        # Research Status
        research_status = "✅ Enabled" if BRAVE_API_KEY else "❌ Disabled"
        embed.add_field(
            name="🔍 Planning Research:",
            value=f"Brave Search API: {research_status}",
            inline=True
        )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Status command error: {e}")
        # Fallback to simple message
        await ctx.send("👑 Rose Ashcombe - Executive Assistant ready for strategic planning!")

