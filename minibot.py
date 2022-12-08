# MiniBot v1.3
#
# TODO: ! - priority; * - working on
#		randomly changing status/presence
#	!	make high priorities ping user
#	!	reminders for dates in the future, ie doctors appointments
#		mute command
#		lower time between notifs slightly
#	!	stop sending messages overnight, say goodnight and good morning
#		fix constructMessage to not lower if msgText[1] = " "
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
intents.members = True
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
		await chan.send("Hello! I'm getting ready to help you out!")
		await checkConnection(chan)

		chan = discord.utils.get(guild.text_channels, name="notifications")
		await checkAlarms(chan)
		n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})
		chan = discord.utils.get(guild.text_channels, name="manga-updates")
		m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})

		# Send ReminderView in #menu
		user = guild.owner
		chan = discord.utils.get(guild.text_channels, name="menu")
		reminder_cursor = await getReminders(-1)
		msg = await chan.send("Please wait one moment...")
		view = reminderView(bot, msg, user, reminder_cursor, MenuType.MAIN)
		await msg.edit(view=view)
		await view.update()

		# Send TemplateView in #menu
		template_cursor = await getTemplates(-1)
		msg = await chan.send("Please wait one moment...")
		view = templateView(bot, msg, user, template_cursor, MenuType.MAIN)
		await msg.edit(view=view)
		await view.update()

		# Send AlarmView in #menu
		alarm_cursor = await getAlarms(-1)
		msg = await chan.send("Please wait one moment...")
		view = alarmView(bot, msg, user, alarm_cursor, MenuType.MAIN)
		await msg.edit(view=view)
		await view.update()

		# Send ReminderView in #phone-menu
		chan = discord.utils.get(guild.text_channels, name="phone-menu")
		msg = await chan.send("Please wait one moment...")
		view = reminderView(bot, msg, user, reminder_cursor, MenuType.PHONE)
		await msg.edit(view=view)
		await view.update()

		# Send TemplateView in #phone-menu
		msg = await chan.send("Please wait one moment...")
		view = templateView(bot, msg, user, template_cursor, MenuType.PHONE)
		await msg.edit(view=view)
		await view.update()

		# Send AlarmView in #phone-menu
		msg = await chan.send("Please wait one moment...")
		view = alarmView(bot, msg, user, alarm_cursor, MenuType.PHONE)
		await msg.edit(view=view)
		await view.update()

@bot.command()
async def reminders(interaction):
	global con
	cursor = await getReminders(-1)
	await interaction.send("Please wait one moment...")
	if interaction.channel.name == "phone-menu":
		view = reminderView(bot, await interaction.original_message(), interaction.user, cursor, MenuType.PHONE)
	else:
		view = reminderView(bot, await interaction.original_message(), interaction.user, cursor, MenuType.MAIN)
	await interaction.edit_original_message(view=view)
	await view.update()

@bot.command()
async def templates(interaction):
	global con
	cursor = await getTemplates(-1)
	await interaction.send("Please wait one moment...")
	if interaction.channel.name == "phone-menu":
		view = templateView(bot, await interaction.original_message(), interaction.user, cursor, MenuType.PHONE)
	else:
		view = templateView(bot, await interaction.original_message(), interaction.user, cursor, MenuType.MAIN)
	await interaction.edit_original_message(view=view)
	await view.update()

@bot.command()
async def alarms(interaction):
	global con
	cursor = await getAlarms(-1)
	await interaction.send("Please wait one moment...")
	if interaction.channel.name == "phone-menu":
		view = alarmView(bot, await interaction.original_message(), interaction.user, cursor, MenuType.PHONE)
	else:
		view = alarmView(bot, await interaction.original_message(), interaction.user, cursor, MenuType.MAIN)
	await interaction.edit_original_message(view=view)
	await view.update()

bot.run(TOKEN)