from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

thread = client.beta.threads.create()
print("✅ New Thread ID:", thread.id)

