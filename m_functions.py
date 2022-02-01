import asyncio, sqlite3
import nextcord as discord
from nextcord.ext import commands
import random, math, requests, json
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
	def __init__(self, bot, msg, user, reminders):
		super().__init__()
		self.sort = -1
		self.bot = bot 
		self.msg = msg
		self.user = user
		self.selected = 0
		self.reminders = reminders
	async def update(self):
		global con
		self.reminders = await getReminders(self.sort)
		msgtext = "```CURRENT REMINDERS\t\t\tPRTY\t\tSORT: "
		if self.sort == -1:
			msgtext += "ALL\n"
		elif self.sort == 0:
			msgtext += "LP\n"
		elif self.sort == 1:
			msgtext += "HP\n"
		count = 1
		for item in self.reminders:
			if self.selected == count - 1:
				msgtext += " >> "
			msgtext += str(count) + ". " + item[0] # + "\t\t" + str(item[1])
			if self.selected == count - 1:
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
			if self.selected == count - 1:
				msgtext += " << "
			msgtext += "\n"
			count += 1
		msgtext += "```"
		await self.msg.edit(msgtext)
	@discord.ui.button(label='ᐱ', style=discord.ButtonStyle.secondary)
	async def up(self, button: discord.ui.Button, interaction: discord.Interaction):
		if self.selected <= 0:
			self.selected = await countReminders(self.sort)
		self.selected -= 1
		await self.update()
	@discord.ui.button(label='SORT', style=discord.ButtonStyle.success)
	async def sort(self, button: discord.ui.Button, interaction: discord.Interaction):
		self.selected = 0
		self.sort += 1
		if self.sort > 1:
			self.sort = -1
		await self.update()
	@discord.ui.button(label='Delete', style=discord.ButtonStyle.danger)
	async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
		toDel = self.reminders[self.selected]
		await deleteReminder(toDel[0], toDel[1])
		await self.update()
		await self.msg.edit(self.msg.content + "Reminder deleted!")
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=2)
	async def down(self, button: discord.ui.Button, interaction: discord.Interaction):
		if self.selected >=  await countReminders(self.sort) - 1:
			self.selected = -1
		self.selected += 1
		await self.update()
	@discord.ui.button(label='Add LP', style=discord.ButtonStyle.primary, row=2)
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
	@discord.ui.button(label='Add HP', style=discord.ButtonStyle.primary, row=2)			
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
	global timerCount
	global maxTimers
	chan = args["chan"]
	await notify(chan)
	if timerCount == maxTimers:
		timerCount = -1
		await mangaCheck(chan)
	timerCount += 1

async def notify(chan):
	# On Alarm, check if a reminder should be sent
	global lowerFreq
	global maxTimers
	global globalTime
	global timeNoLuck
	if random.random() <= lowerFreq:
		reminders = await getReminders(False)
		if len(reminders) > 0:
			await chan.send(random.choice(reminders)[0])
			timeNoLuck = 0
	else:
		timeNoLuck += globalTime
	if timeNoLuck >= maxTimers * globalTime:
		reminders = await getReminders(True)
		await chan.send(random.choice(reminders)[0])
		timeNoLuck = 0
	timer = Timer(globalTime, start_timer, args={'chan':chan})

async def mangaCheck(chan):
	# On "maxTimers"th alarm, check for manga updates
	# Get list of manga from mangadex custom list
	response = requests.get("https://api.mangadex.org/list/bd404ab5-d07c-4dfc-b9ba-40e305e7fa47")
	mangaList = []
	temp = response.json().get("data").get("relationships")
	for i in temp:
		mangaList.append(i.get("id"))

# Database Functions
async def checkConnection(chan):
	global con
	await chan.send("```Attempting database connection```")
	con = sqlite3.connect("m_db.db")
	try:
		cursor = con.execute("SELECT title, priority FROM REMINDERS")
	except:
		await chan.send("```Creating REMINDERS table```")
		cursor = con.execute("CREATE TABLE REMINDERS (title TEXT PRIMARY KEY NOT NULL, priority BOOL NOT NULL);")
	try:
		cursor = con.execute("SELECT mangaID, chapterNUM FROM MANGA")
	except:
		await chan.send("```Creating MANGA table```")
		cursor = con.execute("CREATE TABLE MANGA (mangaID TEXT PRIMARY KEY NOT NULL, chapterNUM TEXT NOT NULL);")
	await chan.send("```Connection successful!```")

async def getReminders(priority):
	global con
	if priority < 0:
		cursor = con.execute("SELECT title, priority FROM REMINDERS")
	else:
		cursor = con.execute("SELECT title, priority FROM REMINDERS WHERE priority=?", (bool(priority),))
	return cursor.fetchall()

async def addReminder(title, priority):
	global con
	con.execute("INSERT INTO REMINDERS VALUES (?, ?) ", (title, bool(priority)))
	con.commit()

async def countReminders(priority):
	global con
	if priority < 0:
		cursor = con.execute("SELECT COUNT(*) FROM REMINDERS")
	else:
		cursor = con.execute("SELECT COUNT(*) FROM REMINDERS WHERE priority=?", (priority,))
	return int(cursor.fetchall()[0][0])

async def deleteReminder(title, priority):
	global con
	con.execute("DELETE FROM REMINDERS WHERE title=? AND priority=?", (title, priority))
	con.commit()

async def addManga(mangaID, chapterNUM):
	global con
	con.execute("INSERT INTO MANGA VALUES (?, ?)", (mangaID, chapterNUM))
	con.commit()

async def removeManga(mangaID):
	global con
	con.execute("DELETE FROM MANGA WHERE mangaID=?", (mangaID,))
	con.commit()

async def findManga(mangaID):
	global con
	cursor = con.execute("SELECT chapterNUM FROM MANGA WHERE mangaID=?", (mangaID,))
	return cursor.fetchall()

async def editManga(mangaID, chapterNUM):
	global con
	cursor = con.execute("UPDATE MANGA SET chapterNUM=? WHERE mangaID=?", (chapterNUM, mangaID))
	con.commit()

async def getManga():
	global con
	cursor = con.execute("SELECT mangaID FROM MANGA")
	out = []
	for manga in cursor.fetchall():
		out.append(manga[0])
	return out