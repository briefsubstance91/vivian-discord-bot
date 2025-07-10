#!/usr/bin/env python3
"""
VIVIAN SPENCER - DISCORD BOT (CRASH FIX)
PR & Communications Specialist with Enhanced Error Handling, Gmail & Calendar Integration
FIXED: Critical crash issues with error handling, async operations, and resource management
Based on proven Flora safety patterns
"""

import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import json
import time
import re
import base64
import pytz
from datetime import datetime, timedelta
from dotenv import load_dotenv
from openai import OpenAI
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import traceback

# Load environment variables
load_dotenv()

# Vivian's PR configuration
ASSISTANT_NAME = "Vivian Spencer"
ASSISTANT_ROLE = "PR & Communications (Crash Fixed)"
ALLOWED_CHANNELS = ['social-overview', 'news-feed', 'external-communications', 'general']

# Environment variables with fallbacks
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("VIVIAN_DISCORD_TOKEN")
ASSISTANT_ID = os.getenv("VIVIAN_ASSISTANT_ID") or os.getenv("ASSISTANT_ID")
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Gmail and Calendar integration variables
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
GMAIL_ADDRESS = os.getenv('GMAIL_ADDRESS')
GOOGLE_CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')

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

# Google Services setup with error handling
gmail_service = None
calendar_service = None
try:
    if GOOGLE_SERVICE_ACCOUNT_JSON:
        credentials_info = json.loads(GOOGLE_SERVICE_ACCOUNT_JSON)
        credentials = service_account.Credentials.from_service_account_info(credentials_info)
        gmail_service = build('gmail', 'v1', credentials=credentials)
        calendar_service = build('calendar', 'v3', credentials=credentials)
        print("✅ Google Gmail & Calendar services connected successfully")
    else:
        print("⚠️ Google credentials not found - Gmail/Calendar functions disabled")
except Exception as e:
    print(f"❌ Google services setup error: {e}")
    gmail_service = None
    calendar_service = None

# Memory and duplicate prevention systems
user_conversations = {}
processing_messages = set()
last_response_time = {}
active_runs = {}

print(f"📱 Starting {ASSISTANT_NAME} - {ASSISTANT_ROLE}...")

# ============================================================================
# ENHANCED PR SEARCH WITH ERROR HANDLING
# ============================================================================

