import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

intents = discord.Intents.default()

intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
