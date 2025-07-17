#!/usr/bin/env python3
"""
UPDATE STATUS & HELP FORMATTING SCRIPT
Updates Vivian and Rose to match the consistent embed formatting used by Flora and Maeve

This script updates:
- Status command formatting (embed-style with sections)
- Help command formatting (structured and professional)
- Consistent visual hierarchy and information display
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create backup of file before updating"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f'{filepath}_backup_{timestamp}'
        shutil.copy2(filepath, backup_name)
        print(f"✅ Backup created: {backup_name}")
        return backup_name
    return None

def update_vivian_status_formatting():
    """Update Vivian's status command to use embed formatting"""
    
    vivian_new_status = '''@bot.command(name='status')
async def status(ctx):
    """Show Vivian's enhanced status with consistent formatting"""
    try:
        embed = discord.Embed(
            title="📱 Vivian Spencer - PR & Communications (Work Calendar Enhanced)",
            description="PR Strategy with Work Calendar & Email Integration",
            color=0x4dabf7
        )
        
        # Core Systems Section
        core_systems = []
        core_systems.append(f"• OpenAI Assistant: {'✅ Connected' if ASSISTANT_ID else '❌ Not configured'}")
        core_systems.append(f"• BG Work Calendar: {'✅ Connected' if work_calendar_accessible else '❌ Not configured'}")
        core_systems.append(f"• Gmail Access: {'✅ Connected' if gmail_service else '❌ Not configured'}")
        core_systems.append(f"• Web Search: {'✅ Available' if BRAVE_API_KEY else '❌ Not configured'}")
        
        embed.add_field(
            name="🔗 Core Systems:",
            value="\\n".join(core_systems),
            inline=False
        )
        
        # Work Calendar Features
        if work_calendar_accessible:
            calendar_features = [
                "• Today's work schedule viewing",
                "• Work briefings for PR planning", 
                "• Meeting-aware communications timing",
                "• Rose integration for executive briefings"
            ]
            embed.add_field(
                name="📅 Work Calendar Features:",
                value="\\n".join(calendar_features),
                inline=False
            )
        
        # Specialties
        specialties = [
            "📅 Meeting-Aware PR",
            "📱 Work Calendar Integration", 
            "📧 Email Management",
            "🔍 Trend Research",
            "💼 Communications Timing",
            "🤝 Rose Integration"
        ]
        embed.add_field(
            name="📰 Specialties:",
            value=" • ".join(specialties),
            inline=False
        )
        
        # Active Status
        embed.add_field(
            name="📊 Active Status:",
            value=f"👥 Conversations: {len(user_conversations)}\\n🏃 Active Runs: {len(active_runs)}",
            inline=False
        )
        
        # Channels
        embed.add_field(
            name="📺 Channels:",
            value="\\n".join([f"#{channel}" for channel in ALLOWED_CHANNELS]),
            inline=True
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"❌ Status command error: {e}")
        # Fallback to simple message
        await ctx.send("📱 Vivian Spencer is online and ready for PR strategy!")'''
    
    return vivian_new_status

