import os
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")

async def get_openai_response(user_message: str) -> str:
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

        for _ in range(30):  # Wait up to ~30 seconds
            run_status = client.beta.threads.runs.retrieve(
                thread_id=THREAD_ID,
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

        messages = client.beta.threads.messages.list(thread_id=THREAD_ID)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                print(f"✅ Got response: {msg.content[0].text.value}")
                return msg.content[0].text.value

        return "⚠️ No assistant response found."

    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return "An error occurred while communicating with the assistant."
