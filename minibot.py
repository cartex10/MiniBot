# MiniBot v1.3
#
# TODO: 
#		fix messages not deleting on command use
#		randomly changing status/presence
#		make high priorities ping user
#		reminders for dates in the future, ie doctors appointments
#		investigate multiple notifications
#		mute command
#
import nextcord as discord
from nextcord.ext import commands
from dotenv import load_dotenv
import random, math, time, asyncio, os
from m_functions import *
from m_vars import *

print("Starting bot with discord.py v" + discord.__version__)
load_dotenv()
TOKEN = os.getenv('TOKEN')														#Actual bot token
#TOKEN = os.getenv('TEST_TOKEN')
GUILD = int(os.getenv('GUILD'))

base_activity = discord.Activity(type=discord.ActivityType.listening, name="!help")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", status="online", activity=base_activity)

@bot.event																		#called at bot startup
async def on_ready():
	global on_check
	global notifyTime
	global mangaTime
	if on_check is not True:
		on_check = True
		guild = bot.get_guild(GUILD)
		await bot.change_presence(activity=base_activity, status="online")
		chan = discord.utils.get(guild.text_channels, name="general")
		await chan.send("```Waking MiniBot!```")
		await chan.send("Hello! I'm getting ready to help you out!")
		await checkConnection(chan)
		chan = discord.utils.get(guild.text_channels, name="notifications")
		n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})
		chan = discord.utils.get(guild.text_channels, name="manga-updates")
		m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})

@bot.slash_command()
async def reminders(interaction):
	global con
	cursor = await getReminders(-1)
	await interaction.send("temp")
	vw = reminderView(bot, await interaction.original_message(), interaction.user, cursor)
	await interaction.edit_original_message(view=vw)
	await vw.update()

@bot.slash_command()
async def messages(interaction):
	global con
	cursor = await getMessages(-1)
	await interaction.send("temp")
	view = messageView(bot, await interaction.original_message(),interaction.user, cursor)
	await interaction.edit_original_message(view=view)
	await view.update()

bot.run(TOKEN)