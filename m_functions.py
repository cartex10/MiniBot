import discord
from discord.ext import commands
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

class reminderModal(discord.ui.Modal, title="Enter Reminder Text"):
	text = discord.ui.TextInput(label='Reminder')
	def __init__(self, view, priority):
		super().__init__()
		self.view = view
		self.priority = priority

	async def on_submit(self, interaction: discord.Interaction):
		await addReminder(self.text.value, self.priority)
		await self.view.update("Reminder Added!")
		await interaction.response.edit_message(view=self.view)

class templateModal(discord.ui.Modal, title="Enter Template Text"):
	text = discord.ui.TextInput(label='Template', required=True)
	weight = discord.ui.TextInput(label='Weight', required=True)
	def __init__(self, view, temptype):
		super().__init__()
		self.view = view
		self.temptype = temptype

	async def on_submit(self, interaction: discord.Interaction):
		await addTemplate(self.text.value, self.temptype, self.weight.value)
		await self.view.update("Template Added!")
		await interaction.response.edit_message(view=self.view)

class reminderView(discord.ui.View):
	def __init__(self, bot, msg, user, reminders, menutype):
		super().__init__()
		self.bot = bot 
		self.msg = msg
		self.user = user
		self.reminders = reminders
		self.menutype = menutype
		self.sort = -1
		self.selected = 0
		self.selectedPriority = 0
		self.timeout = 0
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
	async def update(self, sysMsg=None):
		global con
		self.reminders = await getReminders(self.sort)
		if self.menutype == MenuType.MAIN:
			tabs = "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t "
			tabs2 = "\t\t"
		elif self.menutype == MenuType.PHONE:
			tabs = "\n\t"
			tabs2 = "\t\t\t"
		msgtext = "```CURRENT REMINDERS" + tabs + "PRTY" + tabs2 + "SORT: "
		if self.sort == -1:
			msgtext += "ALL\n"
		elif self.sort == 0:
			msgtext += "LP\n"
		elif self.sort == 1:
			msgtext += "HP\n"
		count = max(self.selected - 4, 0)
		if self.selected > len(self.reminders) - 5:
			count = len(self.reminders) - 9
		if count < 0:
			count = 0
		startcount = count
		for item in self.reminders[count:count+9]:
			if count == startcount and startcount > 0:
				msgtext += "...\n"
			line = ""
			if self.selected == count:
				line += ">> "
			db_rem = item[0]
			if self.menutype == MenuType.MAIN:
				max_length = 106
			elif self.menutype == MenuType.PHONE:
				max_length = 20
			if len(db_rem) > max_length:
				db_rem = db_rem[0:max_length] + "..."
			line += str(count + 1) + ". " + db_rem
			lineLen = len(line)
			tabLength = 116
			if self.menutype == MenuType.MAIN:
				for i in range(0, math.floor((118 - lineLen) / 4)):
					line += "\t"
				for i in range(0, (118 - lineLen) % 4 + 1):
					line += " "
			elif self.menutype == MenuType.PHONE:
				msgtext += line + "\n"
				line = "\t"
			if not item[1]:
				line += "LP"
			elif item[1]:
				line += "HP"
			msgtext += line + "\n"
			count += 1
			if count == startcount + 9:
				if count < len(self.reminders):
					msgtext += "...\n"
				break
		msgtext += "```"
		if sysMsg != None:
			msgtext += sysMsg
		await self.msg.edit(content=msgtext)
	@discord.ui.select(options=ReminderPriorities, row=0)
	async def remsel(self, interaction: discord.Interaction, select: discord.ui.Select):
		self.selectedPriority = int(select.values[0])
		for i in ReminderPriorities:
			if i.value == int(select.values[0]):
				i.default = True
			else:
				i.default = False
		select.options = ReminderPriorities
		await interaction.response.edit_message(view=self)
	@discord.ui.button(label='ᐱ', style=discord.ButtonStyle.secondary)
	async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected -= 1
		if self.selected < 0:
			self.selected = await countReminders(self.sort) - 1
		await self.update()
	@discord.ui.button(label='+', style=discord.ButtonStyle.primary)
	async def addRem(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_modal(reminderModal(view=self, priority=self.selectedPriority))
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=2)
	async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		if self.selected >= await countReminders(self.sort) - 1:
			self.selected = -1
		self.selected += 1
		await self.update()
	@discord.ui.button(label='-', style=discord.ButtonStyle.danger, row=2)
	async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		toDel = self.reminders[self.selected]
		await deleteReminder(toDel[0], toDel[1])
		await self.update("Reminder deleted!")
		if self.selected >=  await countReminders(self.sort) - 1:
			self.selected = -1
	@discord.ui.button(label='SORT', style=discord.ButtonStyle.success, row=2)
	async def sort(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected = 0
		self.sort += 1
		if self.sort > 1:
			self.sort = -1
		await self.update()
	@discord.ui.button(label='REFRESH', style=discord.ButtonStyle.success)
	async def redo(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		await self.update()

class templateView(discord.ui.View):
	def __init__(self, bot, msg, user, templates, menutype):
		super().__init__()
		self.bot = bot 
		self.msg = msg
		self.user = user
		self.templates = templates
		self.menutype = menutype
		self.sort = -1
		self.selected = 0
		self.selectedType = 0
		self.timeout = 0
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
	async def update(self, extra=None):
		global con
		self.templates = await getTemplates(self.sort)
		if self.menutype == MenuType.MAIN:
			tabs = "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
			msgtext = "```TEMPLATE TEXT" + tabs + "TYPE\t\tWEIGHT\t\tSORT: "
		elif self.menutype == MenuType.PHONE:
			msgtext = "```TEMPLATE TEXT\t\tSORT: "
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
		if self.menutype == MenuType.PHONE:
			msgtext += "\tTYPE\t\tWEIGHT\n"
		count = max(self.selected - 4, 0)
		if self.selected > len(self.templates) - 5:
			count = len(self.templates) - 9
		if count < 0:
			count = 0
		startcount = count
		for msg in self.templates[count:count+9]:
			if count == startcount and startcount > 0:
				msgtext += "...\n"
			line = ""
			if self.selected == count:
				line += ">> "
			line += str(count + 1) + ". "
			db_msg = msg[0]
			if self.menutype == MenuType.MAIN:
				max_length = 89
			if self.menutype == MenuType.PHONE:
				max_length = 19
			if len(db_msg) > max_length:
				db_msg = db_msg[0:max_length] + "..."
			line += db_msg
			lineLen = len(line)
			if self.menutype == MenuType.PHONE:
				if self.selected == count:
					for i in range(0, math.floor((29 - lineLen) / 4)):
						line += "    "
					for i in range(0, (29 - lineLen) % 4):
						line += " "
					line += "<<"
				msgtext += line + "\n"
				line = ""
				if self.selected == count:
					line += ">>  "
				else:
					line += "\t"
				lineLen = len(line)
			tabLength = 99
			if self.menutype == MenuType.MAIN:
				for i in range(0, math.floor((tabLength - lineLen) / 4)):
					line += "    "
				for i in range(0, (tabLength - lineLen) % 4):
					line += " "
				if self.selected == count:
					line += " <<  "
				else:
					line += "     "
			if msg[2] == textEnum.personality.value:
				line += "PERSN"
			elif msg[2] == textEnum.notification.value:
				line += "NOTIF"
			elif msg[2] == textEnum.manga.value:
				line += "MANGA"
			elif msg[2] == textEnum.questioning.value:
				line += "QUEST"
			elif msg[2] == textEnum.greeting.value:
				line += "GREET"
			line += "         " + str(msg[1])
			lineLen = len(line)
			if self.menutype == MenuType.MAIN and self.selected == count:
				for i in range(0, math.floor((140 - lineLen) / 4)):
					line += "    "
				for i in range(0, (140 - lineLen) % 4):
					line += " "
			if self.menutype == MenuType.PHONE and self.selected == count:
				for i in range(0, 3 - len(str(msg[1]))):
					line += " "
				line += "        <<"
			msgtext += line + "\n"
			count += 1
			if count == startcount + 9:
				if count < len(self.templates):
					msgtext += "...\n"
				break
		msgtext += "```"
		if extra != None:
			msgtext += extra
		await self.msg.edit(content=msgtext)
	@discord.ui.button(label='ᐱ', style=discord.ButtonStyle.secondary)
	async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected -= 1
		if self.selected < 0:
			self.selected = len(self.templates) - 1
		await self.update()
	@discord.ui.button(label='ᐱ¹⁰', style=discord.ButtonStyle.secondary)
	async def upten(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected -= 10
		if self.selected < 0:
			self.selected = len(self.templates) - 1
		await self.update()
	@discord.ui.select(options=TemplateTypes, row=0)
	async def temsel(self, interaction: discord.Interaction, select: discord.ui.Select):
		value = int(select.values[0])
		self.selectedType = value
		for i in TemplateTypes:
			if i.value == value:
				i.default = True
			else:
				i.default = False
		description = ""
		if value == 1:
			description = "\\*\\*\\* replaces notification\n\n"
		elif value == 2:
			description = "\\*\\*\\* replaces title, ### replaces chapter num\n\n"
		elif value == 3:
			description = "\\*\\*\\* replaces notification\n\n"
		description += WeightDescription
		await self.update(description)
		select.options = TemplateTypes
		await interaction.response.edit_message(view=self)
	@discord.ui.button(label='+', style=discord.ButtonStyle.primary)
	async def add(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.send_modal(templateModal(view=self, temptype=self.selectedType))
	@discord.ui.button(label='REFRESH', style=discord.ButtonStyle.success)
	async def redo(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		await self.update()
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=2)
	async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		if self.selected + 1 >= len(self.templates):
			self.selected = -1
		self.selected += 1
		await self.update()
	@discord.ui.button(label='ᐯ₁₀', style=discord.ButtonStyle.secondary, row=2)
	async def downten(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		if self.selected + 10 >= len(self.templates):
			self.selected = -10
		self.selected += 10
		await self.update()
	@discord.ui.button(label='-', style=discord.ButtonStyle.danger, row=2)
	async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		text = "Are you sure you want to delete the following template? Y/n?\n"
		text += self.templates[self.selected][0]
		await self.update(text)
		def check(m):
			return m.channel == self.msg.channel
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
				await deleteTemplate(self.templates[self.selected][0], self.templates[self.selected][1], self.templates[self.selected][2])
				await self.update("Message template deleted")
				if self.selected >= len(self.templates) - 1:
					self.selected = -1
			else:
				await self.update("Cancelling...")
	@discord.ui.button(label='SORT', style=discord.ButtonStyle.success, row=2)
	async def sort(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected = 0
		self.sort += 1
		if self.sort >= len(textEnum):
			self.sort = -1
		await self.update()

class textEnum(Enum):
	personality = 0
	notification = 1
	manga = 2
	questioning = 3
	greeting = 4
	#startup = 4
	#status = 6

class MenuType(Enum):
	MAIN = 0
	PHONE = 1
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
			msgText = await constructMessage(textEnum.personality)
			await chan.send(msgText)
		elif len(reminders) > 0:
			# Send low priority reminder
			rem = random.choice(reminders)[0]
			rem = rem[0].lower() + rem[1:]
			if rem.endswith('?'):
				msgText = await constructMessage(textEnum.questioning)
			else:
				msgText = await constructMessage(textEnum.notification)
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
			msgText = await constructMessage(textEnum.questioning)
		else:
			msgText = await constructMessage(textEnum.notification)
		await chan.send(msgText.replace("***", rem), delete_after=360*5)
		timeNoLuck = 0
	n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})

async def manga_timer(args):
	# On check for manga updates
	global mangaTime
	global m_timer
	chan = args["chan"]
	mangaIDs = []
	# Get list of manga from mangadex custom list
	try:
		response = requests.get("https://api.mangadex.org/list/bd404ab5-d07c-4dfc-b9ba-40e305e7fa47")
		temp = response.json().get("data").get("relationships")
	except:
		m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})
		return
	for i in temp:
		if response.json().get("result") == "ok":
			mangaIDs.append(i.get("id"))
	# Compare newest manga to database
	for i in mangaIDs:
		info = await getMangaInfo(i)
		if not info.get("errFlag"):
			result = await findManga(i)
			if result == -1:
				# If manga is not in database
				await addManga(i, await getNewestChapter(i))
			elif not result == "err":
				newChap = await getNewestChapter(i)
				if newChap != result and newChap != None:
					# If manga in database has been updated
					msgText = await constructMessage(textEnum.manga)
					embed = discord.Embed().set_image(url=info.get("cover"))
					await chan.send(msgText.replace("***", info.get("title")).replace("###", newChap), embed=embed)
					await editManga(i, newChap)
	m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})

