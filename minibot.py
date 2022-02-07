# MiniBot v1.2
#
# TODO: 
#		fix errors when view updates
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
	global n_timer
	global m_timer
	if on_check is not True:
		on_check = True
		guild = bot.get_guild(GUILD)
		await bot.change_presence(activity=base_activity, status="online")
		chan = discord.utils.get(guild.text_channels, name="general")
		await chan.send("```Waking MiniBot!```")
		await chan.send("Hello! I'm getting ready to help you out!")
		await checkConnection(chan)
		n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})
		chan = discord.utils.get(guild.text_channels, name="manga-updates")
		m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})

@bot.slash_command()
async def reminders(interaction):
	global con
	global n_timer
	global m_timer
	n_timer.cancel()
	guild = bot.get_guild(GUILD)
	chan = discord.utils.get(guild.text_channels, name="general")
	n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})
	cursor = await getReminders(-1)
	msgtext = "```CURRENT REMINDERS\t\t\tPRTY\t\tSORT: ALL\n"
	count = 1
	for item in cursor:
		if not count - 1:
			msgtext += " >> "
		msgtext += str(count) + ". " + item[0]
		if not count - 1:
			for i in range(1, math.floor((30 - len(item[0])) / 4)):
					msgtext += "\t"
		else:
			for i in range(1, math.floor((30 - len(item[0])) / 4)):
				msgtext += "\t"
			for i in range(-1, (30 - len(item[0])) % 4):
				msgtext += " "	
		if not item[1]:
			msgtext += "LP"
		elif item[1]:
			msgtext += "HP"
		if not count - 1:
			msgtext += " << "
		msgtext += "\n"
		count += 1
	msgtext += "```"
	await interaction.send(msgtext)
	vw = reminderView(bot, await interaction.original_message(), interaction.user, cursor)
	await interaction.edit_original_message(view=vw)

@bot.slash_command()
async def messages(interaction):
	global n_timer
	global m_timer
	n_timer.cancel()
	guild = bot.get_guild(GUILD)
	chan = discord.utils.get(guild.text_channels, name="general")
	n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})
	text = "Respond with the new message text\n"
	text += "Send 'CANCEL' to create nothing"
	await interaction.send(text)
	def check(m):
		return m.channel == interaction.channel and m.author == interaction.user
	try:
		msg = await bot.wait_for('message', check=check, timeout=120)
	except asyncio.TimeoutError:
		await interaction.edit_original_message(content="You ran out of time, try again")
	else:
		content = msg.content
		await msg.delete()
		if content != "CANCEL":
			# get input 1
			inp1 = content
			await interaction.edit_original_message(content=text.replace("new message text", "message type num\n1 - personality\n2 - notification\n3 - manga"))
			try:
				msg = await bot.wait_for('message', check=check, timeout=120)
			except asyncio.TimeoutError:
				await interaction.edit_original_message(content="You ran out of time, try again")
			else:
				content = msg.content
				await msg.delete()
				if content != "CANCEL":
					# get input 2
					inp2 = content
					await interaction.edit_original_message(content=text.replace("new message text", "message weight int, DEFAULT=100"))
					try:
						msg = await bot.wait_for('message', check=check, timeout=120)
					except asyncio.TimeoutError:
						await interaction.edit_original_message(content="You ran out of time, try again")
					else:
						content = msg.content
						await msg.delete()
						if content != "CANCEL":
							# get input 3
							inp3 = content
							await interaction.edit_original_message(content="Adding message to database")
							try:
								await addMessage(inp1, int(inp2), int(inp3))
							except:
								await interaction.edit_original_message(content="Error, try again")
						else:
							await interaction.edit_original_message(content="Cancelling...")
				else:
					await interaction.edit_original_message(content="Cancelling...")
		else:
			await interaction.edit_original_message(content="Cancelling...")

bot.run(TOKEN)