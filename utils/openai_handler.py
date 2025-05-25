import os
import asyncio
from openai import OpenAI
from datetime import datetime, timedelta

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

# Store user threads in memory (per-user threads, NOT static)
user_threads = {}

def should_refresh_thread(thread_data):
    """Check if thread should be refreshed (24 hours old or 50+ messages)"""
    max_age = timedelta(hours=24)
    max_messages = 50
    
    return (datetime.now() - thread_data['created'] > max_age) or \
           (thread_data['message_count'] > max_messages)

def get_or_create_thread(user_id):
    """Get existing thread for user or create a new one"""
    thread_key = f"thread_{user_id}"
    
    # Check if thread should be refreshed
    if thread_key in user_threads and should_refresh_thread(user_threads[thread_key]):
        print(f"🔄 Refreshing thread for user {user_id}")
        del user_threads[thread_key]
    
    # Create new thread if needed
    if thread_key not in user_threads:
        thread = client.beta.threads.create()
        user_threads[thread_key] = {
            'id': thread.id,
            'created': datetime.now(),
            'message_count': 0
        }
        print(f"✨ Created new thread: {thread.id} for user {user_id}")
    
    return user_threads[thread_key]

def should_give_detailed_response(user_message):
    """Check if user is asking for a detailed/comprehensive response"""
    detail_triggers = [
        'deep dive', 'detailed', 'comprehensive', 'tell me more', 'elaborate',
        'break it down', 'full breakdown', 'in depth', 'thorough', 'complete',
        'everything about', 'walk me through', 'explain fully'
    ]
    
    return any(trigger in user_message.lower() for trigger in detail_triggers)

def format_for_discord(response, is_detailed=False):
    """Clean up response for Discord formatting"""
    
    # Remove excessive line breaks
    response = response.replace('\n\n\n', '\n\n')
    response = response.replace('\n\n\n\n', '\n\n')
    
    # Remove bold from every concept (too much bolding)
    bold_count = response.count('**')
    if bold_count > 6:  # More than 3 bold phrases
        # Keep only the first 2 bold phrases
        parts = response.split('**')
        new_response = parts[0]
        bold_used = 0
        for i in range(1, len(parts)):
            if bold_used < 4:  # Keep first 2 bold phrases (4 asterisks)
                new_response += '**' + parts[i]
                bold_used += 1
            else:
                new_response += parts[i]
        response = new_response
    
    # Different length limits based on detail level
    if is_detailed:
        max_length = 3000  # Allow longer responses when details requested
    else:
        max_length = 1200  # Keep casual responses tight
    
    if len(response) > max_length:
        # Find a good breaking point
        sentences = response.split('. ')
        truncated = ""
        for sentence in sentences:
            if len(truncated + sentence + '. ') < (max_length - 100):
                truncated += sentence + '. '
            else:
                if is_detailed:
                    truncated += "\n\n*This is just the foundation - want me to go deeper on any specific aspect?*"
                else:
                    truncated += "\n\n*Want the detailed breakdown?*"
                break
        response = truncated
    
    return response.strip()

def is_generic_response(response):
    """Check if response seems generic/wrong"""
    generic_phrases = [
        'ops crew',
        'suggest some options',
        'provide more details',
        'tailor the suggestions',
        'aligned with.*style and functionality'
    ]
    
    return any(phrase.lower() in response.lower() for phrase in generic_phrases)

def is_too_formal(response):
    """Check if response is too formal/listy for Discord"""
    formal_indicators = [
        response.count('\n\n') > 6,  # Too many paragraph breaks
        response.count('1.') > 0 and response.count('6.') > 0,  # Long numbered lists
        len(response) > 2000,  # Too long
        'responsibilities and tasks' in response.lower(),  # Too corporate
    ]
    
    return any(formal_indicators)

