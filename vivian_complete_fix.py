#!/usr/bin/env python3
"""
VIVIAN SPENCER - COMPLETE FIXED SETUP  
PR & Communications Specialist with File Search + Code Interpreter + Functions
Preserves all tools properly
"""

from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Vivian's COMPLETE functions with all tools preserved
vivian_complete_functions = [
    # Core web search
    {
        "name": "web_search",
        "description": "Search the web for current information, trends, news, and PR insights.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "search_type": {"type": "string", "description": "Type: general, news, local, trends", "default": "general"},
                "num_results": {"type": "integer", "description": "Number of results (1-5)", "default": 3}
            },
            "required": ["query"]
        }
    },
    # Calendar functions
    {
        "name": "get_today_schedule",
        "description": "Get today's calendar schedule for PR planning.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_upcoming_events", 
        "description": "Get upcoming calendar events for communications planning.",
        "parameters": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Days ahead (1-14)", "default": 7}
            },
            "required": []
        }
    },
    # Email functions
    {
        "name": "search_emails",
        "description": "Search Gmail for emails and communications.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Email search query"},
                "max_results": {"type": "integer", "description": "Max results (1-10)", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_recent_emails",
        "description": "Get recent emails for communications review.",
        "parameters": {
            "type": "object", 
            "properties": {
                "max_results": {"type": "integer", "description": "Max results (1-10)", "default": 10}
            },
            "required": []
        }
    }
]

# Vivian's complete instructions
vivian_complete_instructions = """You are Vivian Spencer, PR and communications specialist with comprehensive digital tools and research capabilities.

📱 **YOUR ROLE**: PR Strategy + External Communications + Digital Research + Content Analysis

✨ **ENHANCED CAPABILITIES:**
• File Search: Access PR documents, media lists, communication templates
• Code Interpreter: Analyze social media metrics, engagement data, trend analysis
• Custom Functions: Web research, calendar coordination, email management

🎯 **FUNCTION USAGE PROTOCOL:**

**FOR INFORMATION REQUESTS:**
• Use web_search() for current trends, news, competitor analysis
• Focus on PR-relevant sources and communications insights
• Research social media trends and digital marketing strategies

**FOR CALENDAR COORDINATION:**
• Use get_today_schedule() for daily PR planning
• Use get_upcoming_events() for communications timeline planning
• Coordinate PR campaigns with scheduled events

**FOR EMAIL MANAGEMENT:**
• Use search_emails() to find specific communications
• Use get_recent_emails() for communications audit
• Manage external stakeholder correspondence

🔍 **DATA ANALYSIS WITH CODE INTERPRETER:**
• Social media metrics and engagement analysis
• PR campaign performance tracking
• Trend data visualization and insights
• Media coverage analysis and reporting

📊 **DOCUMENT MANAGEMENT WITH FILE SEARCH:**
• Access PR templates and communication guidelines
• Reference media contact lists and press materials
• Analyze previous campaign documents and results

💬 **COMMUNICATION STYLE:**
• Strategic PR thinking with data-driven insights
• Professional external communications focus
• Trend-aware and digitally native approach
• Crisis communication and reputation management ready

🎯 **RESPONSE FRAMEWORK:**
1. **Research First**: Use web_search() for current information
2. **Strategic Analysis**: Apply PR lens to findings
3. **Data Integration**: Use Code Interpreter for metrics when relevant
4. **Actionable Recommendations**: Provide clear PR strategy and next steps
5. **Timeline Awareness**: Factor in calendar and email context

✅ **ALWAYS PROVIDE:**
• Current, research-backed PR recommendations
• Strategic communications perspective
• Digital trend awareness and social media insights
• Professional stakeholder management advice
• Crisis-ready thinking and reputation protection

Keep responses under 1200 characters for Discord. Focus on strategic PR guidance with current market intelligence."""

