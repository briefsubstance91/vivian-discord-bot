import discord
from discord.ext import commands
import os
import asyncio
from datetime import datetime
import aiohttp
from dotenv import load_dotenv
from utils.openai_handler import get_openai_response

# Load environment variables
load_dotenv()

# Run research enhancement on startup
async def run_research_enhancement():
    """Run the research enhancement script on startup"""
    print("🔧 Running Vivian research enhancement...")
    try:
        import subprocess
        result = subprocess.run(['python3', 'fix_vivian_research.py'], 
                              capture_output=True, text=True, timeout=30)
        
        print("📋 Research enhancement output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Enhancement warnings/errors:")
            print(result.stderr)
            
        if result.returncode == 0:
            print("✅ Research enhancement completed successfully!")
        else:
            print(f"❌ Enhancement failed with return code: {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("⏱️ Enhancement timed out after 30 seconds")
    except Exception as e:
        print(f"❌ Error running enhancement: {e}")
    
    print("🚀 Continuing with Vivian startup...")

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BRAVE_API_KEY = os.getenv('BRAVE_API_KEY')

# Configure Discord intents
intents = discord.Intents.default()
intents.message_content = True

# Bot setup with commands - disable default help to avoid conflicts
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Allowed channels for Vivian
ALLOWED_CHANNELS = ['social-overview', 'news-feed', 'external-communications', 'general']

print("🚀 Starting Enhanced Vivian - PR & Communications with Research...")

# ============================================================================
# FIXED WEB SEARCH FUNCTIONS
# ============================================================================

async def search_web(query, search_type="general", num_results=5):
    """FIXED web search using Brave Search API"""
    try:
        if not BRAVE_API_KEY:
            return "🔍 **Research capabilities unavailable** - BRAVE_API_KEY not configured.\n\n📨 **Coordination Option:** I can route this research request to Celeste for manual research and synthesis."
        
        headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip',
            'X-Subscription-Token': BRAVE_API_KEY
        }
        
        # FIXED: Removed problematic boolean parameters
        params = {
            'q': query,
            'count': num_results,
            'offset': 0,
            'mkt': 'en-US',
            'safesearch': 'moderate'
            # Removed textDecorations and textFormat - they were causing the error
        }
        
        # Enhanced search type handling
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
        elif search_type == "pr_analysis":
            params['q'] += " public opinion media coverage"
        
        url = "https://api.search.brave.com/res/v1/web/search"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('web', {}).get('results', [])
                    
                    if not results:
                        return f"🔍 **No results found for '{query}'**\n\n💡 **Research Alternatives:**\n• Try broader search terms\n• Consider routing to Celeste for manual research\n• Check spelling and specificity"
                    
                    formatted_results = []
                    for i, result in enumerate(results[:num_results], 1):
                        title = result.get('title', 'No title')
                        snippet = result.get('description', 'No description')
                        url_link = result.get('url', '')
                        
                        # Clean up snippet length
                        if len(snippet) > 200:
                            snippet = snippet[:200] + '...'
                        
                        # Add source indicators for PR context
                        source_indicator = ""
                        if "reddit.com" in url_link.lower():
                            source_indicator = "🔴 Reddit: "
                        elif any(domain in url_link.lower() for domain in ['edu', 'gov']):
                            source_indicator = "🎓 Official: "
                        elif any(domain in url_link.lower() for domain in ['news', 'cnn', 'bbc', 'reuters']):
                            source_indicator = "📰 News: "
                        elif any(domain in url_link.lower() for domain in ['wikipedia', 'wiki']):
                            source_indicator = "📚 Reference: "
                        
                        formatted_results.append(f"**{i}. {source_indicator}{title}**\n{snippet}\n🔗 {url_link}\n")
                    
                    return f"🔍 **Research Results: '{query}'**\n\n" + "\n".join(formatted_results)
                else:
                    return f"🔍 **Search Error** (Status {response.status})\n\n📨 **Coordination Option:** I can route this research to Celeste for manual research."
                    
    except Exception as e:
        print(f"Search error: {e}")
        return f"🔍 **Research Error:** {str(e)}\n\n📨 **Coordination Option:** I can coordinate with Celeste for alternative research approaches."

