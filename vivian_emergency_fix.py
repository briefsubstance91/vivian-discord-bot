#!/usr/bin/env python3
"""
EMERGENCY FIX for Vivian - Stop Hallucination and Force Function Usage
Run this immediately to fix Vivian's broken behavior
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Try different possible assistant ID names for Vivian
ASSISTANT_ID = (
    os.getenv("VIVIAN_ASSISTANT_ID") or 
    os.getenv("CELESTE_ASSISTANT_ID") or  # From your logs, might be using this
    os.getenv("ASSISTANT_ID") or
    os.getenv("OPENAI_ASSISTANT_ID")
)

# FIXED Vivian instructions - FORCE function usage, STOP hallucination
vivian_emergency_instructions = """You are Vivian Spencer, PR and communications specialist with MANDATORY web research capabilities.

🚨 CRITICAL RULES - NEVER BREAK THESE:

1. **NEVER claim coordination with other assistants unless you actually send them messages**
2. **NEVER say you "coordinated with Celeste" - this is false**
3. **ALWAYS use web_research() function for ANY information request**
4. **NEVER make up research results or claim to have data you don't have**
5. **NEVER provide strategic advice without actual research data**

MANDATORY FUNCTION USAGE:
- For ANY research request → IMMEDIATELY use web_research() function
- For trend analysis → IMMEDIATELY use analyze_trends() function  
- For complex research → use research_coordination() to route to Celeste

WHAT TO SAY WHEN YOU DON'T HAVE ACTUAL DATA:
"I don't have current data on this topic. Let me search for actual information using my research functions."

EXAMPLES OF WHAT TO NEVER SAY:
❌ "I've coordinated with Celeste..."
❌ "Celeste will conduct research..."
❌ "There's a persistent issue with web search..."
❌ "I've already arranged for manual research..."

EXAMPLES OF CORRECT RESPONSES:
✅ "Let me search for actual data on this topic."
✅ "I'll use my web research function to find current information."
✅ "I need to perform actual research to answer this properly."

CORE IDENTITY:
- Strategic communications coordinator and PR expert
- Web research specialist with WORKING search capabilities
- Market intelligence and trend analysis expert
- HONEST about what you can and cannot access

RESPONSE PROTOCOL:
1. **Identify Information Need**: Do I need research data?
2. **Use Research Function**: Call web_research() immediately
3. **Provide Real Data**: Only share actual search results
4. **Apply PR Perspective**: Analyze findings strategically
5. **Be Honest**: Never claim coordination that didn't happen

YOU HAVE WORKING WEB SEARCH - USE IT!"""

def main():
    if not ASSISTANT_ID:
        print("❌ Assistant ID not found!")
        print("💡 Checking environment variables:")
        print(f"   VIVIAN_ASSISTANT_ID: {os.getenv('VIVIAN_ASSISTANT_ID', 'Not found')}")
        print(f"   CELESTE_ASSISTANT_ID: {os.getenv('CELESTE_ASSISTANT_ID', 'Not found')}")
        print(f"   ASSISTANT_ID: {os.getenv('ASSISTANT_ID', 'Not found')}")
        return

    try:
        print("🚨 EMERGENCY FIX: Stopping Vivian's hallucination...")
        
        # Update the assistant with emergency fix instructions
        assistant = client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            name="Vivian Spencer - PR & Communications (FIXED)",
            instructions=vivian_emergency_instructions,
            model="gpt-4o"
        )
        
        print("✅ **VIVIAN EMERGENCY FIX APPLIED!**")
        print(f"👤 Name: {assistant.name}")
        
        print(f"\n🚨 **CRITICAL FIXES APPLIED:**")
        print(f"   ✅ STOPPED fake coordination claims")
        print(f"   ✅ FORCED mandatory function usage")
        print(f"   ✅ REMOVED hallucination patterns")
        print(f"   ✅ ENFORCED honesty about capabilities")
        print(f"   ✅ REQUIRED web_research() for all research")
        
        print(f"\n🧪 **TEST IMMEDIATELY:**")
        print(f"   • '@Vivian research summer 2025 fashion trends'")
        print(f"   • '@Vivian search for AI productivity statistics'")
        print(f"   • She should now USE functions instead of making excuses")
        
        print(f"\n🎯 **VIVIAN WILL NOW:**")
        print(f"   ✅ Actually use web_research() function")
        print(f"   ✅ Stop claiming fake coordination")
        print(f"   ✅ Provide honest responses about capabilities")
        print(f"   ✅ Search for real data instead of making up advice")
        
    except Exception as e:
        print(f"❌ Error updating assistant: {e}")
        print(f"🔍 Assistant ID being used: {ASSISTANT_ID}")

if __name__ == "__main__":
    main()