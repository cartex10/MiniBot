# MiniBot v1.3
#
# TODO: ! - priority; * - working on
#		randomly changing status/presence
#	!	make high priorities ping user
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
intents = discord.Intents.all()
#intents.message_content = True
#intents.members = True
bot = commands.Bot(command_prefix="!", status="online", activity=base_activity, intents=intents)

@bot.event																		#called at bot startup
async def on_ready():
	global on_check
	global notifyTime
	global mangaTime
	guild = bot.get_guild(GUILD)
	await bot.tree.sync()
	if on_check is not True:
		on_check = True
		# Startup Msg/DB connection
		chan = discord.utils.get(guild.text_channels, name="general")
		await checkConnection(chan)
		await bot.change_presence(activity=base_activity, status="online")
		msg = await chan.send("Hello! I'm getting ready to help you out!")
		
		# Clean guild
		channels = ["menu", "phone-menu", "notifications"]
		category = discord.utils.get(guild.categories, name="Bot Channels")
		for chan in channels:
			try:
				toDel = discord.utils.get(guild.text_channels, name=chan)
				await toDel.delete()
				await guild.create_text_channel(name=chan, category=category, position=0)
			except:
				await guild.create_text_channel(name=chan, category=category, position=0)

		# Setup Notifications/ Alarms
		chan = discord.utils.get(guild.text_channels, name="notifications")
		await checkAlarms(chan)
		n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})

		# Setup Manga Updates
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

@bot.hybrid_command()
async def reminders(ctx):
	global con
	cursor = await getReminders(-1)
	msg = await ctx.send("Please wait one moment...")
	if ctx.channel.name == "phone-menu":
		view = reminderView(bot, msg, ctx.author, cursor, MenuType.PHONE)
	else:
		view = reminderView(bot, msg, ctx.author, cursor, MenuType.MAIN)
	await msg.edit(view=view)
	await view.update()

@bot.hybrid_command()
async def templates(ctx):
	global con
	cursor = await getTemplates(-1)
	msg = await ctx.send("Please wait one moment...")
	if ctx.channel.name == "phone-menu":
		view = templateView(bot, msg, ctx.author, cursor, MenuType.PHONE)
	else:
		view = templateView(bot, msg, ctx.author, cursor, MenuType.MAIN)
	await msg.edit(view=view)
	await view.update()

@bot.hybrid_command()
async def alarms(ctx):
	global con
	cursor = await getAlarms(-1)
	msg = await ctx.send("Please wait one moment...")
	if ctx.channel.name == "phone-menu":
		view = alarmView(bot, msg, ctx.author, cursor, MenuType.PHONE)
	else:
		view = alarmView(bot, msg, ctx.author, cursor, MenuType.MAIN)
	await msg.edit(view=view)
	await view.update()

@bot.hybrid_command()
async def clean(ctx):
	guild = bot.get_guild(GUILD)
	channels = ["menu", "phone-menu", "notifications"]
	category = discord.utils.get(guild.categories, name="Bot Channels")
	for chan in channels:
		try:
			toDel = discord.utils.get(guild.text_channels, name=chan)
			await toDel.delete()
			await guild.create_text_channel(name=chan, category=category, position=0)
		except:
			await guild.create_text_channel(name=chan, category=category, position=0)
	chan = discord.utils.get(guild.text_channels, name="notifications")
	await chan.send("Just finished cleaning up!")

@bot.hybrid_command()
async def settings(ctx, setting, value):
	await ctx.defer(ephemeral=True)
	msg = await ctx.send("Please wait one moment")
	if setting.upper() == "L" or setting.upper() == "LIST":
		# List command
		text = "List of all configurable settings:\n```"
		for setting in list(Settings):
			value = await getSetting(setting)
			text += setting + "  ->  " + str(value) + "\n"
		await msg.edit(content=text + "```")
		return
	if await getSetting(setting) == "[ ]":
		await msg.edit(content="ERROR: Setting not found.")
		return
	if value[0].upper() == "T" or value[0].upper() == "Y":
		# Check for boolean true inputs
		if (len(value) == 1) or (value.upper() == "TRUE") or (value.upper() == "YES"):
			value = 1
	elif value[0].upper() == "F" or value[0].upper() == "N":
		# Check for boolean false inputs
		if (len(value) == 1) or (value.upper() == "FALSE") or (value.upper() == "NO"):
			value = 0
		# Check for None/Null inputs
		elif value.upper() == "NONE" or value.upper() == "NULL" or value == "[ ]":
			value = None
	await updateSetting(setting, value)
	text = "Setting updated successfully!\n```"
	if value is None:
		value = "[ ]"
	text += setting.get("setting") + " -> " + str(value) + "```"
	await msg.edit(content=text)

@bot.check
async def check_commands(ctx):
	await bot.tree.sync()
	return True

bot.run(TOKEN)