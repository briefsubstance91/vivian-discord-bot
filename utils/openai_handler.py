from openai import OpenAI
import os
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")

print(f"🔧 Loaded ASSISTANT_ID: {ASSISTANT_ID}")
print(f"🔧 Loaded THREAD_ID: {THREAD_ID}")

async def get_openai_response(user_message: str) -> str:
    if not ASSISTANT_ID or not THREAD_ID:
        return "❌ Missing ASSISTANT_ID or THREAD_ID in environment."

    try:
        print(f"📨 Sending message to OpenAI Assistant (Thread: {THREAD_ID})")

        message = client.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=user_message
        )
        print(f"✅ Message added to thread: {message.id}")

        run = client.beta.threads.runs.create(
            thread_id=THREAD_ID,
            assistant_id=ASSISTANT_ID
        )
        print(f"🏃 Run created: {run.id}")

        # Wait for run to complete
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=THREAD_ID, run_id=run.id)
            print(f"🔄 Run status: {run_status.status}")
            if run_status.status == "completed":
                break
            elif run_status.status == "requires_action":
                return "❌ Assistant needs action from tool call (not yet supported in this version)."
            time.sleep(1)

        # Retrieve messages and find response from current run
        messages = client.beta.threads.messages.list(thread_id=THREAD_ID, limit=10)

        for msg in messages.data:
            if msg.role == "assistant" and msg.run_id == run.id:
                response_text = msg.content[0].text.value
                print(f"✅ Got response: {response_text}")
                return response_text

        return "❌ No assistant reply found."

    except Exception as e:
        error_msg = f"❌ An error occurred: {e}"
        print(error_msg)
        return error_msg
