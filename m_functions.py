import nextcord as discord
from nextcord.ext import commands
import asyncio, sqlite3, random, math, requests, json
from m_vars import *
from enum import Enum

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
		self.bot = bot 
		self.msg = msg
		self.user = user
		self.reminders = reminders
		self.sort = -1
		self.selected = 0
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
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
	@discord.ui.button(label='REFRESH', style=discord.ButtonStyle.success)
	async def redo(self, button: discord.ui.Button, interaction: discord.Interaction):
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

class textEnum(Enum):
	personality = 1
	notification = 2
	manga = 3

# Timers
async def notify_timer(args):
	# On Alarm, check if a reminder should be sent
	global lowerFreq
	global maxTimers
	global notifyTime
	global timeNoLuck
	chan = args["chan"]
	if random.random() <= lowerFreq:
		reminders = await getReminders(False)
		if len(reminders) > 0:
			await chan.send(random.choice(reminders)[0])
			timeNoLuck = 0
	else:
		timeNoLuck += notifyTime
	if timeNoLuck >= maxTimers * notifyTime:
		reminders = await getReminders(True)
		await chan.send(random.choice(reminders)[0])
		timeNoLuck = 0
	timer = Timer(notifyTime, notify_timer, args={'chan':chan})

async def manga_timer(args):
	# On "maxTimers"th alarm, check for manga updates
	# Get list of manga from mangadex custom list
	global mangaTime
	chan = args["chan"]
	response = requests.get("https://api.mangadex.org/list/bd404ab5-d07c-4dfc-b9ba-40e305e7fa47")
	mangaIDs = []
	temp = response.json().get("data").get("relationships")
	for i in temp:
		if response.json().get("result") == "ok":
			mangaIDs.append(i.get("id"))
	# Compare newest manga to database
	for i in mangaIDs:
		inf = await getMangaInfo(i)
		if inf.get("errFlag"):
			continue
		result = await findManga(i)
		if result == -1:
			# If manga is not in database
			await addManga(i, await getNewestChapter(i))
		elif result == "err":
			continue
		else:
			newChap = await getNewestChapter(i)
			if newChap != result:
				# If manga in database has been updated
				await chan.send(inf.get("title") + " has been updated!")
				await editManga(i, newChap)
	timer = Timer(mangaTime, manga_timer, args={'chan':chan})

async def getNewestChapter(mangaID):
	response = requests.get("https://api.mangadex.org/manga/" + mangaID + "/aggregate")
	respo = response.json().get("volumes")
	vols = list(respo)
	try:
		chaps = list(respo.get("none").get("chapters").keys())
	except:
		chaps = list(respo.get(vols[1]).get("chapters").keys())
	return chaps[0]

async def getMangaInfo(mangaID):
	resp = requests.get("https://api.mangadex.org/manga/" + mangaID)
	if resp.json().get("result") != "ok":
		return {"title": "", "errFlag": True}
	title = list(resp.json().get("data").get("attributes").get("title").values())[0]
	return {"title": title, "errFlag": False}

# Database Functions
async def checkConnection(chan):
	global con
	msg = await chan.send("```Attempting database connection```")
	con = sqlite3.connect("m_db.db")
	try:
		cursor = con.execute("SELECT title, priority FROM REMINDERS")
	except:
		await msg.edit("```Creating REMINDERS table```")
		cursor = con.execute("CREATE TABLE REMINDERS (title TEXT PRIMARY KEY NOT NULL, priority BOOL NOT NULL);")
	try:
		cursor = con.execute("SELECT mangaID, chapterNUM FROM MANGA")
	except:
		await msg.edit("```Creating MANGA table```")
		cursor = con.execute("CREATE TABLE MANGA (mangaID TEXT PRIMARY KEY NOT NULL, chapterNUM TEXT NOT NULL);")
	try:
		cursor = con.execute("SELECT msgText, msgType FROM MESSAGES")
	except:
		await msg.edit("```Creating MESSAGES table```")
		cursor = con.execute("CREATE TABLE MESSAGES (msgText TEXT PRIMARY KEY NOT NULL, msgType INT NOT NULL, msgWeight INT NOT NULL);")
	await msg.edit("```Connection successful!```")

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
	out = -1
	cursor = con.execute("SELECT chapterNUM FROM MANGA WHERE mangaID=?", (mangaID,))
	for manga in cursor.fetchall():
		out = manga[0]
	return out

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

async def addMessage(msgText, msgType, msgWeight):
	global con
	con.execute("INSERT INTO MESSAGES VALUES (?, ?, ?)", (msgText, msgType, msgWeight))
	con.commit()

async def getRandomMessage(msgType):
	global con
	cursor = con.execute("SELECT msgText, msgWeight FROM MESSAGES WHERE msgType=?", (msgType,))
	msgList = cursor.fetchall()
	randList = []
	count = 0
	for msg in msgList:
		for i in range(0, msg[1]):
			randList.append(count)
		count += 1
	if len(randList) == 0:
		return None
	return msgList[random.choice(randList)][0]