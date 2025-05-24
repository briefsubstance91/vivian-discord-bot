import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

async def get_openai_response(user_message: str) -> str:
    if not ASSISTANT_ID or not THREAD_ID:
        error_msg = "Missing ASSISTANT_ID or THREAD_ID from environment."
        print(f"❌ {error_msg}")
        return error_msg

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

        while True:
            status = client.beta.threads.runs.retrieve(run.id, thread_id=THREAD_ID)
            print(f"🔄 Run status: {status.status}")

            if status.status == "completed":
                break
            elif status.status == "requires_action":
                tool_calls = status.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []

                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)

                    print(f"🛠️ Tool requested: {tool_name} with args {arguments}")
                    dummy_output = f"Tool `{tool_name}` was called with arguments {arguments}"
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": dummy_output
                    })

                client.beta.threads.runs.submit_tool_outputs(
                    thread_id=THREAD_ID,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )

        messages = client.beta.threads.messages.list(thread_id=THREAD_ID)
        for msg in reversed(messages.data):
            if msg.role == "assistant":
                reply_text = msg.content[0].text.value
                print(f"✅ Got response: {reply_text}")
                return reply_text

        return "Vivian had no reply."

    except Exception as e:
        error_msg = f"❌ OpenAI error: {e}"
        print(error_msg)
        return f"Vivian crashed: {e}"
