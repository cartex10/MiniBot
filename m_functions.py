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
	async def update(self, sysMsg=None):
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
				msgtext += ">> "
			msgtext += str(count) + ". " + item[0] # + "\t\t" + str(item[1])
			if self.selected == count - 1:
				for i in range(2, math.floor((30 - len(item[0])) / 4)):
					msgtext += "\t"
				msgtext += "  "
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
		if sysMsg != None:
			msgtext += sysMsg
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
	@discord.ui.button(label='DELETE', style=discord.ButtonStyle.danger)
	async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
		toDel = self.reminders[self.selected]
		await deleteReminder(toDel[0], toDel[1])
		await self.update("Reminder deleted!")
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=2)
	async def down(self, button: discord.ui.Button, interaction: discord.Interaction):
		if self.selected >=  await countReminders(self.sort) - 1:
			self.selected = -1
		self.selected += 1
		await self.update()
	@discord.ui.button(label='ADD LP', style=discord.ButtonStyle.primary, row=2)
	async def addLP(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new reminder\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the reminder, try again")
		else:
			content = msg.content
			await msg.delete()
			if content != "CANCEL":
				await addReminder(content, 0)
				await self.update("Added Reminder")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ADD HP', style=discord.ButtonStyle.primary, row=2)			
	async def addHP(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new reminder\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the reminder, try again")
		else:
			content = msg.content
			await msg.delete()
			if content != "CANCEL":
				await addReminder(content, 1)
				await self.update("Added Reminder")
			else:
				await self.update("Cancelling...")

class messageView(discord.ui.View):
	def __init__(self, bot, msg, user, messages):
		super().__init__()
		self.bot = bot 
		self.msg = msg
		self.user = user
		self.messages = messages
		self.sort = -1
		self.selected = 0
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
	async def update(self, extra=None):
		global con
		self.messages = await getMessages(self.sort)
		msgtext = "```MESSAGE TEXT\t\t\t\t  TYPE\t\tWEIGHT\t\tSORT: "
		if self.sort == -1:
			msgtext += "ALL\n"
		elif self.sort == textEnum.personality.value:
			msgtext += "PERSN\n"
		elif self.sort == textEnum.notification.value:
			msgtext += "NOTIF\n"
		elif self.sort == textEnum.manga.value:
			msgtext += "MANGA\n"
		elif self.sort == textEnum.questioning.value:
			msgtext += "QUEST\n"
		elif self.sort == textEnum.greeting.value:
			msgtext += "GREET\n"
		count = 1
		for msg in self.messages:
			if self.selected == count - 1:
				msgtext += ">> "
			msgtext += str(count) + ". " + msg[0][0:min([len(msg[0]), 20])] # + "\t\t" + str(msg[1])
			if self.selected == count - 1:
				for i in range(0, math.floor((25 - min([len(msg[0]), 20])) / 4)):
					msgtext += "\t "
			else:
				for i in range(0, math.floor((25 - min([len(msg[0]), 20])) / 4)):
					msgtext += "\t"
				for i in range(-1, (25 - min([len(msg[0]), 20])) % 4):
					msgtext += " "
			if msg[2] == textEnum.personality.value:
				msgtext += "PERSN"
			elif msg[2] == textEnum.notification.value:
				msgtext += "NOTIF"
			elif msg[2] == textEnum.manga.value:
				msgtext += "MANGA"
			elif msg[2] == textEnum.questioning.value:
				msgtext += "QUEST"
			elif msg[2] == textEnum.greeting.value:
				msgtext += "GREET"
			msgtext += "\t\t" + str(msg[1])
			if self.selected == count - 1:
				msgtext += " << "
			msgtext += "\n"
			count += 1
		msgtext += "```"
		if extra != None:
			msgtext += extra
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
		if self.sort >= len(textEnum):
			self.sort = -1
		await self.update()
	@discord.ui.button(label='REFRESH', style=discord.ButtonStyle.success)
	async def redo(self, button: discord.ui.Button, interaction: discord.Interaction):
		await self.update()
	@discord.ui.button(label='DELETE', style=discord.ButtonStyle.danger)
	async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Are you sure you want to delete the following message? Y/n?\n"
		text += self.messages[self.selected][0]
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to confirm, try again")
		else:
			content = msg.content
			try:
				await msg.delete()
				await msg.delete()
				await msg.delete()
			except:
				pass
			if content.upper() == "Y":
				await deleteMessage(self.messages[self.selected][0], self.messages[self.selected][1], self.messages[self.selected][2])
				await self.update("Message template deleted")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=2)
	async def down(self, button: discord.ui.Button, interaction: discord.Interaction):
		if self.selected >=  await countReminders(self.sort) - 1:
			self.selected = -1
		self.selected += 1
		await self.update()
	@discord.ui.button(label='ADD PERSN', style=discord.ButtonStyle.primary, row=2)
	async def addPERSN(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new message template\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the message template, try again")
		else:
			content = msg.content
			try:
				await msg.delete()
				await msg.delete()
				await msg.delete()
			except:
				pass
			if content != "CANCEL":
				# get input 1 - Message text
				inp1 = content
				count = 1
				string = "Respond with the messages weight\n"
				for i in ['0', '20', '40', '60', '80', '100']:
					string += i + " - "
					if i == '0':
						string += "Never used"
					elif i == '20':
						string += "Fun to see, hard to get"
					elif i == '40':
						string += "Not too often"
					elif i == '60':
						string += "idk"
					elif i == '80':
						string += "Good not too often"
					elif i == '100':
						string += "Full weight"
					string +='\n'
				string += "Send 'CANCEL' to create nothing"
				await self.update(string)
				try:
					msg = await self.bot.wait_for('message', check=check, timeout=120)
				except asyncio.TimeoutError:
					await self.update("You ran out of time to add the message template, try again")
				else:
					content = msg.content
					try:
						await msg.delete()
						await msg.delete()
						await msg.delete()
					except:
						pass
				if content != "CANCEL":
					# get input 2 - Weight
					inp2 = content
					await addMessage(inp1, textEnum.personality.value, inp2)
					await self.update("Message template added successfully")
				else:
					await self.update("Cancelling...")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ADD NOTIF', style=discord.ButtonStyle.primary, row=2)
	async def addNOTIF(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new message template\n"
		text += "\\*\\*\\* replaces notification\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the message template, try again")
		else:
			content = msg.content
			try:
				await msg.delete()
				await msg.delete()
				await msg.delete()
			except:
				pass
			if content != "CANCEL":
				# get input 1 - Message text
				inp1 = content
				count = 1
				string = "Respond with the messages weight\n"
				for i in ['0', '20', '40', '60', '80', '100']:
					string += i + " - "
					if i == '0':
						string += "Never used"
					elif i == '20':
						string += "Fun to see, hard to get"
					elif i == '40':
						string += "Not too often"
					elif i == '60':
						string += "idk"
					elif i == '80':
						string += "Good not too often"
					elif i == '100':
						string += "Full weight"
					string +='\n'
				string += "Send 'CANCEL' to create nothing"
				await self.update(string)
				try:
					msg = await self.bot.wait_for('message', check=check, timeout=120)
				except asyncio.TimeoutError:
					await self.update("You ran out of time to add the message template, try again")
				else:
					content = msg.content
					try:
						await msg.delete()
						await msg.delete()
						await msg.delete()
					except:
						pass
				if content != "CANCEL":
					# get input 2 - Weight
					inp2 = int(content)
					await addMessage(inp1, textEnum.notification.value, inp2)
					await self.update("Message template added successfully")
				else:
					await self.update("Cancelling...")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ADD MANGA', style=discord.ButtonStyle.primary, row=2)
	async def addMANGA(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new message template\n"
		text += "\\*\\*\\* replaces title, ### replaces chapter num\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the message template, try again")
		else:
			content = msg.content
			try:
				await msg.delete()
				await msg.delete()
				await msg.delete()
			except:
				pass
			if content != "CANCEL":
				# get input 1 - Message text
				inp1 = content
				count = 1
				string = "Respond with the messages weight\n"
				for i in ['0', '20', '40', '60', '80', '100']:
					string += i + " - "
					if i == '0':
						string += "Never used"
					elif i == '20':
						string += "Fun to see, hard to get"
					elif i == '40':
						string += "Not too often"
					elif i == '60':
						string += "idk"
					elif i == '80':
						string += "Good not too often"
					elif i == '100':
						string += "Full weight"
					string +='\n'
				string += "Send 'CANCEL' to create nothing"
				await self.update(string)
				try:
					msg = await self.bot.wait_for('message', check=check, timeout=120)
				except asyncio.TimeoutError:
					await self.update("You ran out of time to add the message template, try again")
				else:
					content = msg.content
					try:
						await msg.delete()
						await msg.delete()
						await msg.delete()
					except:
						pass
				if content != "CANCEL":
					# get input 2 - Weight
					inp2 = int(content)
					await addMessage(inp1, textEnum.manga.value, inp2)
					await self.update("Message template added successfully")
				else:
					await self.update("Cancelling...")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ADD QUEST', style=discord.ButtonStyle.primary, row=2)
	async def addQUEST(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new message template\n"
		text += "\\*\\*\\* replaces notification\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the message template, try again")
		else:
			content = msg.content
			try:
				await msg.delete()
				await msg.delete()
				await msg.delete()
			except:
				pass
			if content != "CANCEL":
				# get input 1 - Message text
				inp1 = content
				count = 1
				string = "Respond with the messages weight\n"
				for i in ['0', '20', '40', '60', '80', '100']:
					string += i + " - "
					if i == '0':
						string += "Never used"
					elif i == '20':
						string += "Fun to see, hard to get"
					elif i == '40':
						string += "Not too often"
					elif i == '60':
						string += "idk"
					elif i == '80':
						string += "Good not too often"
					elif i == '100':
						string += "Full weight"
					string +='\n'
				string += "Send 'CANCEL' to create nothing"
				await self.update(string)
				try:
					msg = await self.bot.wait_for('message', check=check, timeout=120)
				except asyncio.TimeoutError:
					await self.update("You ran out of time to add the message template, try again")
				else:
					content = msg.content
					try:
						await msg.delete()
						await msg.delete()
						await msg.delete()
					except:
						pass
				if content != "CANCEL":
					# get input 2 - Weight
					inp2 = int(content)
					await addMessage(inp1, textEnum.questioning.value, inp2)
					await self.update("Message template added successfully")
				else:
					await self.update("Cancelling...")
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='ADD GREET', style=discord.ButtonStyle.primary, row=3)
	async def addGREET(self, button: discord.ui.Button, interaction: discord.Interaction):
		text = "Respond with the new message template\n"
		text += "Send 'CANCEL' to create nothing"
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel and m.author == self.user
		try:
			msg = await self.bot.wait_for('message', check=check, timeout=120)
		except asyncio.TimeoutError:
			await self.update("You ran out of time to add the message template, try again")
		else:
			content = msg.content
			try:
				await msg.delete()
				await msg.delete()
				await msg.delete()
			except:
				pass
			if content != "CANCEL":
				# get input 1 - Message text
				inp1 = content
				count = 1
				string = "Respond with the messages weight\n"
				for i in ['0', '20', '40', '60', '80', '100']:
					string += i + " - "
					if i == '0':
						string += "Never used"
					elif i == '20':
						string += "Fun to see, hard to get"
					elif i == '40':
						string += "Not too often"
					elif i == '60':
						string += "idk"
					elif i == '80':
						string += "Good not too often"
					elif i == '100':
						string += "Full weight"
					string +='\n'
				string += "Send 'CANCEL' to create nothing"
				await self.update(string)
				try:
					msg = await self.bot.wait_for('message', check=check, timeout=120)
				except asyncio.TimeoutError:
					await self.update("You ran out of time to add the message template, try again")
				else:
					content = msg.content
					try:
						await msg.delete()
						await msg.delete()
						await msg.delete()
					except:
						pass
				if content != "CANCEL":
					# get input 2 - Weight
					inp2 = content
					await addMessage(inp1, textEnum.greeting.value, inp2)
					await self.update("Message template added successfully")
				else:
					await self.update("Cancelling...")
			else:
				await self.update("Cancelling...")

class textEnum(Enum):
	personality = 0
	notification = 1
	manga = 2
	questioning = 3
	greeting = 4
	#startup = 4
	#status = 6

# Timers
async def notify_timer(args):
	# On Alarm, check if a reminder should be sent
	global lowerFreq
	global maxTimers
	global notifyTime
	global timeNoLuck
	global personalityOverride
	global n_timer
	chan = args["chan"]
	if random.random() <= lowerFreq:
		reminders = await getReminders(False)
		if random.random() <= personalityOverride:
			# Instead of notifying, send personal message
			msgText = constructMessage(textEnum.personality)
			await chan.send(msgText)
		elif len(reminders) > 0:
			# Send low priority reminder
			rem = random.choice(reminders)[0]
			if rem.endswith('?'):
				msgText = constructMessage(textEnum.questioning)
			else:
				msgText = constructMessage(textEnum.notification)
			await chan.send(msgText.replace("***", rem), delete_after=360*5)
		timeNoLuck = 0
	else:
		# Do nothing
		timeNoLuck += notifyTime
	if timeNoLuck >= maxTimers * notifyTime:
		# Send high priority reminder
		reminders = await getReminders(True)
		rem = random.choice(reminders)[0]
		if rem.endswith('?'):
			msgText = constructMessage(textEnum.questioning)
		else:
			msgText = constructMessage(textEnum.notification)
		await chan.send(msgText.replace("***", rem), delete_after=360*5)
		timeNoLuck = 0
	n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})

