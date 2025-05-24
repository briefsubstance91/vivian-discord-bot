import openai
import os
import asyncio
import time
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")

print(f"🔧 Loaded ASSISTANT_ID: {ASSISTANT_ID}")
print(f"🔧 Loaded THREAD_ID: {THREAD_ID}")

async def get_openai_response(user_message: str) -> str:
    """
    Send a message to OpenAI Assistant and get response
    """
    if not ASSISTANT_ID or not THREAD_ID:
        return "❌ Missing ASSISTANT_ID or THREAD_ID from environment variables."
    
    if not os.getenv("OPENAI_API_KEY"):
        return "❌ Missing OPENAI_API_KEY from environment variables."

    try:
        print(f"📨 Sending message to OpenAI Assistant (Thread: {THREAD_ID})")
        
        # Add message to thread
        message = client.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=user_message
        )
        
        print(f"✅ Message added to thread: {message.id}")
        
        # Create and run the assistant
        run = client.beta.threads.runs.create(
            thread_id=THREAD_ID,
            assistant_id=ASSISTANT_ID
        )
        
        print(f"🏃 Run created: {run.id}")
        
        # Wait for completion with timeout
        max_wait_time = 60  # 60 seconds timeout
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=THREAD_ID,
                run_id=run.id
            )
            
            print(f"🔄 Run status: {run_status.status}")
            
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                return f"❌ Assistant run failed: {run_status.last_error}"
            elif run_status.status == "expired":
                return "❌ Assistant run expired (took too long)"
            
            # Wait a bit before checking again
            await asyncio.sleep(1)
        else:
            return "❌ Assistant response timed out"
        
        # Get the latest messages
        messages = client.beta.threads.messages.list(
            thread_id=THREAD_ID,
            limit=10
        )
        
        # Find the most recent assistant message
        for msg in messages.data:
            if msg.role == "assistant" and msg.run_id == run.id:
                if msg.content and len(msg.content) > 0:
                    # Handle different content types
                    if hasattr(msg.content[0], 'text'):
                        response_text = msg.content[0].text.value
                        print(f"✅ Got response: {response_text[:100]}...")
                        return response_text
                    else:
                        return str(msg.content[0])
        
        return "❌ No response found from assistant"

    except openai.RateLimitError:
        return "❌ OpenAI rate limit exceeded. Please try again later."
    except openai.APIConnectionError:
        return "❌ Failed to connect to OpenAI. Please check your internet connection."
    except openai.AuthenticationError:
        return "❌ OpenAI authentication failed. Please check your API key."
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return f"❌ An error occurred: {str(e)}"


def create_new_thread():
    """
    Create a new thread for the assistant (utility function)
    """
    try:
        thread = client.beta.threads.create()
        print(f"✅ New thread created: {thread.id}")
        return thread.id
    except Exception as e:
        print(f"❌ Failed to create thread: {e}")
        return None