def update_vivian_help_formatting():
    """Update Vivian's help command to use embed formatting"""
    
    vivian_new_help = '''@bot.command(name='help')
async def help_command(ctx):
    """Show Vivian's enhanced help with consistent formatting"""
    try:
        embed = discord.Embed(
            title="📱 Vivian Spencer - PR & Communications (Work Calendar Enhanced)",
            description="Your strategic PR specialist with work calendar integration and meeting-aware communications planning",
            color=0x4dabf7
        )
        
        embed.add_field(
            name="💬 How to Use Vivian",
            value=f"• Mention @{ASSISTANT_NAME} for PR advice with work calendar insights\\n• Ask about work schedule, meetings, PR timing, communications strategy\\n• Get meeting preparation and stakeholder follow-up guidance",
            inline=False
        )
        
        embed.add_field(
            name="📅 Work Calendar Commands",
            value="• `!work-today` - Today's work schedule for PR planning\\n• `!work-upcoming [days]` - Upcoming work meetings\\n• `!work-briefing` - Work-focused morning briefing\\n• `!work-freetime` - Find free time for PR activities",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Communications Commands", 
            value="• `!emails [query]` - Search or get recent emails\\n• `!search [query]` - PR research\\n• `!ping` - Test connectivity\\n• `!status` - Show capabilities",
            inline=False
        )
        
        embed.add_field(
            name="📱 Example Requests",
            value="• `@Vivian what meetings do I have today and how should I prepare?`\\n• `@Vivian when's the best time this week for media outreach?`\\n• `@Vivian help me plan communications around my work schedule`\\n• `@Vivian export my work calendar for Rose's briefing`",
            inline=False
        )
        
        embed.add_field(
            name="📰 Specialties",
            value="📅 Meeting-Aware PR • 📱 Work Calendar Integration • 📧 Email Management • 🔍 Trend Research • 💼 Communications Timing • 🤝 Rose Integration",
            inline=False
        )
        
        await ctx.send(embed=embed)
    except Exception as e:
        print(f"❌ Help command error: {e}")
        # Fallback to simple message
        await ctx.send("📱 Vivian Spencer - Your PR & Communications specialist. Mention me for strategic advice!")'''
    
    return vivian_new_help

def update_rose_status_formatting():
    """Update Rose's status command to use embed formatting"""
    
    rose_new_status = '''@bot.command(name='status')
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
            value="\\n".join(core_systems),
            inline=False
        )
        
        # Calendar Integration
        calendar_status = "❌ No calendars accessible"
        if accessible_calendars:
            calendar_names = [name for name, _, _ in accessible_calendars]
            calendar_status = f"✅ {len(accessible_calendars)} calendars: {', '.join(calendar_names)}"
        
        embed.add_field(
            name="📅 Calendar Integration:",
            value=f"{calendar_status}\\n🇨🇦 Timezone: Toronto (America/Toronto)",
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
            value="\\n".join(exec_features),
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
            value=f"👥 Active conversations: {len(user_conversations)}\\n🏢 Allowed channels: {', '.join(ALLOWED_CHANNELS)}\\n📊 Processing: {len(processing_messages)} messages",
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
        await ctx.send("👑 Rose Ashcombe - Executive Assistant ready for strategic planning!")'''
    
    return rose_new_status

def update_rose_help_formatting():
    """Update Rose's help command to use embed formatting"""
    
    rose_new_help = '''@bot.command(name='help')
async def help_command(ctx):
    """Enhanced help command with executive formatting"""
    try:
        embed = discord.Embed(
            title="👑 Rose Ashcombe - Executive Assistant (Complete Enhanced)",
            description="Your strategic executive assistant with complete Google Calendar integration and advanced task management",
            color=0xd4af37  # Gold color for executive
        )

        embed.add_field(
            name="💬 How to Use Rose",
            value=f"• Mention @{bot.user.name if bot.user else 'Rose'} for executive strategy & calendar management\\n• Ask about schedules, planning, productivity optimization\\n• Get strategic insights and actionable recommendations",
            inline=False
        )

        embed.add_field(
            name="📅 Calendar & Scheduling Commands",
            value="• `!today` - Today's executive schedule\\n• `!upcoming [days]` - Upcoming events (default 7 days)\\n• `!briefing` / `!daily` / `!morning` - Morning executive briefing\\n• `!calendar` - Quick calendar overview with AI insights",
            inline=False
        )

        embed.add_field(
            name="🎯 Executive Planning Commands", 
            value="• `!schedule [timeframe]` - Flexible schedule view\\n• `!agenda` - Comprehensive executive agenda\\n• `!overview` - Complete executive overview\\n• `!research <query>` - Strategic planning research",
            inline=False
        )

        embed.add_field(
            name="🔧 System Commands",
            value="• `!status` - System and calendar status\\n• `!ping` - Test connectivity\\n• `!help` - This command menu",
            inline=False
        )

        embed.add_field(
            name="📱 Example Requests",
            value="• `@Rose what's my schedule looking like this week?`\\n• `@Rose help me plan my quarterly review preparation`\\n• `@Rose when do I have free time for strategic planning?`\\n• `@Rose analyze my calendar efficiency`",
            inline=False
        )

        embed.add_field(
            name="🎯 Specialties",
            value="👑 Executive Planning • 📊 Strategic Analysis • 📅 Calendar Mastery • 🎯 Productivity Optimization • 💼 Meeting Management • 📋 Task Coordination",
            inline=False
        )
        
        embed.add_field(
            name="📺 Available Channels",
            value="\\n".join([f"#{channel}" for channel in ALLOWED_CHANNELS]),
            inline=True
        )

        await ctx.send(embed=embed)
        
    except Exception as e:
        print(f"❌ Help command error: {e}")
        # Fallback to simple message
        await ctx.send("👑 Rose Ashcombe - Executive Assistant. Mention me for strategic planning!")'''
    
    return rose_new_help