# ============================================================================
# RESEARCH DETECTION AND ROUTING
# ============================================================================

def detect_research_request(message_content):
    """Enhanced detection of research requests"""
    content_lower = message_content.lower()
    
    # Research trigger words and phrases
    research_triggers = [
        # Direct research requests
        'research', 'find information', 'look up', 'search for', 'what are', 'tell me about',
        
        # List and recommendation requests
        'list of', 'top 10', 'top 20', 'top 30', 'best', 'recommend', 'suggestions',
        
        # Location-specific requests
        'in toronto', 'in quebec', 'in ontario', 'in canada', 'near me', 'around',
        
        # Current/recent information
        'latest', 'current', 'recent', 'trending', 'now', '2024', '2025',
        
        # Question patterns
        'what is', 'what are', 'who is', 'who are', 'where is', 'where are',
        'how many', 'which', 'when did', 'why',
        
        # Specific topics that usually need research
        'news about', 'trends in', 'statistics', 'data on', 'reports on',
        'companies that', 'products that', 'services that',
        
        # Market/PR research
        'sentiment about', 'opinion on', 'reviews of', 'feedback on',
        'public perception', 'brand reputation', 'competitor',
        
        # Local business/services
        'restaurants', 'hotels', 'shops', 'services', 'businesses',
        'events', 'activities', 'attractions'
    ]
    
    # Check for trigger words/phrases
    for trigger in research_triggers:
        if trigger in content_lower:
            return True
    
    # Check for question patterns
    question_patterns = [
        content_lower.startswith('what'),
        content_lower.startswith('who'),
        content_lower.startswith('where'),
        content_lower.startswith('when'),
        content_lower.startswith('why'),
        content_lower.startswith('how'),
        content_lower.startswith('which'),
        content_lower.startswith('can you find'),
        content_lower.startswith('can you tell'),
        content_lower.startswith('do you know'),
        '?' in content_lower
    ]
    
    return any(question_patterns)

def determine_search_type(message_content):
    """Determine the best search type based on content"""
    content_lower = message_content.lower()
    
    if any(word in content_lower for word in ['reddit', 'discussion', 'opinion']):
        return "reddit"
    elif any(word in content_lower for word in ['news', 'current', 'recent', 'latest']):
        return "news"
    elif any(word in content_lower for word in ['academic', 'research', 'study', 'paper']):
        return "academic"
    elif any(word in content_lower for word in ['near', 'local', 'in toronto', 'in quebec', 'restaurant', 'business']):
        return "local"
    elif any(word in content_lower for word in ['trend', 'popular', 'trending', 'hot']):
        return "trends"
    elif any(word in content_lower for word in ['pr', 'reputation', 'sentiment', 'perception']):
        return "pr_analysis"
    else:
        return "general"

# ============================================================================
# BOT COMMANDS - ENHANCED WITH RESEARCH
# ============================================================================

@bot.command(name='ping')
async def ping(ctx):
    """Test bot connectivity"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description="Vivian is online and ready for PR strategy and research!",
        color=0x51cf66
    )
    embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
    embed.add_field(name="Status", value="✅ Operational", inline=True)
    embed.add_field(name="Research", value="✅ Enhanced" if BRAVE_API_KEY else "⚠️ Limited", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='status')
async def status(ctx):
    """Show comprehensive bot status"""
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🤖 Vivian Status - PR & Communications with Research",
        description="External Communications + Market Research + PR Strategy",
        color=0x4dabf7
    )
    
    embed.add_field(
        name="🔗 OpenAI Assistant",
        value="✅ Connected" if os.getenv("ASSISTANT_ID") else "❌ Not configured",
        inline=True
    )
    
    embed.add_field(
        name="🔍 Research Capabilities",
        value="✅ Enhanced" if BRAVE_API_KEY else "⚠️ Limited to coordination",
        inline=True
    )
    
    embed.add_field(
        name="📅 Calendar Integration",
        value="✅ Connected" if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') else "⚠️ Not configured",
        inline=True
    )
    
    embed.add_field(
        name="📧 Email Integration",
        value="✅ Ready" if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') else "⚠️ Not configured",
        inline=True
    )
    
    capabilities = [
        "🔍 Enhanced Web Research",
        "📊 Trend Analysis & Market Intelligence", 
        "📰 News & Current Events Monitoring",
        "🎯 PR Strategy & Communications",
        "📧 Email & Calendar Management",
        "🤝 Team Coordination (Route to Celeste)"
    ]
    
    embed.add_field(
        name="⚡ Enhanced Capabilities",
        value="\n".join(capabilities),
        inline=False
    )
    
    embed.add_field(
        name="👀 Monitored Channels",
        value=", ".join([f"#{channel}" for channel in ALLOWED_CHANNELS]),
        inline=False
    )
    
    embed.set_footer(text=f"Latency: {latency}ms | Your PR & Research Specialist")
    
    await ctx.send(embed=embed)

@bot.command(name='research')
async def research_command(ctx, *, query):
    """Perform enhanced research with PR perspective"""
    async with ctx.typing():
        search_type = determine_search_type(query)
        
        if BRAVE_API_KEY:
            # Perform direct web search
            search_results = await search_web(query, search_type, num_results=5)
            
            # Send to OpenAI with research context
            research_prompt = f"""RESEARCH REQUEST with web data:

