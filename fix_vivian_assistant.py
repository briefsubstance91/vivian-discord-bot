#!/usr/bin/env python3
"""
Fix Vivian Assistant - Update with proper function definitions and instructions
Run this to sync your OpenAI assistant with your local code
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Calendar and Email functions that exactly match your local code
vivian_functions = [
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Get today's calendar schedule. Use when user asks: 'what's on my calendar today', 'today's schedule', 'what do I have today', etc.",
            "parameters": {
                "type": "object", 
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tomorrow_schedule", 
            "description": "Get tomorrow's calendar schedule. Use when user asks: 'tomorrow's schedule', 'what's happening tomorrow', 'tomorrow's events', etc.",
            "parameters": {
                "type": "object", 
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Get upcoming events for multiple days. Use when user asks: 'this week', 'next few days', 'upcoming schedule', 'week ahead', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer", 
                        "description": "Number of days ahead (7 for week, 3-5 for few days, 14 for two weeks)", 
                        "default": 7
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_free_time",
            "description": "Find available time slots. Use when user asks: 'when am I free', 'find time for meeting', 'available slots', 'schedule new meeting', etc.",
            "parameters": {
                "type": "object", 
                "properties": {
                    "duration": {
                        "type": "integer", 
                        "description": "Meeting duration in minutes (30, 60, 90, 120)", 
                        "default": 60
                    },
                    "date": {
                        "type": "string", 
                        "description": "Date to search (YYYY-MM-DD format), leave empty for today", 
                        "default": ""
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search Gmail for emails. Use when user asks: 'find emails about X', 'emails from John', 'search for messages', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string", 
                        "description": "Gmail search query (keywords, sender name, from:email@domain.com, subject terms)"
                    },
                    "max_results": {
                        "type": "integer", 
                        "description": "Maximum emails to return", 
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_emails",
            "description": "Get recent emails from inbox. Use when user asks: 'check my emails', 'recent messages', 'what's in my inbox', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {
                        "type": "integer", 
                        "description": "Number of recent emails to show", 
                        "default": 10
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email. Use when user asks: 'send email to X', 'compose message', 'email someone about Y', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string", 
                        "description": "Recipient email address"
                    },
                    "subject": {
                        "type": "string", 
                        "description": "Email subject line"
                    },
                    "body": {
                        "type": "string", 
                        "description": "Email body content"
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    }
]

# Enhanced instructions for Vivian Spencer
vivian_instructions = """You are Vivian Spencer, a strategic productivity assistant specializing in PR, social media, and external communications management.

CORE IDENTITY:
- Strategic external communications coordinator
- PR and social media management expert
- Pop culture and news awareness
- Email management and outreach specialist
- Focus on public image and strategic messaging

CRITICAL FUNCTION USAGE RULES:
🚨 **MANDATORY**: For ANY calendar or email question, you MUST use the appropriate function FIRST.

Calendar Function Triggers:
- "calendar", "schedule", "today", "tomorrow", "this week", "upcoming", "free time", "available", "when", "meeting time"
- Examples: "what's on my calendar" → get_today_schedule()
- "tomorrow's schedule" → get_tomorrow_schedule()
- "this week" → get_upcoming_events(days=7)
- "when am I free" → find_free_time()

Email Function Triggers:
- "email", "inbox", "messages", "check emails", "find emails", "search", "send"
- Examples: "check my emails" → get_recent_emails()
- "emails about project" → search_emails(query="project")
- "send email to John" → send_email() (ask for details)

RESPONSE PROTOCOL:
1. **Always use functions for calendar/email queries** - never guess or assume
2. **Base your response entirely on function results** - if function says "no events", that's the truth
3. **Never fabricate calendar events or email information**
4. **Present function results first, then add strategic insights**

RESPONSE STYLE:
- Start with factual function results
- Add strategic PR/communications perspective
- Suggest optimizations for productivity and image management
- Keep tone professional but approachable
- Think like a strategic communications advisor

CONVERSATION MEMORY:
- Remember user preferences and communication patterns
- Build on previous scheduling discussions
- Reference past strategic advice when relevant

NEVER DO:
❌ Invent calendar events if function returns "no events"
❌ Make assumptions about emails without using functions
❌ Give generic responses when functions are available
❌ Ignore function results in favor of training data

ALWAYS DO:
✅ Use appropriate function for every calendar/email question
✅ Present actual function results as primary information
✅ Add strategic communications insights after facts
✅ Maintain focus on external communications and PR strategy"""

def main():
    if not ASSISTANT_ID:
        print("❌ ASSISTANT_ID not found in environment variables!")
        print("💡 Make sure your .env file has ASSISTANT_ID set")
        return

    try:
        print("🔄 Updating Vivian Spencer assistant...")
        
        # Update the assistant with new instructions and functions
        assistant = client.beta.assistants.update(
            assistant_id=ASSISTANT_ID,
            name="Vivian Spencer - PR & Communications Assistant",
            instructions=vivian_instructions,
            tools=vivian_functions,
            model="gpt-4o"
        )
        
        print("✅ **VIVIAN ASSISTANT UPDATED SUCCESSFULLY!**")
        print(f"👤 Name: {assistant.name}")
        print(f"🔧 Functions: {len(vivian_functions)} calendar & email functions")
        print(f"📋 Function List:")
        for tool in vivian_functions:
            func_name = tool['function']['name']
            func_desc = tool['function']['description'].split('.')[0]
            print(f"   • {func_name} - {func_desc}")
        
        print(f"\n🎯 **KEY IMPROVEMENTS:**")
        print(f"   ✅ Strict function usage requirements")
        print(f"   ✅ No more fabricated calendar events")
        print(f"   ✅ Clear natural language → function mapping")
        print(f"   ✅ PR/communications strategic focus")
        print(f"   ✅ Better conversation memory handling")
        
        print(f"\n📝 **TEST QUERIES TO TRY:**")
        print(f"   • 'What's on my calendar today?'")
        print(f"   • 'Check my recent emails'")
        print(f"   • 'What's my schedule this week?'")
        print(f"   • 'When am I free for a 1-hour meeting?'")
        
    except Exception as e:
        print(f"❌ Error updating assistant: {e}")
        print(f"🔍 Assistant ID being used: {ASSISTANT_ID}")
        print(f"💡 Double-check your OpenAI API key and Assistant ID")

if __name__ == "__main__":
    main()