from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

response = client.beta.threads.create()
print("✅ New Thread ID:", response.id)
