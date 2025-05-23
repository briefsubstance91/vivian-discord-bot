import openai
import os
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")

print(f"🔧 Loaded ASSISTANT_ID: {ASSISTANT_ID}")
print(f"🔧 Loaded THREAD_ID: {THREAD_ID}")

def get_openai_response(user_message: str) -> str:
    if not ASSISTANT_ID or not THREAD_ID:
        return "Missing ASSISTANT_ID or THREAD_ID from environment."

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
                return msg.content[0].text.value

        return "Vivian had no reply."

    except Exception as e:
        return f"Vivian crashed: {e}"
