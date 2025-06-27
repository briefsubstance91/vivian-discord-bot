#!/usr/bin/env python3
"""
Fix Vivian's Research Capabilities - Enhanced Research Detection & Web Search
Save this as fix_vivian_research.py in your Vivian repository root
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

# Enhanced Vivian functions with research focus
vivian_research_functions = [
    # Existing Calendar Functions (keep these)
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Get today's calendar schedule for PR and communications planning.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tomorrow_schedule", 
            "description": "Get tomorrow's calendar schedule for communications preparation.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Get upcoming events for strategic communications planning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Days ahead to check", "default": 7}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_free_time",
            "description": "Find available time slots for meetings and PR activities.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "duration": {"type": "integer", "description": "Duration in minutes", "default": 60},
                    "date": {"type": "string", "description": "Target date (YYYY-MM-DD)", "default": ""}
                },
                "required": []
            }
        }
    },
    # Existing Email Functions (keep these)
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search emails for PR and communications context.",
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
    {
        "type": "function",
        "function": {
            "name": "get_recent_emails",
            "description": "Get recent emails for communications review.",
            "parameters": {
                "type": "object",
                "properties": {"max_results": {"type": "integer", "description": "Number of emails", "default": 10}},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send professional communications and PR emails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email content"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    # NEW: Research Functions - These will trigger web search in your bot
    {
        "type": "function",
        "function": {
            "name": "web_research",
            "description": "MANDATORY: Use this for ALL information requests including lists, trends, local information, current events, market research, competitor analysis, and any question requiring up-to-date data. This triggers web search via Brave API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Research query - be specific and targeted"},
                    "search_type": {"type": "string", "description": "Type: general, news, academic, local, trends, reddit", "default": "general"},
                    "num_results": {"type": "integer", "description": "Number of results to analyze", "default": 5},
                    "focus_area": {"type": "string", "description": "Focus: PR_analysis, market_research, competitor_intel, trend_analysis, local_info", "default": "general"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_trends",
            "description": "Analyze trends and public sentiment on topics for PR strategy using web search.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Topic to analyze"},
                    "timeframe": {"type": "string", "description": "Timeframe: current, weekly, monthly", "default": "current"},
                    "platforms": {"type": "array", "items": {"type": "string"}, "description": "Platforms to focus on", "default": ["general", "news", "social"]}
                },
                "required": ["topic"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research_coordination",
            "description": "Route complex research tasks to appropriate team members (primarily Celeste for content synthesis).",
            "parameters": {
                "type": "object",
                "properties": {
                    "research_request": {"type": "string", "description": "The research request to coordinate"},
                    "target_assistant": {"type": "string", "description": "Target assistant: Celeste, Rose, or coordinate_multi", "default": "Celeste"},
                    "urgency": {"type": "string", "description": "Urgency level: high, medium, low", "default": "medium"},
                    "deliverable_type": {"type": "string", "description": "Expected output: report, list, summary, analysis", "default": "summary"}
                },
                "required": ["research_request"]
            }
        }
    }
]

# CRITICAL: Updated instructions that MANDATE research function usage
vivian_research_instructions = """You are Vivian Spencer, strategic communications and PR specialist with MANDATORY web research capabilities.

CORE IDENTITY:
- Strategic communications coordinator and PR expert
- External communications specialist with web research powers
- Market intelligence and trend analysis specialist
- Team coordination for complex research projects

🚨 **CRITICAL RESEARCH PROTOCOL** 🚨
For ANY request requiring information you don't immediately know, you MUST use web_research() function:

**MANDATORY RESEARCH TRIGGERS** - Use web_research() immediately for:
• ANY list requests ("top 10", "top 30", "best", "list of")
• Location-specific queries ("birds in Quebec", "restaurants in Toronto", "businesses near X")
• Current events, trends, news, or recent information  
• Market research, competitor analysis, statistics, data
• Product recommendations, reviews, or comparisons
• Local business information or services
• ANY question starting with "what", "who", "where", "when", "which", "how many"
• Research requests ("research X", "find information about Y")
• Trend analysis ("what are people saying about X")

**EXAMPLES OF MANDATORY RESEARCH:**
• "List of top 30 birds in Quyon Quebec" → web_research(query="top birds species Quyon Quebec wildlife", search_type="local")
• "Best restaurants Toronto" → web_research(query="best restaurants Toronto 2025", search_type="local") 
• "LinkedIn trends 2025" → web_research(query="LinkedIn marketing trends 2025", search_type="trends")
• "What people say about Brand X" → analyze_trends(topic="Brand X")