async def manga_timer(args):
	# On "maxTimers"th alarm, check for manga updates
	global mangaTime
	global m_timer
	chan = args["chan"]
	# Get list of manga from mangadex custom list
	response = requests.get("https://api.mangadex.org/list/bd404ab5-d07c-4dfc-b9ba-40e305e7fa47")
	mangaIDs = []
	temp = response.json().get("data").get("relationships")
	for i in temp:
		if response.json().get("result") == "ok":
			mangaIDs.append(i.get("id"))
	# Compare newest manga to database
	for i in mangaIDs:
		info = await getMangaInfo(i)
		if info.get("errFlag"):
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
				greet = await getRandomMessage(textEnum.greeting.value)
				msgText = greet + await getRandomMessage(textEnum.manga.value)
				msgText = msgText[0].upper() + msgText[1:]
				embed = discord.Embed().set_image(url=info.get("cover"))
				await chan.send(msgText.replace("***", info.get("title")).replace("###", newChap), embed=embed)
				await editManga(i, newChap)
	m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})

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
		return {"errFlag": True}
	title = list(resp.json().get("data").get("attributes").get("title").values())[0]
	respo = resp.json().get("data").get("relationships")
	cover = "https://uploads.mangadex.org/covers/" + mangaID
	for i in respo:
		if i.get("type") == "cover_art":
			response = requests.get("https://api.mangadex.org/cover/" + i.get("id"))
			cover += "/" + response.json().get("data").get("attributes").get("fileName")
			break
	return {"title": title, "cover": cover, "errFlag": False}

