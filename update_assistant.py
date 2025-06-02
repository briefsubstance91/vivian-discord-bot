from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Complete list of all functions (existing + new management functions)
all_functions = [
    # Existing Calendar Reading Functions
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Get today's calendar schedule and events",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tomorrow_schedule", 
            "description": "Get tomorrow's calendar schedule and events",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_upcoming_events",
            "description": "Get upcoming events for specified number of days",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days ahead to look for events", "default": 7}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_free_time",
            "description": "Find free time slots in calendar for specified duration",
            "parameters": {
                "type": "object", 
                "properties": {
                    "duration": {"type": "integer", "description": "Duration in minutes", "default": 60},
                    "date": {"type": "string", "description": "Date to search (YYYY-MM-DD)", "default": ""}
                }
            }
        }
    },
    # Existing Email Reading Functions  
    {
        "type": "function",
        "function": {
            "name": "search_emails",
            "description": "Search Gmail messages for specific content, sender, or topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query for emails"},
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
            "description": "Get recent emails from the inbox",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_results": {"type": "integer", "description": "Maximum emails to return", "default": 10}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email via Gmail",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email address"},
                    "subject": {"type": "string", "description": "Email subject line"},
                    "body": {"type": "string", "description": "Email body content"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    # NEW Calendar Management Functions
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": "Create a new calendar event",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title/summary"},
                    "start_datetime": {"type": "string", "description": "Start date and time in ISO format"},
                    "end_datetime": {"type": "string", "description": "End date and time in ISO format"},
                    "description": {"type": "string", "description": "Event description (optional)"},
                    "location": {"type": "string", "description": "Event location (optional)"},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "Attendee emails (optional)"}
                },
                "required": ["title", "start_datetime", "end_datetime"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_calendar_event",
            "description": "Update an existing calendar event",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "Calendar event ID to update"},
                    "title": {"type": "string", "description": "New event title (optional)"},
                    "start_datetime": {"type": "string", "description": "New start time (optional)"},
                    "end_datetime": {"type": "string", "description": "New end time (optional)"},
                    "description": {"type": "string", "description": "New description (optional)"},
                    "location": {"type": "string", "description": "New location (optional)"}
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": "Delete a calendar event",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "Calendar event ID to delete"}
                },
                "required": ["event_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "move_calendar_event",
            "description": "Move/reschedule a calendar event to a new time",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "Calendar event ID to move"},
                    "new_start_datetime": {"type": "string", "description": "New start date and time"},
                    "new_end_datetime": {"type": "string", "description": "New end time (optional)"}
                },
                "required": ["event_id", "new_start_datetime"]
            }
        }
    },
    # NEW Email Management Functions
    {
        "type": "function",
        "function": {
            "name": "delete_email",
            "description": "Delete an email permanently",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID to delete"}
                },
                "required": ["message_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "archive_email",
            "description": "Archive an email (remove from inbox)",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID to archive"}
                },
                "required": ["message_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "reply_to_email",
            "description": "Reply to an email",
            "parameters": {
                "type": "object",
                "properties": {
                    "message_id": {"type": "string", "description": "Gmail message ID to reply to"},
                    "reply_body": {"type": "string", "description": "The reply message content"},
                    "include_original": {"type": "boolean", "description": "Include original message", "default": True}
                },
                "required": ["message_id", "reply_body"]
            }
        }
    }
]

# Update the assistant
try:
    assistant = client.beta.assistants.update(
        assistant_id=ASSISTANT_ID,
        tools=all_functions
    )
    print(f"✅ Assistant updated successfully!")
    print(f"📧 Email functions: search_emails, get_recent_emails, send_email, delete_email, archive_email, reply_to_email")
    print(f"📅 Calendar functions: get_today_schedule, get_tomorrow_schedule, get_upcoming_events, find_free_time, create_calendar_event, update_calendar_event, delete_calendar_event, move_calendar_event")
    print(f"🎯 Total functions: {len(all_functions)}")
    
except Exception as e:
    print(f"❌ Error updating assistant: {e}")
