# MiniBot v1.3
#
# TODO: 
#		fix messages not deleting on command use
#		randomly changing status/presence
#		make high priorities ping user
#		reminders for dates in the future, ie doctors appointments
#		investigate multiple notifications
#		mute command
#		limit how much stuff shows in views to 10 per page
#		fix greetings: adding space between greeting and text, make text auto uppercase or lowercase
#		lower time between notifs slightly
#		limit how many database members are sent in message to 10 to limit number of characters sent in message
#		add ... to shortened texts
#		shorten reminders that are too long
#		in reminderView move TYPE over a bit
#		fix selected formatting
#		add up 5 and down 5 buttons
#		make weight array into enum
#
import nextcord as discord
from nextcord.ext import commands
from dotenv import load_dotenv
import random, math, time, asyncio, os
from m_functions import *
from m_vars import *

print("Starting bot with nextcord.py v" + discord.__version__)
load_dotenv()
TOKEN = os.getenv('TOKEN')
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
	await interaction.send("Please wait one moment...")
	view = reminderView(bot, await interaction.original_message(), interaction.user, cursor)
	await interaction.edit_original_message(view=view)
	await view.update()

@bot.slash_command()
async def messages(interaction):
	global con
	cursor = await getMessages(-1)
	await interaction.send("Please wait one moment...")
	view = messageView(bot, await interaction.original_message(), interaction.user, cursor)
	await interaction.edit_original_message(view=view)
	await view.update()

bot.run(TOKEN)