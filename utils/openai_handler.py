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

async def retry_with_context(thread_id, original_message):
    """Retry with explicit Vivian Spencer context"""
    try:
        # Add context message
        client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f'As Vivian Spencer, my strategist and style architect, please respond to: "{original_message}". Remember your role - you see patterns, opportunities, and what\'s on the horizon. Speak with composed insight.'
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
        
        # Create run with explicit Vivian Spencer instructions
        run = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions="You are Vivian Spencer, the user's strategist and style architect. You see patterns, opportunities, and what's just on the horizon. You speak like someone who knows their angles, edits for clarity, and trusts their own taste. Your tone is composed and insightful.",
            additional_instructions="Stay in character as Vivian Spencer. Respond with strategic insight about the question asked."
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
                        return recovery_response
                    else:
                        return "I seem to be having technical difficulties. Could you rephrase your question about communications strategy?"
                
                return response
        
        return "⚠️ No assistant response found."
        
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "An error occurred while communicating with the assistant."