async def pr_search_enhanced(query, search_type="general", num_results=3):
    """Enhanced PR and communications research with comprehensive error handling"""
    if not BRAVE_API_KEY:
        print("⚠️ Brave Search API key not configured")
        return "🔍 PR research requires Brave Search API configuration"
    
    try:
        # Enhance query for PR content
        if search_type == "trends":
            pr_query = f"{query} PR trends communications marketing 2025"
        elif search_type == "crisis":
            pr_query = f"{query} crisis communication PR management strategy"
        elif search_type == "social":
            pr_query = f"{query} social media strategy PR communications"
        else:
            pr_query = f"{query} PR communications strategy marketing"
        
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
            try:
                async with session.get(
                    'https://api.search.brave.com/res/v1/web/search',
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'web' not in data or 'results' not in data['web']:
                            return "🔍 No PR search results found"
                        
                        results = data['web']['results'][:num_results]
                        
                        if not results:
                            return "🔍 No PR search results found"
                        
                        formatted = []
                        
                        for i, result in enumerate(results, 1):
                            title = result.get('title', 'Unknown Source')[:80]
                            snippet = result.get('description', 'No description available')[:150]
                            url_link = result.get('url', '')
                            
                            if url_link and len(url_link) > 10:
                                formatted.append(f"📰 **{title}**\n{snippet}\n🔗 {url_link}")
                        
                        return "\n\n".join(formatted)
                    else:
                        print(f"❌ Brave Search API error: Status {response.status}")
                        return f"🔍 PR search error (status {response.status})"
                        
            except asyncio.TimeoutError:
                print("❌ PR search timeout")
                return "🔍 PR search timed out"
            except aiohttp.ClientError as e:
                print(f"❌ HTTP client error: {e}")
                return f"🔍 PR search connection error"
                    
    except Exception as e:
        print(f"❌ PR search error: {e}")
        print(f"📋 Traceback: {traceback.format_exc()}")
        return f"🔍 PR search error: Please try again"

# ============================================================================
# GMAIL FUNCTIONS WITH ERROR HANDLING
# ============================================================================

def search_gmail_messages(query, max_results=5):
    """Search Gmail messages with error handling"""
    if not gmail_service or not GMAIL_ADDRESS:
        return "📧 **Email Search:** Gmail integration not configured\n\n💼 **PR Tip:** Set up Gmail integration for communications management"
    
    try:
        results = gmail_service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return f"📧 **Email Search:** No emails found for '{query}'\n\n💼 **Strategy:** Consider broader search terms or date ranges"
        
        formatted_emails = []
        for i, message in enumerate(messages[:max_results], 1):
            try:
                msg = gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata'
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
                
                formatted_emails.append(f"**{i}.** {subject}\n   From: {sender[:50]}...\n   Date: {date[:20]}")
                
            except Exception as e:
                formatted_emails.append(f"**{i}.** Error retrieving email details")
        
        return f"📧 **Email Search:** '{query}' ({len(messages)} results)\n\n" + "\n\n".join(formatted_emails)
        
    except Exception as e:
        print(f"❌ Gmail search error: {e}")
        return f"📧 **Email Search:** Error searching emails for '{query}'"

def get_recent_emails(max_results=10):
    """Get recent emails with error handling"""
    if not gmail_service:
        return "📧 **Recent Emails:** Gmail integration not configured\n\n💼 **Communications Tip:** Enable Gmail for email management and PR coordination"
    
    try:
        results = gmail_service.users().messages().list(
            userId='me',
            maxResults=max_results
        ).execute()
        
        messages = results.get('messages', [])
        
        if not messages:
            return "📧 **Recent Emails:** No recent emails found"
        
        formatted_emails = []
        for i, message in enumerate(messages[:5], 1):  # Limit to 5 for Discord
            try:
                msg = gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='metadata'
                ).execute()
                
                headers = msg['payload'].get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
                
                formatted_emails.append(f"• {subject}\n  From: {sender[:40]}...")
                
            except Exception as e:
                formatted_emails.append(f"• Error retrieving email {i}")
        
        return f"📧 **Recent Emails:** Latest {len(messages)} messages\n\n" + "\n".join(formatted_emails)
        
    except Exception as e:
        print(f"❌ Recent emails error: {e}")
        return "📧 **Recent Emails:** Error retrieving recent emails"

# ============================================================================
# CALENDAR FUNCTIONS WITH ERROR HANDLING
# ============================================================================