def patch_vivian_main():
    """Patch Vivian's main.py with new formatting"""
    
    if not os.path.exists('main.py'):
        print("❌ Vivian main.py not found in current directory")
        return False
    
    print("🔧 Patching Vivian's status and help formatting...")
    
    # Read current file
    with open('main.py', 'r') as f:
        content = f.read()
    
    # Find and replace status command
    old_status_pattern = r'@bot\.command\(name=\'status\'\)\nasync def status\(ctx\):.*?except Exception as e:\s*print\(f"❌ Status command error: \{e\}"\)'
    new_status = update_vivian_status_formatting()
    
    # Find and replace help command  
    old_help_pattern = r'@bot\.command\(name=\'help\'\)\nasync def help_command\(ctx\):.*?except Exception as e:\s*print\(f"❌ Help command error: \{e\}"\)'
    new_help = update_vivian_help_formatting()
    
    # Apply replacements
    import re
    
    # Replace status command
    if '@bot.command(name=\'status\')' in content:
        # Find the entire status function and replace it
        status_start = content.find('@bot.command(name=\'status\')')
        if status_start != -1:
            # Find the end of the function (next @bot.command or end of file)
            next_command = content.find('@bot.command', status_start + 1)
            if next_command == -1:
                next_command = len(content)
            
            # Replace the status function
            content = content[:status_start] + new_status + '\\n\\n' + content[next_command:]
            print("✅ Updated Vivian status command")
        else:
            print("⚠️ Could not locate Vivian status command")
    
    # Replace help command
    if '@bot.command(name=\'help\')' in content:
        # Find the entire help function and replace it
        help_start = content.find('@bot.command(name=\'help\')')
        if help_start != -1:
            # Find the end of the function (next @bot.command or end of file)
            next_command = content.find('@bot.command', help_start + 1)
            if next_command == -1:
                next_command = len(content)
            
            # Replace the help function
            content = content[:help_start] + new_help + '\\n\\n' + content[next_command:]
            print("✅ Updated Vivian help command")
        else:
            print("⚠️ Could not locate Vivian help command")
    
    # Write back to file
    with open('main.py', 'w') as f:
        f.write(content)
    
    return True