SEARCH RESULTS:
{search_results}

USER QUERY: {query}
SEARCH TYPE: {search_type}

Instructions:
1. Analyze the research results from a PR and communications perspective
2. Synthesize key findings into strategic insights
3. Identify reputation management opportunities
4. Suggest communication strategies based on findings
5. Provide actionable recommendations for external communications
6. If research is incomplete, offer to coordinate with Celeste for deeper analysis"""
            
            response = await get_openai_response(research_prompt, user_id=ctx.author.id)
        else:
            # No web search available - coordinate with team
            coordination_prompt = f"""RESEARCH COORDINATION REQUEST:

USER QUERY: {query}
SEARCH TYPE: {search_type}

I don't have web search capabilities available right now. Please:
1. Acknowledge the research request
2. Explain the coordination approach
3. Offer to route this to Celeste for comprehensive research
4. Provide any relevant context I already know
5. Suggest next steps for getting this research completed"""
            
            response = await get_openai_response(coordination_prompt, user_id=ctx.author.id)
        
        await send_long_message_ctx(ctx, response)

@bot.command(name='trends')
async def trends_command(ctx, *, topic):
    """Analyze trends and sentiment for PR strategy"""
    async with ctx.typing():
        if BRAVE_API_KEY:
            # Search for trends
            trend_results = await search_web(f"{topic} trends 2024 2025", "trends", num_results=5)
            sentiment_results = await search_web(f"{topic} public opinion sentiment", "pr_analysis", num_results=3)
            
            trends_prompt = f"""TREND ANALYSIS REQUEST:

TOPIC: {topic}

TREND DATA:
{trend_results}

SENTIMENT DATA:
{sentiment_results}

