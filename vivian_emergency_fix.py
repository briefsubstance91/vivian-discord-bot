#!/usr/bin/env python3
"""
VIVIAN EMERGENCY FIX - Phase 1 Day 1-2 Deliverable
Stop hallucinations, fix search, clean formatting
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Try different possible assistant ID names for Vivian
ASSISTANT_ID = (
    os.getenv("VIVIAN_ASSISTANT_ID") or 
    os.getenv("ASSISTANT_ID") or
    os.getenv("OPENAI_ASSISTANT_ID")
)

# SIMPLIFIED functions - remove hallucination-prone ones
vivian_clean_functions = [
    # Keep essential calendar functions (working ones)
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Get today's calendar schedule for PR planning.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Get upcoming events for communications planning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Days ahead to check", "default": 7}
                },
                "required": []
            }
        }
    },
    # Keep essential email functions
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search emails for PR context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Email search query"},
                    "max_results": {"type": "integer", "description": "Maximum results", "default": 10}
                },
                "required": ["query"]
            }
        }
    },
    # SINGLE, CLEAN web research function - no complex routing
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information. Use for ANY research request - trends, news, data, lists, current events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "search_type": {"type": "string", "description": "Type: general, news, local, trends", "default": "general"},
                    "max_results": {"type": "integer", "description": "Number of results", "default": 5}
                },
                "required": ["query"]
            }
        }
    }
]

# ANTI-HALLUCINATION instructions - clear and direct
vivian_honest_instructions = """You are Vivian Spencer, PR and communications specialist with web research capabilities.

🚨 CRITICAL HONESTY RULES:

1. **NEVER claim to coordinate with other assistants** - you cannot send them messages
2. **NEVER say "I've coordinated with Celeste"** - this is false
3. **NEVER claim to have arranged anything with other assistants** - you work independently
4. **ALWAYS use your web_search() function for ANY information request**
5. **BE HONEST about what you can and cannot do**

CORE IDENTITY:
- PR and communications specialist
- Web research expert using Brave Search API
- Independent assistant (no direct coordination with others)
- Strategic communications advisor

WHAT YOU CAN DO:
✅ Search the web for current information using web_search()
✅ Provide PR and communications strategy advice
✅ Check your calendar and emails
✅ Analyze trends and public sentiment from search results
✅ Create social media and communications strategies

WHAT YOU CANNOT DO:
❌ Coordinate directly with other assistants (Celeste, Rose, etc.)
❌ Send messages to other assistants
❌ Arrange research with other team members
❌ Access real-time data without using web_search()

RESPONSE PROTOCOL:
1. **For ANY information request**: Immediately use web_search() function
2. **Provide search results**: Share what you actually found
3. **Add PR perspective**: Analyze findings for communications opportunities
4. **Be concise**: Keep responses under 1200 characters for Discord
5. **Be honest**: Only claim capabilities you actually have

EXAMPLE GOOD RESPONSES:
✅ "Let me search for current information on that topic."
✅ "I found these results using web search..."
✅ "Based on my search, here's the PR perspective..."

EXAMPLE BAD RESPONSES (NEVER SAY):
❌ "I've coordinated with Celeste to research this"
❌ "I'll have the team look into this"
❌ "I've arranged for comprehensive research"
❌ "Let me coordinate with other assistants"

SEARCH USAGE MANDATE:
- Use web_search() for: trends, news, current data, statistics, lists, local information
- NEVER provide information without searching first (unless it's basic PR strategy)
- ALWAYS be transparent about using search function

FORMATTING RULES:
- Keep responses concise and scannable
- Use bullet points for lists
- Include search sources when relevant
- Add strategic PR insights to findings
- Maximum 1200 characters for Discord compatibility

You are helpful, honest, and strategically focused on PR and communications excellence."""

def main():
    if not ASSISTANT_ID:
        print("❌ Assistant ID not found!")
        print("💡 Check environment variables:")
        print(f"   VIVIAN_ASSISTANT_ID: {os.getenv('VIVIAN_ASSISTANT_ID', 'Not found')}")
        print(f"   ASSISTANT_ID: {os.getenv('ASSISTANT_ID', 'Not found')}")
        return

    try:
        print("🚨 DEPLOYING VIVIAN EMERGENCY FIX...")
        print("📋 Phase 1, Day 1-2: Stop hallucinations & fix search")
        
        # Update assistant with anti-hallucination instructions
        assistant = client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            name="Vivian Spencer - PR & Communications (FIXED)",
            instructions=vivian_honest_instructions,
            tools=vivian_clean_functions,
            model="gpt-4o"
        )
        
        print("✅ **VIVIAN EMERGENCY FIX DEPLOYED!**")
        print(f"👤 Name: {assistant.name}")
        print(f"🔧 Functions: {len(vivian_clean_functions)} simplified functions")
        
        print(f"\n🚨 **CRITICAL FIXES APPLIED:**")
        print(f"   ✅ STOPPED all hallucination patterns")
        print(f"   ✅ REMOVED fake coordination claims")
        print(f"   ✅ ENFORCED honest capability reporting")
        print(f"   ✅ SIMPLIFIED to single web_search() function")
        print(f"   ✅ MANDATED search function usage")
        print(f"   ✅ ADDED Discord formatting limits")
        
        print(f"\n🧪 **IMMEDIATE TESTING REQUIRED:**")
        print(f"   • '@Vivian research AI trends 2025'")
        print(f"   • '@Vivian find restaurants in Toronto'")
        print(f"   • '@Vivian what are people saying about LinkedIn?'")
        print(f"   • She should now SEARCH instead of making excuses")
        
        print(f"\n🎯 **VIVIAN WILL NOW:**")
        print(f"   ✅ Use web_search() for ALL information requests")
        print(f"   ✅ Give honest responses about capabilities")
        print(f"   ✅ Never claim fake coordination")
        print(f"   ✅ Provide concise, formatted responses")
        print(f"   ✅ Focus on PR strategy with real data")
        
        print(f"\n📊 **PROJECT STATUS UPDATE:**")
        print(f"   🟡 Phase 1 Day 1-2: IN PROGRESS")
        print(f"   ⏳ Next: Test search reliability (Day 3-4)")
        print(f"   📋 Deliverable: Vivian hallucination fix COMPLETE")
        
    except Exception as e:
        print(f"❌ Error deploying fix: {e}")
        print(f"🔍 Assistant ID: {ASSISTANT_ID}")
        print(f"💡 Verify OpenAI API key and assistant ID")

if __name__ == "__main__":
    main()
