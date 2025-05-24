import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

response = openai.Thread.create()
print("✅ New Thread ID:", response["id"])