async def getNewestChapter(mangaID):
	try:
		response = requests.get("https://api.mangadex.org/manga/" + mangaID + "/aggregate")
		respo = response.json().get("volumes")
		vols = list(respo)
	except:
		return None
	try:
		chaps = list(respo.get("none").get("chapters").keys())
	except:
		chaps = list(respo.get(vols[1]).get("chapters").keys())
	return chaps[0]

async def getMangaInfo(mangaID):
	try:
		resp = requests.get("https://api.mangadex.org/manga/" + mangaID)
	except:
		return {"errFlag": True}
	if resp.json().get("result") != "ok":
		return {"errFlag": True}
	title = list(resp.json().get("data").get("attributes").get("title").values())[0]
	respo = resp.json().get("data").get("relationships")
	cover = "https://uploads.mangadex.org/covers/" + mangaID
	for i in respo:
		if i.get("type") == "cover_art":
			try:
				response = requests.get("https://api.mangadex.org/cover/" + i.get("id"))
			except:
				return {"errFlag": True}
			cover += "/" + response.json().get("data").get("attributes").get("fileName")
			break
	return {"title": title, "cover": cover, "errFlag": False}

async def constructMessage(msgType):
	greet = await getRandomTemplate(textEnum.greeting.value)
	msgText = await getRandomTemplate(msgType.value)
	if greet == "":
		return msgText[0].upper() + msgText[1:].lower()
	else:
		return greet[0].upper() + greet[1:].lower() + " " + msgText[0].lower() + msgText[1:]

