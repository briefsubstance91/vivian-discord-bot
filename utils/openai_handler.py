import openai
import os
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

print(f"🔧 Loaded ASSISTANT_ID: {ASSISTANT_ID}")
print(f"🔧 Loaded THREAD_ID: {THREAD_ID}")

def get_openai_response(user_message: str) -> str:
    if not ASSISTANT_ID or not THREAD_ID:
        error_msg = "Missing ASSISTANT_ID or THREAD_ID from environment."
        print(f"❌ {error_msg}")
        return error_msg

    try:
        print(f"📨 Sending to OpenAI (Thread: {THREAD_ID})")

        openai.beta.threads.messages.create(
            thread_id=THREAD_ID,
            role="user",
            content=user_message
        )

        run = openai.beta.threads.runs.create(
            thread_id=THREAD_ID,
            assistant_id=ASSISTANT_ID
        )

        while True:
            status = openai.beta.threads.runs.retrieve(run.id, thread_id=THREAD_ID)
            if status.status == "completed":
                break

        messages = openai.beta.threads.messages.list(thread_id=THREAD_ID)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                reply_text = msg.content[0].text.value
                print(f"💬 Vivian says: {reply_text}")
                return reply_text

        return "Vivian had no reply."

    except Exception as e:
        error_msg = f"❌ OpenAI error: {e}"
        print(error_msg)
        return f"Vivian crashed: {e}"
