import asyncio, sqlite3
import nextcord as discord
from nextcord.ext import commands
import random, math
from m_vars import *

# Classes
class Timer:
	def __init__(self, timeout, callback, args=None):
		self._timeout = timeout
		self._callback = callback
		self._args = args
		self._task = asyncio.ensure_future(self._job())

	async def _job(self):
		await asyncio.sleep(self._timeout)
		await self._callback(self._args)

	def cancel(self):
		self._task.cancel()

class reminderView(discord.ui.View):
	def __init__(self, bot, msg, user):
		super().__init__()
		self.sort = -1
		self.bot = bot 
		self.msg = msg
		self.user = user
		self.selected = 0
	async def update(self):
		cursor = await getReminders(self.sort)
		msgtext = "```CURRENT REMINDERS\t\t\tPTY\t\tSORT: "
		if self.sort == -1:
			msgtext += "ALL\n"
		elif self.sort == 0:
			msgtext += "LP\n"
		elif self.sort == 1:
			msgtext += "HP\n"
		count = 1
		for item in cursor:
			if self.selected == count - 1:
				msgtext += " >> "
			msgtext += str(count) + ". " + item[0] # + "\t\t" + str(item[1])
			if self.selected == count - 1:
				for i in range(1, math.floor((30 - len(item[0])) / 4)):
					msgtext += "\t"
			else:
				for i in range(0, math.floor((30 - len(item[0])) / 4)):
					msgtext += "\t"
			if not item[1]:
				msgtext += "LP"
			elif item[1]:
				msgtext += "HP"
			if self.selected == count - 1:
				msgtext += " << "
			msgtext += "\n"
			count += 1
		msgtext += "```"
		await self.msg.edit(msgtext)
	@discord.ui.button(label='SORT', style=discord.ButtonStyle.secondary)
	async def sort(self, button: discord.ui.Button, interaction: discord.Interaction):
		self.sort += 1
		if self.sort > 1:
			self.sort = -1
		await self.update()
	@discord.ui.button(label='ADD LP', style=discord.ButtonStyle.primary)
	async def addLP(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new reminder\n"
		text += "Send 'CANCEL' to create nothing"
		await self.msg.edit(self.msg.content + text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update()
			await self.msg.edit(self.msg.content + "You ran out of time to create the inventory, try again")
		else:
			content = msg.content
			await msg.delete()
			if content != "CANCEL":
				await addReminder(content, 0)
				await self.update()
				await self.msg.edit(self.msg.content + "Added Reminder")
			else:
				await self.update()
				await self.msg.edit(self.msg.content + "Cancelling...")
	@discord.ui.button(label='ADD HP', style=discord.ButtonStyle.primary)			
	async def addHP(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new reminder\n"
		text += "Send 'CANCEL' to create nothing"
		await self.msg.edit(self.msg.content + text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update()
			await self.msg.edit(self.msg.content + "You ran out of time to create the inventory, try again")
		else:
			content = msg.content
			await msg.delete()
			if content != "CANCEL":
				await addReminder(content, 1)
				await self.update()
				await self.msg.edit(self.msg.content + "Added Reminder")
			else:
				await self.update()
				await self.msg.edit(self.msg.content + "Cancelling...")

# Timers
async def start_timer(args):
	chan = args["chan"]
	await timesUp(chan)

async def timesUp(chan):
	global lowerFreq
	global higherTime
	global globalTime
	if random.random() <= lowerFreq:
		await chan.send("Lower")
	else:
		await chan.send("Higher")

	timer = Timer(globalTime, start_timer, args={'chan':chan})

# Database Functions
async def checkConnection(chan):
	global con
	await chan.send("```Attempting database connection```")
	con = sqlite3.connect("m_db.db")
	try:
		cursor = con.execute("SELECT title, priority FROM REMINDERS")
		await chan.send("```Connection successful!```")
	except:
		await chan.send("```Creating REMINDERS table```")
		cursor = con.execute("CREATE TABLE REMINDERS (title TEXT PRIMARY KEY NOT NULL, priority BOOL NOT NULL);")

async def getReminders(priority):
	global con
	if priority < 0:
		cursor = con.execute("SELECT title, priority FROM REMINDERS")
	else:
		cursor = con.execute("SELECT title, priority FROM REMINDERS WHERE priority=?", (bool(priority),))
	return cursor

async def addReminder(title, priority):
	global con
	con.execute("INSERT INTO REMINDERS VALUES (?, ?) ", (title, bool(priority)))
	con.commit()