import nextcord as discord
from nextcord.ext import commands
from dotenv import load_dotenv
import random, math, time, asyncio, os
from m_functions import *
from m_vars import *

print("Starting bot with discord.py v" + discord.__version__)
load_dotenv()
TOKEN = os.getenv('TOKEN')														#Actual bot token

base_activity = discord.Activity(type=discord.ActivityType.listening, name="!help")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", status="online", activity=base_activity)

@bot.event																		#called at bot startup
async def on_ready():
	global on_check
	if on_check is not True:
		on_check = True
		guild_id = 710657083246379120
		guild = bot.get_guild(guild_id)
		chan = discord.utils.get(guild.text_channels, name="general")
		await bot.change_presence(activity=base_activity, status="online")
		await chan.send("Hello")
		timer = Timer(globalTime, start_timer, args={'chan':chan})

bot.run(TOKEN)