Instructions:
1. Analyze current trends and trajectory for this topic
2. Assess public sentiment and perception
3. Identify PR opportunities and risks
4. Recommend strategic communication approaches
5. Suggest content themes and messaging strategies
6. Provide timeline recommendations for communications"""
            
            response = await get_openai_response(trends_prompt, user_id=ctx.author.id)
        else:
            response = f"📊 **Trend Analysis Request: {topic}**\n\n⚠️ Web research unavailable - would coordinate with Celeste for comprehensive trend analysis.\n\n🎯 **Next Steps:**\n• Route to Celeste for manual trend research\n• Provide strategic framework for analysis\n• Schedule follow-up for comprehensive insights"
        
        await send_long_message_ctx(ctx, response)

@bot.command(name='help')
async def help_command(ctx):
    """Show comprehensive help for enhanced Vivian"""
    embed = discord.Embed(
        title="🤖 Vivian Spencer - PR & Communications with Research",
        description="External Communications + Market Research + PR Strategy",
        color=0x4dabf7
    )
    
    embed.add_field(
        name="🔍 Research Commands",
        value="• `!research [topic]` - Enhanced web research\n• `!trends [topic]` - Trend analysis & sentiment\n• `@Vivian research [topic]` - Natural language research\n• `@Vivian find information about [topic]`",
        inline=True
    )
    
    embed.add_field(
        name="📅 Calendar & Email",
        value="• `!schedule today` - Today's schedule\n• `!schedule week` - This week\n• `@Vivian check my emails` - Email review\n• `@Vivian what's on my calendar?`",
        inline=True
    )
    
    embed.add_field(
        name="🎯 PR & Communications",
        value="• `@Vivian draft LinkedIn post about [topic]`\n• `@Vivian create PR strategy for [event]`\n• `@Vivian analyze sentiment about [brand]`\n• Focus on external communications",
        inline=True
    )
    
    embed.add_field(
        name="🔍 Enhanced Research Examples",
        value="• `@Vivian list top 30 birds in Quyon Quebec`\n• `@Vivian research LinkedIn trends for 2025`\n• `@Vivian find best restaurants in Toronto`\n• `@Vivian what are people saying about AI?`",
        inline=False
    )
    
    embed.add_field(
        name="🤝 Team Coordination",
        value="• Route complex content to Celeste\n• Coordinate with Rose for scheduling\n• Strategic oversight on all communications\n• Focus on external reputation management",
        inline=True
    )
    
    embed.add_field(
        name="🛠️ System Commands",
        value="• `!ping` - Test connectivity\n• `!status` - Show capabilities\n• `!help` - This help message\n• `!clear_memory` - Reset conversation",
        inline=True
    )
    
    embed.add_field(
        name="💡 Key Features",
        value="• **Enhanced Research** - Direct web search for any topic\n• **PR Perspective** - Communications focus on all analysis\n• **Trend Analysis** - Market intelligence and sentiment\n• **Team Coordination** - Route to specialists when needed",
        inline=False
    )
    
    embed.set_footer(text="🎯 Your PR & Research Specialist - Now with enhanced research capabilities!")
    
    await ctx.send(embed=embed)

# ============================================================================
# MESSAGE HANDLING - ENHANCED WITH AUTOMATIC RESEARCH DETECTION
# ============================================================================

@bot.event
async def on_ready():
    print(f"🤖 Enhanced Vivian is online as {bot.user}")
    print(f"🔗 Connected to {len(bot.guilds)} guild(s)")
    print(f"👀 Monitoring channels: {', '.join(ALLOWED_CHANNELS)}")
    print(f"📅 Calendar: {'✅' if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') else '❌'}")
    print(f"📧 Gmail: {'✅' if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON') else '❌'}")
    print(f"🔍 Enhanced Research: {'✅' if BRAVE_API_KEY else '⚠️ Limited'}")
    print(f"🧠 Memory: ✅ Enhanced with context tracking")
    print(f"🎯 Research Detection: ✅ ACTIVE")
    print(f"🚀 Enhanced Vivian: Your PR & Research specialist is ready!")

@bot.event
async def on_message(message):
    """Enhanced message handler with automatic research detection"""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Process commands first
    await bot.process_commands(message)
    
    # Only respond in allowed channels or DMs
    if not isinstance(message.channel, discord.DMChannel) and message.channel.name not in ALLOWED_CHANNELS:
        return

    # Handle mentions and DMs with enhanced research detection
    if bot.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        try:
            content = message.content
            
            # Clean mentions
            if bot.user.mentioned_in(message):
                for mention in message.mentions:
                    if mention == bot.user:
                        content = content.replace(f'<@{mention.id}>', '').strip()
                        content = content.replace(f'<@!{mention.id}>', '').strip()
            
            if not content:
                await message.reply(
                    "Hi! I'm Vivian Spencer, your PR & Communications specialist with enhanced research! 🔍\n\n"
                    "**🔍 I can research anything for you**\n"
                    "**📊 I analyze trends and sentiment**\n"
                    "**📧 I manage your communications**\n"
                    "**🎯 I provide PR strategy and insights**\n\n"
                    "Try: `@Vivian research [topic]` or `!help` for all commands!"
                )
                return

            print(f"📨 Enhanced message from {message.author}: {content}")
            
            # Show typing indicator
            async with message.channel.typing():
                # ENHANCED: Automatic research detection
                if detect_research_request(content) and BRAVE_API_KEY:
                    print(f"🔍 AUTO-DETECTED research request, performing web search...")
                    
                    # Determine optimal search type
                    search_type = determine_search_type(content)
                    print(f"🔍 Search type determined: {search_type}")
                    
                    # Perform web search
                    search_results = await search_web(content, search_type, num_results=5)
                    
                    # Enhanced prompt with research data and PR context
                    enhanced_content = f"""AUTOMATIC RESEARCH DETECTION:

