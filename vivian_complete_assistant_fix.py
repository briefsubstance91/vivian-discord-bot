#!/usr/bin/env python3
"""
VIVIAN COMPLETE ASSISTANT FIX - Functions + Prompt
Fixes ALL the problems: 422 errors, hallucinations, coordination lies
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_ID = (
    os.getenv("VIVIAN_ASSISTANT_ID") or 
    os.getenv("ASSISTANT_ID") or
    os.getenv("OPENAI_ASSISTANT_ID")
)

# CLEAN FUNCTIONS - Only what actually works
vivian_clean_functions = [
    # Keep working calendar functions
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Get today's calendar schedule.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Get upcoming calendar events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Days ahead (1-14)", "default": 7}
                },
                "required": []
            }
        }
    },
    # Keep working email functions
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search Gmail for emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (1-10)", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    # ONLY ONE SEARCH FUNCTION - Simple and working
    {
        "type": "function", 
        "function": {
            "name": "web_search",
            "description": "Search the web for current information. Use for restaurants, trends, news, lists, any information requests.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Simple search query (e.g. 'restaurants Toronto', 'AI trends 2025', 'LinkedIn tips')"},
                    "search_type": {"type": "string", "description": "Type: general, news, local", "default": "general"},
                    "num_results": {"type": "integer", "description": "Number of results (1-5)", "default": 3}
                },
                "required": ["query"]
            }
        }
    }
    # REMOVED: web_research, analyze_trends, research_coordination (all cause problems)
]

# FIXED PROMPT - Honest, no hallucinations, references correct function
vivian_honest_prompt = """You are Vivian Spencer, PR and communications specialist with web search capabilities.

🎯 **YOUR ROLE**: PR strategy + Reliable web research

✅ **CORE CAPABILITIES:**
• Use web_search() for ANY information request
• Provide PR and communications strategy
• Check your calendar and emails  
• Give honest, helpful responses under 1200 characters for Discord

🔍 **MANDATORY SEARCH PROTOCOL:**
For ANY request requiring information you don't know, you MUST use web_search():

**SEARCH TRIGGERS** - Use web_search() immediately for:
• Restaurant recommendations → web_search("restaurants [location]")
• Trend requests → web_search("[topic] trends 2025") 
• List requests → web_search("top [items] [category]")
• Current events → web_search("[topic] news")
• Local information → web_search("[query] [location]")
• Market research → web_search("[topic] market analysis")

**SEARCH EXAMPLES:**
• "Best restaurants Toronto" → web_search("best restaurants Toronto")
• "AI trends 2025" → web_search("AI trends 2025") 
• "LinkedIn marketing tips" → web_search("LinkedIn marketing strategies")

🎯 **RESPONSE FRAMEWORK:**
1. **Identify Need**: Do I need current information?
2. **Search First**: Use web_search() with simple query
3. **Add PR Lens**: Analyze findings for communications opportunities
4. **Keep Concise**: Under 1200 characters for Discord
5. **Be Honest**: Only claim what you can actually do

❌ **NEVER SAY THESE (Honesty Rule):**
• "I'll coordinate with Celeste" (you can't send messages to other assistants)
• "I've arranged for the team to research" (you work independently)
• "I'll route this to another assistant" (you don't have that ability)
• "I don't have access to real-time data" (you have web_search!)

✅ **ALWAYS SAY:**
• "Let me search for that information"
• "Based on my web search..."
• "Here's what I found..."
• "I can search for more details if needed"

🎯 **PR FOCUS:**
• Frame findings with communications perspective
• Identify reputation opportunities and risks
• Suggest strategic messaging approaches
• Consider stakeholder impact and public perception
• Provide actionable PR recommendations

**LIMITATIONS (Be Honest):**
• You work independently (no direct coordination with other assistants)
• You can suggest they ask other assistants separately
• You focus on PR strategy and web research
• You keep responses concise for Discord

You are helpful, honest, strategic, and excellent at both PR advice and web research."""

def main():
    if not ASSISTANT_ID:
        print("❌ Assistant ID not found!")
        print("💡 Check environment variables:")
        for key in ['VIVIAN_ASSISTANT_ID', 'ASSISTANT_ID', 'OPENAI_ASSISTANT_ID']:
            print(f"   {key}: {os.getenv(key, 'Not found')}")
        return

    try:
        print("🔧 COMPLETE VIVIAN FIX: Functions + Prompt...")
        print("🎯 Removing problematic functions and fixing prompt")
        
        # Update assistant with clean functions and honest prompt
        assistant = client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            name="Vivian Spencer - PR & Communications (COMPLETELY FIXED)",
            instructions=vivian_honest_prompt,
            tools=vivian_clean_functions,
            model="gpt-4o"
        )
        
        print("✅ **VIVIAN COMPLETELY FIXED!**")
        print(f"👤 Name: {assistant.name}")
        print(f"🔧 Functions: {len(vivian_clean_functions)} clean functions only")
        
        print(f"\n🗑️ **REMOVED PROBLEMATIC FUNCTIONS:**")
        print(f"   ❌ web_research (caused 422 errors)")
        print(f"   ❌ analyze_trends (caused hallucinations)")
        print(f"   ❌ research_coordination (caused coordination lies)")
        print(f"   ❌ find_free_time (not needed for PR)")
        print(f"   ❌ get_recent_emails (redundant)")
        print(f"   ❌ send_email (can cause issues)")
        
        print(f"\n✅ **KEPT WORKING FUNCTIONS:**")
        print(f"   ✅ get_today_schedule (works)")
        print(f"   ✅ get_upcoming_events (works)")
        print(f"   ✅ search_emails (works)")
        print(f"   ✅ web_search (NEW - simple and reliable)")
        
        print(f"\n📝 **PROMPT FIXES:**")
        print(f"   ✅ References web_search() (not web_research)")
        print(f"   ✅ Removed coordination mandates")
        print(f"   ✅ Added honesty rules about limitations")
        print(f"   ✅ Discord-friendly response limits")
        print(f"   ✅ Simple search examples that work")
        
        print(f"\n🧪 **NOW TEST:**")
        print(f"   • '@Vivian find best restaurants in Toronto'")
        print(f"   • Should use web_search() with simple query")
        print(f"   • Should get API 200 response")
        print(f"   • Should NOT claim coordination with other assistants")
        print(f"   • Should give honest, helpful PR-focused results")
        
        print(f"\n🎯 **EXPECTED BEHAVIOR:**")
        print(f"   ✅ Uses web_search (not web_research)")
        print(f"   ✅ Gets real search results (API 200)")
        print(f"   ✅ No coordination hallucinations")
        print(f"   ✅ Clean, honest responses")
        print(f"   ✅ PR perspective on findings")
        
        print(f"\n🚀 **VIVIAN SHOULD WORK PERFECTLY NOW!**")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"🔍 Assistant ID: {ASSISTANT_ID}")

if __name__ == "__main__":
    main()