def get_today_schedule():
    """Get today's calendar schedule with error handling"""
    if not calendar_service or not GOOGLE_CALENDAR_ID:
        return "📅 **Today's Schedule:** Calendar integration not configured\n\n💼 **PR Planning:** Manual schedule review recommended for communications timing"
    
    try:
        # Get today's date range in UTC
        today = datetime.now(pytz.UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today.replace(hour=23, minute=59, second=59)
        
        events_result = calendar_service.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=today.isoformat(),
            timeMax=tomorrow.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return "📅 **Today's Schedule:** No scheduled events\n\n💼 **PR Opportunity:** Perfect day for strategic communications planning and content creation"
        
        formatted_events = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            title = event.get('summary', 'Untitled Event')
            
            if 'T' in start:  # Has time
                time_str = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%I:%M %p')
                formatted_events.append(f"• {time_str}: {title}")
            else:  # All day event
                formatted_events.append(f"• All Day: {title}")
        
        return f"📅 **Today's PR Schedule:** {len(events)} events\n\n" + "\n".join(formatted_events)
        
    except Exception as e:
        print(f"❌ Calendar error: {e}")
        return "📅 **Today's Schedule:** Error retrieving calendar data"

def get_upcoming_events(days=7):
    """Get upcoming events with error handling"""
    if not calendar_service or not GOOGLE_CALENDAR_ID:
        return f"📅 **Upcoming {days} Days:** Calendar integration not configured\n\n💼 **PR Planning:** Manual weekly communications planning recommended"
    
    try:
        start_time = datetime.now(pytz.UTC)
        end_time = start_time + timedelta(days=days)
        
        events_result = calendar_service.events().list(
            calendarId=GOOGLE_CALENDAR_ID,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        events = events_result.get('items', [])
        
        if not events:
            return f"📅 **Upcoming {days} Days:** No scheduled events\n\n💼 **Strategic Opportunity:** Focus on proactive PR planning and relationship building"
        
        # Group by date
        from collections import defaultdict
        events_by_date = defaultdict(list)
        
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            title = event.get('summary', 'Untitled Event')
            
            if 'T' in start:
                date_obj = datetime.fromisoformat(start.replace('Z', '+00:00'))
                date_str = date_obj.strftime('%a %m/%d')
                time_str = date_obj.strftime('%I:%M %p')
                events_by_date[date_str].append(f"  • {time_str}: {title}")
            else:
                date_obj = datetime.fromisoformat(start)
                date_str = date_obj.strftime('%a %m/%d')
                events_by_date[date_str].append(f"  • All Day: {title}")
        
        formatted = []
        for date, day_events in list(events_by_date.items())[:7]:  # Limit to 7 days
            formatted.append(f"**{date}**")
            formatted.extend(day_events[:5])  # Limit events per day
        
        return f"📅 **Upcoming {days} Days:** {len(events)} total events\n\n" + "\n".join(formatted)
        
    except Exception as e:
        print(f"❌ Calendar error: {e}")
        return f"📅 **Upcoming {days} Days:** Error retrieving calendar data"

# ============================================================================
# VIVIAN'S OPENAI INTEGRATION WITH COMPREHENSIVE ERROR HANDLING
# ============================================================================

def get_user_thread(user_id):
    """Get or create thread for user with error handling"""
    try:
        if user_id not in user_conversations:
            thread = client.beta.threads.create()
            user_conversations[user_id] = thread.id
            print(f"📱 Created PR thread for user {user_id}")
        return user_conversations[user_id]
    except Exception as e:
        print(f"❌ Error creating thread: {e}")
        return None

async def get_vivian_response(message, user_id):
    """Get response from Vivian's enhanced OpenAI assistant with comprehensive error handling"""
    try:
        if not ASSISTANT_ID:
            return "⚠️ Vivian not configured - check VIVIAN_ASSISTANT_ID environment variable"
        
        # Check if user already has an active run
        if user_id in active_runs:
            return "📱 Vivian is currently analyzing PR strategy. Please wait a moment..."
        
        # Mark user as having active run
        active_runs[user_id] = True
        
        # Get user's thread
        thread_id = get_user_thread(user_id)
        if not thread_id:
            return "❌ Error creating PR connection. Please try again."
        
        # Clean message
        clean_message = message.replace(f'<@{bot.user.id}>', '').strip() if hasattr(bot, 'user') and bot.user else message.strip()
        
        # Enhanced message with PR focus
        enhanced_message = f"""USER PR REQUEST: {clean_message}

RESPONSE GUIDELINES:
- Use professional PR-focused Discord formatting with strategic headers
- Provide strategic communications insights and actionable recommendations
- Apply PR specialist tone: strategic, professional, trend-aware
- Keep main content under 1200 characters for Discord efficiency
- Use headers like: 📱 **PR Strategy:** or 📰 **Market Intelligence:**
- IMPORTANT: Always provide strategic communications context and actionable next steps"""
        
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
                    return "📱 PR office is busy. Please try again in a moment."
            else:
                print(f"❌ Message creation error: {e}")
                return "❌ Error creating PR message. Please try again."
        
        # Run assistant with PR instructions
        try:
            run = client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=ASSISTANT_ID,
                instructions="""You are Vivian Spencer, PR and communications specialist with enhanced research and coordination capabilities.

PR APPROACH:
- Provide strategic PR thinking with data-driven insights
- Apply professional communications perspective with trend awareness
- Include actionable recommendations with clear timelines
- Focus on crisis-ready thinking and reputation management

FORMATTING: Use professional PR formatting with strategic headers (📱 📰 📧 📅 💼) and provide organized, action-oriented guidance.

STRUCTURE:
📱 **PR Strategy:** [strategic overview with market insights]
📰 **Market Intelligence:** [research-backed recommendations]
💼 **Action Items:** [specific next steps with communications timing]

Keep core content focused and always provide strategic communications context."""
            )
        except Exception as e:
            print(f"❌ Run creation error: {e}")
            return "❌ Error starting PR analysis. Please try again."
        
        print(f"📱 Vivian run created: {run.id}")
        
        # Wait for completion with function handling
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
            elif run_status.status in ["failed", "cancelled", "expired"]:
                print(f"❌ Run {run_status.status}")
                return "❌ PR analysis interrupted. Please try again with a different request."
            
            await asyncio.sleep(2)
        else:
            print("⏱️ Run timed out")
            return "⏱️ PR office is busy analyzing complex strategies. Please try again in a moment."
        
        # Get response and apply enhanced formatting
        try:
            messages = client.beta.threads.messages.list(thread_id=thread_id, limit=5)
            for msg in messages.data:
                if msg.role == "assistant":
                    response = msg.content[0].text.value
                    return format_for_discord_vivian(response)
        except Exception as e:
            print(f"❌ Error retrieving messages: {e}")
            return "❌ Error retrieving PR guidance. Please try again."
        
        return "📱 PR analysis unclear. Please try again with a different approach."
        
    except Exception as e:
        print(f"❌ Vivian error: {e}")
        print(f"📋 Full traceback: {traceback.format_exc()}")
        return "❌ Something went wrong with PR guidance. Please try again!"
    finally:
        # Always remove user from active runs when done
        active_runs.pop(user_id, None)

def format_for_discord_vivian(response):
    """Format response for Discord with error handling"""
    try:
        if not response or not isinstance(response, str):
            return "📱 PR guidance processing. Please try again."
        
        # Clean excessive spacing
        response = response.replace('\n\n\n\n', '\n\n')
        response = response.replace('\n\n\n', '\n\n')
        
        # Tighten list formatting
        response = re.sub(r'\n\n(\d+\.)', r'\n\1', response)
        response = re.sub(r'\n\n(•)', r'\n•', response)
        
        # Length management
        if len(response) > 1900:
            response = response[:1900] + "\n\n📱 *(PR insights continue)*"
        
        print(f"📱 Final response: {len(response)} characters")
        return response.strip()
        
    except Exception as e:
        print(f"❌ Discord formatting error: {e}")
        return "📱 PR message needs refinement. Please try again."

# ============================================================================
# ENHANCED MESSAGE HANDLING WITH COMPREHENSIVE ERROR HANDLING
# ============================================================================

async def send_long_message(original_message, response):
    """Send response with length handling and error recovery"""
    try:
        if len(response) <= 2000:
            await original_message.reply(response)
        else:
            # Split into chunks
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
            
            # Send chunks
            for i, chunk in enumerate(chunks):
                if i == 0:
                    await original_message.reply(chunk)
                else:
                    await original_message.channel.send(chunk)
                    
    except discord.HTTPException as e:
        print(f"❌ Discord HTTP error: {e}")
        try:
            await original_message.reply("📱 PR guidance too complex for Discord. Please try a more specific request.")
        except:
            pass
    except Exception as e:
        print(f"❌ Message sending error: {e}")

# ============================================================================
# DISCORD BOT EVENT HANDLERS WITH ERROR HANDLING
# ============================================================================

@bot.event
async def on_ready():
    """Bot startup with comprehensive initialization"""
    try:
        print(f"✅ {ASSISTANT_NAME} has awakened!")
        print(f"📱 Connected as {bot.user.name} (ID: {bot.user.id})")
        print(f"📋 Watching channels: {', '.join(ALLOWED_CHANNELS)}")
        print(f"🤖 Assistant ID: {ASSISTANT_ID}")
        print(f"🔍 PR Search: {'✅' if BRAVE_API_KEY else '❌'}")
        print(f"📧 Gmail Integration: {'✅' if gmail_service else '❌'}")
        print(f"📅 Calendar Integration: {'✅' if calendar_service else '❌'}")
    except Exception as e:
        print(f"❌ Error in on_ready: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler"""
    print(f"❌ Discord error in {event}: {traceback.format_exc()}")

@bot.event
async def on_message(message):
    """Enhanced message handling with comprehensive error checking"""
    try:
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
            
            # DUPLICATE PREVENTION
            message_key = f"{message.author.id}_{message.content[:50]}"
            current_time = time.time()
            
            # Check if we're already processing this message
            if message_key in processing_messages:
                return
            
            # Check if user sent same message too quickly (within 5 seconds)
            if message.author.id in last_response_time:
                if current_time - last_response_time[message.author.id] < 5:
                    return
            
            # Mark message as being processed
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
                # Always clean up
                processing_messages.discard(message_key)
                
    except Exception as e:
        print(f"❌ Critical on_message error: {e}")
        print(f"📋 Critical traceback: {traceback.format_exc()}")

# ============================================================================
# BASIC BOT COMMANDS WITH ERROR HANDLING
# ============================================================================

@bot.command(name='ping')
async def ping(ctx):
    """Test connectivity with error handling"""
    try:
        latency = round(bot.latency * 1000)
        await ctx.send(f"📱 Pong! Latency: {latency}ms - PR operations running smoothly!")
    except Exception as e:
        print(f"❌ Ping command error: {e}")

@bot.command(name='status')
async def status(ctx):
    """Show Vivian's status with error handling"""
    try:
        embed = discord.Embed(
            title="📱 Vivian Spencer - PR & Communications (Crash Fixed)",
            description="PR Strategy with Email & Calendar Integration",
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
            name="📱 Enhanced Features",
            value="• Gmail Integration - Search and review work emails\n• Calendar Access - Check schedule and meetings\n• PR Strategy - Communications and social media insights\n• Web Research - Current trends and information",
            inline=False
        )
        
        embed.add_field(
            name="📊 Active Status",
            value=f"👥 Conversations: {len(user_conversations)}\n🏃 Active Runs: {len(active_runs)}",
            inline=False
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"❌ Status command error: {e}")

@bot.command(name='help')
async def help_command(ctx):
    """Show Vivian's enhanced help"""
    try:
        embed = discord.Embed(
            title="📱 Vivian Spencer - PR & Communications",
            description="Your strategic PR specialist with email/calendar integration and trend research",
            color=0x4dabf7
        )
        
        embed.add_field(
            name="💬 How to Use Vivian",
            value=f"• Mention @{ASSISTANT_NAME} for PR advice & communications strategy\n• Ask about emails, calendar, trends, crisis communication\n• Get strategic insights based on current market intelligence",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Communications Commands",
            value="• `!emails [query]` - Search or get recent emails\n• `!calendar [days]` - Get calendar events\n• `!search [query]` - Web research\n• `!ping` - Test connectivity\n• `!status` - Show capabilities",
            inline=False
        )
        
        embed.add_field(
            name="📱 Example Requests",
            value="• `@Vivian analyze my email priorities for today`\n• `@Vivian what are the latest PR trends?`\n• `@Vivian help me plan a crisis communication strategy`\n• `@Vivian research social media best practices`",
            inline=False
        )
        
        embed.add_field(
            name="📰 Specialties",
            value="📱 PR Strategy • 📧 Email Management • 📅 Calendar Coordination • 🔍 Trend Research • 💼 Crisis Communication",
            inline=False
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"❌ Help command error: {e}")

@bot.command(name='emails')
async def emails_command(ctx, *, query=None):
    """Search or get recent emails with error handling"""
    try:
        async with ctx.typing():
            if query:
                result = search_gmail_messages(query)
            else:
                result = get_recent_emails()
            await send_long_message(ctx, result)
    except Exception as e:
        print(f"❌ Emails command error: {e}")
        await ctx.send("❌ Error retrieving emails. Please try again.")

@bot.command(name='calendar')
async def calendar_command(ctx, days: int = 7):
    """Get calendar events with error handling"""
    try:
        async with ctx.typing():
            if days == 0:
                events = get_today_schedule()
            else:
                events = get_upcoming_events(days)
            await send_long_message(ctx, events)
    except Exception as e:
        print(f"❌ Calendar command error: {e}")
        await ctx.send("❌ Error retrieving calendar events. Please try again.")

@bot.command(name='search')
async def search_command(ctx, *, query):
    """Search PR information with error handling"""
    try:
        async with ctx.typing():
            results = await pr_search_enhanced(query)
            await send_long_message(ctx, results)
    except Exception as e:
        print(f"❌ Search command error: {e}")
        await ctx.send("❌ Error searching PR information. Please try again.")

# ============================================================================
# BOT STARTUP WITH ERROR HANDLING
# ============================================================================

def main():
    """Main function with comprehensive error handling"""
    try:
        if not DISCORD_TOKEN:
            print("❌ CRITICAL: No Discord token found")
            return
            
        print(f"📱 Starting Vivian Spencer PR & communications bot...")
        bot.run(DISCORD_TOKEN)
        
    except discord.LoginFailure:
        print("❌ CRITICAL: Invalid Discord token")
    except Exception as e:
        print(f"❌ CRITICAL: Bot startup failed: {e}")
        print(f"📋 Startup traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()