def patch_rose_main():
    """Patch Rose's main.py with new formatting"""
    
    rose_files = ['main.py', 'rose_main.py', '../rose-discord-bot/main.py']
    rose_file = None
    
    for filepath in rose_files:
        if os.path.exists(filepath):
            rose_file = filepath
            break
    
    if not rose_file:
        print("❌ Rose main.py not found. Tried: main.py, rose_main.py, ../rose-discord-bot/main.py")
        return False
    
    print(f"🔧 Patching Rose's status and help formatting in {rose_file}...")
    
    # Read current file
    with open(rose_file, 'r') as f:
        content = f.read()
    
    # Get new formatting
    new_status = update_rose_status_formatting()
    new_help = update_rose_help_formatting()
    
    # Replace status command
    if '@bot.command(name=\'status\')' in content or 'async def status_command(ctx):' in content:
        # Find and replace status function
        status_patterns = [
            r'@bot\.command\(name=\'status\'\)\nasync def status_command\(ctx\):.*?(?=@bot\.command|\n\nif __name__|$)',
            r'@bot\.command\(name=\'status\'\)\nasync def status\(ctx\):.*?(?=@bot\.command|\n\nif __name__|$)'
        ]
        
        for pattern in status_patterns:
            if re.search(pattern, content, re.DOTALL):
                content = re.sub(pattern, new_status + '\\n\\n', content, flags=re.DOTALL)
                print("✅ Updated Rose status command")
                break
        else:
            print("⚠️ Could not locate Rose status command pattern")
    
    # Replace help command
    if '@bot.command(name=\'help\')' in content:
        help_pattern = r'@bot\.command\(name=\'help\'\)\nasync def help_command\(ctx\):.*?(?=@bot\.command|\n\nif __name__|$)'
        if re.search(help_pattern, content, re.DOTALL):
            content = re.sub(help_pattern, new_help + '\\n\\n', content, flags=re.DOTALL)
            print("✅ Updated Rose help command")
        else:
            print("⚠️ Could not locate Rose help command pattern")
    
    # Write back to file
    with open(rose_file, 'w') as f:
        f.write(content)
    
    return True

def main():
    """Main script execution"""
    print("🎨 STATUS & HELP FORMATTING UPDATE SCRIPT")
    print("=" * 60)
    print("Updating Vivian and Rose to match Flora/Maeve embed formatting")
    print()
    
    # Check current directory
    print(f"📂 Current directory: {os.getcwd()}")
    print(f"📄 Files found: {', '.join([f for f in os.listdir('.') if f.endswith('.py')])}")
    print()
    
    # Create backups and patch files
    results = []
    
    # Patch Vivian
    print("📱 Processing Vivian Spencer...")
    if os.path.exists('main.py'):
        backup_file('main.py')
        if patch_vivian_main():
            results.append("✅ Vivian: Status & Help updated")
        else:
            results.append("❌ Vivian: Failed to update")
    else:
        results.append("⚠️ Vivian: main.py not found")
    
    print()
    
    # Patch Rose
    print("👑 Processing Rose Ashcombe...")
    if patch_rose_main():
        results.append("✅ Rose: Status & Help updated")
    else:
        results.append("❌ Rose: Failed to update")
    
    print()
    print("🎉 FORMATTING UPDATE COMPLETE!")
    print("=" * 60)
    
    for result in results:
        print(f"  {result}")
    
    print()
    print("📋 NEW FORMATTING FEATURES:")
    print("  • Discord embeds with consistent color schemes")
    print("  • Structured information sections")
    print("  • Professional visual hierarchy")
    print("  • Consistent field organization")
    print("  • Enhanced readability and branding")
    print()
    print("🎨 VISUAL IMPROVEMENTS:")
    print("  • Vivian: Professional blue theme (0x4dabf7)")
    print("  • Rose: Executive gold theme (0xd4af37)")
    print("  • Organized sections with clear headers")
    print("  • Consistent emoji usage and spacing")
    print()
    print("🚀 NEXT STEPS:")
    print("  1. Test updated formatting: !status and !help commands")
    print("  2. Deploy to Railway if satisfied with local results")
    print("  3. Verify consistency across all assistants")
    print()
    print("💡 TESTING COMMANDS:")
    print("  • !status - View enhanced status display")
    print("  • !help - View improved help formatting")
    print("  • Compare with Flora and Maeve formatting")

if __name__ == "__main__":
    main()
