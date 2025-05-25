import discord
import os
from utils.openai_handler import get_openai_response

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Configure Discord intents
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🤖 Vivian is online as {client.user}")
    print(f"🔗 Connected to {len(client.guilds)} guild(s)")

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == client.user:
        return
    
    # Ignore messages that don't mention the bot (optional - remove if you want to respond to all messages)
    if not client.user.mentioned_in(message) and not isinstance(message.channel, discord.DMChannel):
        return

    print(f"📨 Message received from {message.author}: {message.content}")
    
    # Show typing indicator
    async with message.channel.typing():
        try:
            # Get response from OpenAI Assistant - pass user ID for per-user threads
            reply = await get_openai_response(message.content, user_id=message.author.id)
            
            # Discord has a 2000 character limit for messages
            if len(reply) > 2000:
                # Split long messages
                for i in range(0, len(reply), 2000):
                    await message.reply(reply[i:i+2000])
            else:
                await message.reply(reply)
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
            await message.reply("Sorry, I encountered an error while processing your message.")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("❌ DISCORD_TOKEN not found in environment variables")
        exit(1)
    
    try:
        client.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")