async def constructMessage(msgType):
	greet = await getRandomMessage(textEnum.greeting.value)
	msgText = await getRandomMessage(msgType.value)
	if greet == "":
		return msgText[0].upper() + msgText[1:]
	else:
		return greet[0].upper() + greet[1:] + " " + msgText[0].lower() + msgText[1:]

### Database Functions
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

# Reminders
async def getReminders(priority):
	global con
	if priority < 0:
		cursor = con.execute("SELECT title, priority FROM REMINDERS")
	else:
		cursor = con.execute("SELECT title, priority FROM REMINDERS WHERE priority=?", (priority,))
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

# Manga
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

# Message
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
	if msgType == textEnum.greeting.value:
		for i in range(0, 100):
			randList.append(-1)
	select = random.choice(randList)
	if select == -1:
		return ""
	return msgList[select][0]

async def getMessages(msgType):
	global con
	if msgType < 0:
		cursor = con.execute("SELECT msgText, msgWeight, msgType FROM MESSAGES")
	else:
		cursor = con.execute("SELECT msgText, msgWeight, msgType FROM MESSAGES WHERE msgType=?", (msgType,))
	return cursor.fetchall()

async def deleteMessage(msgText, msgWeight, msgType):
	global con
	con.execute("DELETE FROM MESSAGES WHERE msgText=? AND msgWeight=? AND msgType=?", (msgText, msgWeight, msgType))
	con.commit()