import openai
import os
from assistant_config import ASSISTANT_ID, THREAD_ID

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_openai_response(user_message: str) -> str:
    try:
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
        print(f"OpenAI error: {e}")
        return "Something went wrong talking to Vivian."