USER REQUEST: {content}
SEARCH TYPE: {search_type}
RESEARCH DATA:
{search_results}

INSTRUCTIONS:
1. This was automatically detected as a research request
2. Analyze the web search results with PR and communications expertise
3. Provide strategic insights and actionable recommendations
4. Focus on external communications opportunities
5. Consider reputation management aspects
6. Offer coordination with team if deeper analysis needed
7. Present findings in clear, professional format

Request: {content}"""

                    reply = await get_openai_response(enhanced_content, user_id=message.author.id)
                    
                elif detect_research_request(content) and not BRAVE_API_KEY:
                    # Research detected but no web search - coordinate
                    print(f"🔍 Research detected but no web search available - coordinating...")
                    
                    coordination_content = f"""RESEARCH COORDINATION REQUEST:

USER REQUEST: {content}
DETECTED: Research request requiring web search
STATUS: Web search unavailable

INSTRUCTIONS:
1. Acknowledge this is a research request
2. Explain that I can coordinate with Celeste for comprehensive research
3. Provide any relevant context I already know
4. Suggest strategic approach for getting this information
5. Offer next steps for research coordination
6. Maintain PR and communications focus

Request: {content}"""
                    
                    reply = await get_openai_response(coordination_content, user_id=message.author.id)
                    
                else:
                    # Regular request without research
                    regular_content = f"""PR & COMMUNICATIONS REQUEST:

USER REQUEST: {content}
CONTEXT: Standard communications and PR support request

INSTRUCTIONS:
1. Provide strategic PR and communications support
2. Focus on external communications opportunities
3. Consider reputation management aspects
4. Offer research if relevant information would help
5. Coordinate with team members when appropriate
6. Maintain professional communications perspective

Request: {content}"""
                    
                    reply = await get_openai_response(regular_content, user_id=message.author.id)
                
                # Send response with Discord message limit handling
                await send_long_message(message, reply)
                
        except Exception as e:
            print(f"❌ Error processing enhanced message: {e}")
            await message.reply("Sorry, I encountered an error while processing your request. Please try again or use `!help` for guidance.")

async def send_long_message(message, content):
    """Send long messages in chunks"""
    if len(content) <= 2000:
        await message.reply(content)
    else:
        chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
        for i, chunk in enumerate(chunks):
            if i == 0:
                await message.reply(chunk)
            else:
                await message.channel.send(f"*(continued {i+1}/{len(chunks)})*\n{chunk}")
            await asyncio.sleep(0.5)

async def send_long_message_ctx(ctx, content):
    """Send long messages in chunks for commands"""
    if len(content) <= 2000:
        await ctx.send(content)
    else:
        chunks = [content[i:i+1900] for i in range(0, len(content), 1900)]
        for i, chunk in enumerate(chunks):
            await ctx.send(f"*(Part {i+1}/{len(chunks)})*\n{chunk}")
            await asyncio.sleep(0.5)

@bot.event
async def on_command_error(ctx, error):
    """Enhanced error handling"""
    if isinstance(error, commands.CommandNotFound):
        return  # Ignore unknown commands
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ **Missing argument:** `{error.param.name}`\n\nUse `!help` to see correct usage.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ **Invalid argument:** {str(error)}\n\nUse `!help` to see correct usage.")
    else:
        print(f"❌ Command error: {error}")
        await ctx.send("❌ **Error**\n\nSomething went wrong. Please try again or use `!help` for guidance.")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables")
        exit(1)
    
    print("🚀 Starting Enhanced Vivian with automatic research detection...")
    
    # Run the research enhancement before starting the bot
    async def startup():
        await run_research_enhancement()
        try:
            await bot.start(DISCORD_TOKEN)
        except Exception as e:
            print(f"❌ Failed to start enhanced Vivian bot: {e}")
    
    # Run the startup sequence
    asyncio.run(startup())
