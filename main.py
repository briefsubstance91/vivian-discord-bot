import discord
import os
from dotenv import load_dotenv
from utils.openai_handler import get_openai_response

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Vivian is online as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    print(f"Message received: {message.content}")
    await message.channel.typing()

    reply = get_openai_response(message.content)
    await message.reply(reply)

client.run(DISCORD_TOKEN)