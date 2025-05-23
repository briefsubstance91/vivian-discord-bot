from dotenv import load_dotenv
import os

load_dotenv()

ASSISTANT_ID = os.getenv("ASSISTANT_ID")
THREAD_ID = os.getenv("THREAD_ID")

print(f"🔧 Loaded ASSISTANT_ID: {ASSISTANT_ID}")
print(f"🔧 Loaded THREAD_ID: {THREAD_ID}")