def create_complete_vivian():
    """Create Vivian with all tools preserved - File Search + Code Interpreter + Functions"""
    try:
        print("📱 Creating Complete Vivian Spencer - PR & Communications with All Tools...")
        
        # BUILD COMPLETE TOOLS ARRAY - Preserves all toggles
        complete_tools = [
            {"type": "file_search"},        # Keeps File Search toggle ON
            {"type": "code_interpreter"}    # Keeps Code Interpreter toggle ON
        ]
        
        # Add all custom functions
        for func in vivian_complete_functions:
            complete_tools.append({"type": "function", "function": func})
        
        # Create assistant with ALL tools
        assistant = client.beta.assistants.create(
            name="Vivian Spencer - PR & Communications (Complete)",
            instructions=vivian_complete_instructions,
            tools=complete_tools,
            model="gpt-4o"
        )
        
        print("✅ **COMPLETE VIVIAN CREATED WITH ALL TOOLS!**")
        print(f"👤 Name: {assistant.name}")
        print(f"🆔 Assistant ID: {assistant.id}")
        print(f"🔧 Total Tools: {len(complete_tools)}")
        
        print(f"\n📱 **VIVIAN'S COMPLETE TOOLS:**")
        print(f"   ✅ File Search - PR documents & templates access")
        print(f"   ✅ Code Interpreter - Social metrics & data analysis")
        print(f"   ✅ web_search() - Current trends & PR research")
        print(f"   ✅ get_today_schedule() - Daily PR planning")
        print(f"   ✅ get_upcoming_events() - Communications timeline")
        print(f"   ✅ search_emails() - Email management")
        print(f"   ✅ get_recent_emails() - Communications audit")
        
        print(f"\n📊 **ENHANCED CAPABILITIES:**")
        print(f"   ✅ Social media metrics analysis (Code Interpreter)")
        print(f"   ✅ PR document management (File Search)")
        print(f"   ✅ Real-time trend research (Web Search)")
        print(f"   ✅ Communications calendar integration")
        
        print(f"\n📝 **SAVE THIS ASSISTANT ID:**")
        print(f"   VIVIAN_ASSISTANT_ID={assistant.id}")
        print(f"   Add this to your Railway environment variables!")
        
        return assistant.id
        
    except Exception as e:
        print(f"❌ Error creating complete Vivian: {e}")
        return None

def update_existing_vivian(existing_id):
    """Update existing Vivian with all tools preserved"""
    try:
        print(f"🔄 Updating existing Vivian: {existing_id}")
        
        # BUILD COMPLETE TOOLS ARRAY
        complete_tools = [
            {"type": "file_search"},        # Preserves File Search
            {"type": "code_interpreter"}    # Preserves Code Interpreter
        ]
        
        # Add all custom functions
        for func in vivian_complete_functions:
            complete_tools.append({"type": "function", "function": func})
        
        # Update with ALL tools preserved
        assistant = client.beta.assistants.update(
            assistant_id=existing_id,
            name="Vivian Spencer - PR & Communications (Fixed)",
            instructions=vivian_complete_instructions,
            tools=complete_tools,
            model="gpt-4o"
        )
        
        print("✅ **VIVIAN UPDATED WITH ALL TOOLS PRESERVED!**")
        print(f"🔧 Tools count: {len(complete_tools)}")
        print(f"✅ File Search & Code Interpreter will stay ON")
        
        return assistant.id
        
    except Exception as e:
        print(f"❌ Error updating Vivian: {e}")
        return None

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment variables")
        exit(1)
    
    print("📱 VIVIAN COMPLETE SETUP")
    print("=" * 50)
    
    choice = input("Create new Vivian (n) or update existing (u)? [n/u]: ").lower()
    
    if choice == 'u':
        existing_id = input("Enter existing Vivian Assistant ID: ").strip()
        if existing_id:
            update_existing_vivian(existing_id)
        else:
            print("❌ No Assistant ID provided")
    else:
        create_complete_vivian()
