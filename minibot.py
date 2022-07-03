# MiniBot v1.3
#
# TODO: ! - priority; * - working on
#		fix messages not deleting on command use
#		randomly changing status/presence
#	!	make high priorities ping user
#		reminders for dates in the future, ie doctors appointments
#		mute command
#		lower time between notifs slightly
#		in reminderView move TYPE over a bit
#	!	add up 5 and down 5 buttons
#	!	make weight array into enum
#	!	stop sending messages overnight, say goodnight and good morning
#		completion message upon reminder deletion
#	!	add error checking to mandadex api calls
#
import discord
from discord.ext import commands
from dotenv import load_dotenv
import random, math, time, asyncio, os
from m_functions import *
from m_vars import *

print("Starting bot with discord.py v" + discord.__version__)
load_dotenv()
TOKEN = os.getenv('TOKEN')
GUILD = int(os.getenv('GUILD'))

base_activity = discord.Activity(type=discord.ActivityType.listening, name="!help")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", status="online", activity=base_activity, intents=intents)

@bot.event																		#called at bot startup
async def on_ready():
	global on_check
	global notifyTime
	global mangaTime
	guild = bot.get_guild(GUILD)
	if on_check is not True:
		on_check = True
		await bot.change_presence(activity=base_activity, status="online")
		chan = discord.utils.get(guild.text_channels, name="general")
		await chan.send("```Waking MiniBot!```")
		await chan.send("Hello! I'm getting ready to help you out!")
		await checkConnection(chan)
		chan = discord.utils.get(guild.text_channels, name="notifications")
		n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})
		chan = discord.utils.get(guild.text_channels, name="manga-updates")
		m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})
		chan = discord.utils.get(guild.text_channels, name="menu")
		user = guild.owner
		# Send ReminderView in #menu
		cursor = await getReminders(-1)
		msg = await chan.send("Please wait one moment...")
		view = reminderView(bot, msg, user, cursor)
		await msg.edit(view=view)
		await view.update()
		# Send MessageView in #menu
		cursor = await getMessages(-1)
		msg = await chan.send("Please wait one moment...")
		view = messageView(bot, msg, user, cursor)
		await msg.edit(view=view)
		await view.update()

@bot.command()
async def reminders(interaction):
	global con
	cursor = await getReminders(-1)
	await interaction.send("Please wait one moment...")
	view = reminderView(bot, await interaction.original_message(), interaction.user, cursor)
	await interaction.edit_original_message(view=view)
	await view.update()

@bot.command()
async def messages(interaction):
	global con
	cursor = await getMessages(-1)
	await interaction.send("Please wait one moment...")
	view = messageView(bot, await interaction.original_message(), interaction.user, cursor)
	await interaction.edit_original_message(view=view)
	await view.update()

bot.run(TOKEN)