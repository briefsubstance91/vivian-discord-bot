import openai
import os
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_openai_response(user_message: str) -> str:
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

        # Wait for run to complete
        while True:
            status = openai.beta.threads.runs.retrieve(run.id, thread_id=THREAD_ID)
            if status.status == "completed":
                break

        # Get the assistant's latest message
        messages = openai.beta.threads.messages.list(thread_id=THREAD_ID)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                reply_text = msg.content[0].text.value
                print(f"💬 Vivian says: {reply_text}")
                return reply_text

        return "Vivian had no reply."

    except Exception as e:
        print(f"❌ OpenAI error: {e}")
        return "Something went wrong talking to Vivian."
