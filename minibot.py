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
		await chan.send("```Awaking MiniBot!```")
		await chan.send("Hello! I'm getting ready to help you out!")
		await checkConnection(chan)
		timer = Timer(globalTime, start_timer, args={'chan':chan})

@bot.slash_command()
async def reminders(interaction):
	cursor = await getReminders(-1)
	msgtext = "```CURRENT REMINDERS\t\t\tPTY\t\tSORT: ALL\n"
	count = 1
	for item in cursor:
		if not count - 1:
			msgtext += " >> "
		msgtext += str(count) + ". " + item[0] # + "\t\t" + str(item[1])
		if not count - 1:
			for i in range(1, math.floor((30 - len(item[0])) / 4)):
				msgtext += "\t"
		else:
			for i in range(0, math.floor((30 - len(item[0])) / 4)):
				msgtext += "\t"
		if not item[1]:
			msgtext += "LP"
		elif item[1]:
			msgtext += "HP"
		if not count - 1:
			msgtext += " << "
		msgtext += "\n"
		count += 1
	msgtext += "```"
	msg = await interaction.send(msgtext)
	vw = reminderView(bot, await interaction.original_message())
	await interaction.edit_original_message(view=vw)

bot.run(TOKEN)