### Database Functions
async def checkConnection(chan):
	global con
	msg = await chan.send("```Attempting database connection```")
	con = sqlite3.connect("m_db.db")
	try:
		cursor = con.execute("SELECT title, priority FROM REMINDERS")
	except:
		await msg.edit(content="```Creating REMINDERS table```")
		cursor = con.execute("CREATE TABLE REMINDERS (title TEXT PRIMARY KEY NOT NULL, priority BOOL NOT NULL);")
	try:
		cursor = con.execute("SELECT mangaID, chapterNUM FROM MANGA")
	except:
		await msg.edit(content="```Creating MANGA table```")
		cursor = con.execute("CREATE TABLE MANGA (mangaID TEXT PRIMARY KEY NOT NULL, chapterNUM TEXT NOT NULL);")
	try:
		cursor = con.execute("SELECT msgText, msgType FROM MESSAGES")
	except:
		await msg.edit(content="```Creating MESSAGES table```")
		cursor = con.execute("CREATE TABLE MESSAGES (msgText TEXT PRIMARY KEY NOT NULL, msgType INT NOT NULL, msgWeight INT NOT NULL);")
	await msg.edit(content="```Connection successful!```")

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
	if out == None:
		return "err"
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

# Templates
async def addTemplate(msgText, msgType, msgWeight):
	global con
	con.execute("INSERT INTO MESSAGES VALUES (?, ?, ?)", (msgText, msgType, msgWeight))
	con.commit()

async def getRandomTemplate(msgType):
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

async def getTemplates(msgType):
	global con
	if msgType < 0:
		cursor = con.execute("SELECT msgText, msgWeight, msgType FROM MESSAGES")
	else:
		cursor = con.execute("SELECT msgText, msgWeight, msgType FROM MESSAGES WHERE msgType=?", (msgType,))
	return cursor.fetchall()

async def deleteTemplate(msgText, msgWeight, msgType):
	global con
	con.execute("DELETE FROM MESSAGES WHERE msgText=? AND msgWeight=? AND msgType=?", (msgText, msgWeight, msgType))
	con.commit()