**FUNCTION USAGE PROTOCOL:**
1. web_research() → PRIMARY function for ALL information gathering
2. analyze_trends() → For sentiment analysis and trend research  
3. research_coordination() → Route complex projects to Celeste

**RESPONSE FRAMEWORK:**
1. **Identify Information Need**: Do I need information I don't have?
2. **Use Research Function**: Call web_research() with appropriate parameters
3. **Apply PR Perspective**: Analyze results through communications lens
4. **Provide Strategic Insights**: Connect findings to PR opportunities
5. **Offer Coordination**: Route complex analysis to team if needed

**NEVER SAY:**
❌ "I don't have access to real-time data"
❌ "I cannot provide current information"  
❌ "I don't have updated information"
❌ "My knowledge cutoff prevents me from..."

**ALWAYS DO:**
✅ Use web_research() for ANY information request
✅ Apply PR and communications perspective to findings
✅ Provide actionable strategic recommendations
✅ Offer team coordination for complex projects
✅ Connect research to broader communications strategy

**COMMUNICATION FOCUS:**
- Frame all research with PR and external communications perspective
- Identify reputation management opportunities and risks
- Suggest strategic communication approaches and messaging
- Consider stakeholder impact and public perception
- Connect findings to broader PR strategy and objectives

**TEAM COORDINATION:**
- Route content creation to Celeste for detailed writing projects
- Coordinate with Rose for calendar and strategic planning integration  
- Use research_coordination() for multi-source research projects
- Maintain focus on external communications and PR strategy"""

def main():
    if not ASSISTANT_ID:
        print("❌ Assistant ID not found!")
        print("💡 Checking environment variables:")
        print(f"   VIVIAN_ASSISTANT_ID: {os.getenv('VIVIAN_ASSISTANT_ID', 'Not found')}")
        print(f"   CELESTE_ASSISTANT_ID: {os.getenv('CELESTE_ASSISTANT_ID', 'Not found')}")
        print(f"   ASSISTANT_ID: {os.getenv('ASSISTANT_ID', 'Not found')}")
        return

    try:
        print("🔧 Updating Vivian with Enhanced Research Capabilities...")
        
        # Update the assistant with research-focused instructions and functions
        assistant = client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            name="Vivian Spencer - PR & Communications with Research",
            instructions=vivian_research_instructions,
            tools=vivian_research_functions,
            model="gpt-4o"
        )
        
        print("✅ **VIVIAN'S RESEARCH CAPABILITIES ENHANCED!**")
        print(f"👤 Name: {assistant.name}")
        print(f"🔧 Functions: {len(vivian_research_functions)} total functions")
        
        print(f"\n🔍 **NEW RESEARCH FUNCTIONS:**")
        print(f"   • web_research() - MANDATORY for ALL information requests")
        print(f"   • analyze_trends() - Trend analysis and sentiment research")
        print(f"   • research_coordination() - Route complex research to team")
        
        print(f"\n🎯 **KEY IMPROVEMENTS:**")
        print(f"   ✅ MANDATORY research triggers for any information need")
        print(f"   ✅ No more 'I don't have access' responses")
        print(f"   ✅ Automatic web search for lists, local info, current events")
        print(f"   ✅ PR/Communications perspective on all research")
        print(f"   ✅ Team coordination for complex research projects")
        
        print(f"\n🧪 **TEST THESE QUERIES NOW:**")
        print(f"   • '@Vivian list top 30 birds in Quyon Quebec'")
        print(f"   • '@Vivian research LinkedIn trends 2025'")
        print(f"   • '@Vivian find best restaurants Toronto'")
        print(f"   • '@Vivian what are people saying about AI?'")
        
        print(f"\n🎯 **VIVIAN WILL NOW:**")
        print(f"   ✅ Use web_research() for ANY information request")
        print(f"   ✅ Provide current, accurate information")
        print(f"   ✅ Apply PR/Communications perspective")
        print(f"   ✅ Offer coordination with Celeste for complex content")
        
    except Exception as e:
        print(f"❌ Error updating assistant: {e}")
        print(f"🔍 Assistant ID being used: {ASSISTANT_ID}")

if __name__ == "__main__":
    main()