async def retry_with_context(thread_id, original_message):
    """Retry with explicit Vivian Spencer context"""
    try:
        # Add context message emphasizing Discord style
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f'As Vivian Spencer, respond to "{original_message}" in a conversational, strategic way. Keep it under 1500 characters, no numbered lists, and end with an insightful question. You\'re having coffee with a client, not writing a report.'
        )
        
        # Create run
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )
        
        # Wait for completion (shorter timeout for retry)
        for _ in range(15):
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                for msg in reversed(messages.data):
                    if msg.role == "assistant":
                        return msg.content[0].text.value
                break
            elif run_status.status in ["failed", "requires_action"]:
                break
                
            await asyncio.sleep(1)
        
        return None
    except Exception as error:
        print(f"❌ Recovery attempt failed: {error}")
        return None

async def get_openai_response(user_message: str, user_id: int) -> str:
    try:
        # TEMPORARY FIX: Force new thread every message to avoid caching issues
        # This ensures each question gets a fresh response instead of cached answers
        # Remove this line once OpenAI fixes their caching behavior
        user_threads.clear()
        
        # Get or create thread for this specific user (NOT static thread)
        thread_data = get_or_create_thread(user_id)
        thread_id = thread_data['id']
        
        print(f"📨 Sending message to OpenAI Assistant (Thread: {thread_id}, User: {user_id})")
        
        # Clean the user message (remove bot mentions)
        clean_message = user_message.replace(f'<@1373036719930085567>', '').strip()
        
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=clean_message
        )
        
        # Increment message count
        thread_data['message_count'] += 1
        print(f"✅ Message added to thread: {message.id}")
        
        # Check if user wants detailed response
        wants_detail = should_give_detailed_response(clean_message)
        
        # Create run with dynamic instructions based on request type
        if wants_detail:
            instructions = "You are Vivian Spencer. CRITICAL: Even for detailed breakdowns, maintain your conversational strategic voice. NEVER write like a productivity blog or textbook. Write like you're having an in-depth coffee conversation with a strategic friend. NO numbered lists, NO formal headers, NO 'Let's dive into' language."
            additional = "ABSOLUTELY FORBIDDEN: 'Let's dive into', 'First, start by', numbered lists, bullet points, textbook language. REQUIRED: Flow like the casual responses but longer. Use phrases like 'Here's what I see working', 'The pattern I notice', 'What's interesting is'. Stay conversational even when comprehensive."
        else:
            instructions = "You are Vivian Spencer. Keep this conversational and strategic (800-1200 chars). Write like you're texting a smart friend - no formal language or corporate speak. Weave insights together naturally. End with strategic perspective or question."
            additional = "Sound like Vivian - strategic, composed, insightful. Avoid phrases like 'The key is' or 'It's also smart to'. More like 'Here's what I see working' or 'The pattern I notice'. Strategic advisor voice, not generic advice."

        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions=instructions,
            additional_instructions=additional
        )
        
        print(f"🏃 Run created: {run.id}")
        
        # Wait for completion
        for _ in range(30):  # Wait up to ~30 seconds
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            print(f"🔄 Run status: {run_status.status}")
            
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                raise Exception("❌ Run failed.")
            elif run_status.status == "requires_action":
                raise Exception("⚠️ Run requires action (not handled).")
            await asyncio.sleep(1)
        else:
            raise TimeoutError("⏱️ Timed out waiting for assistant to complete.")
        
        # Get response
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                response = msg.content[0].text.value
                print(f"✅ Got response: {response[:100]}...")
                
                # Check if response seems generic/wrong
                if is_generic_response(response):
                    print("⚠️  Detected generic response, attempting recovery...")
                    recovery_response = await retry_with_context(thread_id, clean_message)
                    if recovery_response:
                        print("✅ Recovery successful")
                        return format_for_discord(recovery_response, wants_detail)
                    else:
                        return "I seem to be having technical difficulties. Could you rephrase your question about communications strategy?"
                
                # Check if response is too formal for Discord
                elif is_too_formal(response):
                    print("⚠️  Response too formal for Discord, attempting recovery...")
                    recovery_response = await retry_with_context(thread_id, clean_message)
                    if recovery_response:
                        print("✅ Recovery successful - more conversational")
                        return format_for_discord(recovery_response, wants_detail)
                
                # Apply Discord formatting and return
                return format_for_discord(response, wants_detail)
        
        return "⚠️ No assistant response found."
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "An error occurred while communicating with the assistant."