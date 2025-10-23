import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()

intents.message_content = True
intents.members = True
#add more bot permissions if needed

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
