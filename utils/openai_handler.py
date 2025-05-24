import os
import time
import openai
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

async def get_openai_response(user_message: str) -> str:
    if not ASSISTANT_ID or not THREAD_ID:
        return "❌ ASSISTANT_ID or THREAD_ID not set."

    try:
        print(f"📨 Sending message to OpenAI Assistant (Thread: {THREAD_ID})")

        # Check for active runs
        existing_runs = openai.beta.threads.runs.list(thread_id=THREAD_ID).data
        if any(run.status in ["queued", "in_progress", "requires_action"] for run in existing_runs):
            return "⏳ Assistant is still processing a previous request. Please wait."

        # Add user message to thread
        message = openai.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=user_message
        )
        print(f"✅ Message added to thread: {message.id}")

        # Create a new run
        run = openai.beta.threads.runs.create(
            thread_id=THREAD_ID,
            assistant_id=ASSISTANT_ID
        )
        print(f"🏃 Run created: {run.id}")

        # Poll run status
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=THREAD_ID,
                run_id=run.id
            )
            print(f"🔄 Run status: {run_status.status}")
            if run_status.status == "completed":
                break
            elif run_status.status in ["failed", "cancelled"]:
                return f"❌ Assistant failed to complete run (status: {run_status.status})"
            time.sleep(1)

        # Fetch the last assistant message
        messages = openai.beta.threads.messages.list(thread_id=THREAD_ID)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                reply = msg.content[0].text.value
                print(f"✅ Got response: {reply}")
                return reply

        return "❌ No assistant reply found."

    except openai.OpenAIError as e:
        return f"❌ OpenAI error: {str(e)}"
    except Exception as e:
        return f"❌ Unexpected error: {str(e)}"
