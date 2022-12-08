import discord
from discord.ext import commands
import asyncio, sqlite3, random, math, requests, json
from m_vars import *
import datetime
from datetime import time, tzinfo, timedelta

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

class alarmModal(discord.ui.Modal, title="Enter Alarm Info"):
	name = discord.ui.TextInput(label='Name', required=True)
	alarmDate = discord.ui.TextInput(label='mm/dd/yy', required=True)
	alarmTime = discord.ui.TextInput(label='hh:mm', required=False)
	def __init__(self, view, chan, number=None, unit=None):
		super().__init__()
		self.view = view
		self.number = number
		self.unit = unit
		self.chan = chan

	async def on_submit(self, interaction: discord.Interaction):
		try:
			splitDate = self.alarmDate.value.split("/")
			if int(splitDate[2]) < 2000:
				splitDate[2] = int(splitDate[2]) + 2000
			else:
				splitDate[2] = int(splitDate[2])
			convDate = datetime.date(splitDate[2], int(splitDate[0]), int(splitDate[1]))
		except:
			await self.view.update("Error with the date you selected")
			await interaction.response.edit_message(view=self.view)
			return
		try:
			if self.alarmTime.value != None:
				splitTime = self.alarmTime.value.split(":")
				convTime = datetime.time(int(splitTime[0]), int(splitTime[1]), tzinfo=EDT)
			else:
				convTime = NOON
			alarmDateTime = datetime.datetime.combine(convDate, convTime)
		except:
			await self.view.update("Error with the selected time (24hr format)")
			await interaction.response.edit_message(view=self.view)
			return
		alarmID = await getNextID()
		await addAlarm(alarmID, self.name.value, alarmDateTime, self.number, self.unit)
		await setAlarm(self.chan, alarmID, self.name.value, alarmDateTime, self.number, self.unit)
		await self.view.update("Alarm Set!")
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
		elif self.sort == TextEnum.Personality.value:
			msgtext += "PERSN\n"
		elif self.sort == TextEnum.Notification.value:
			msgtext += "NOTIF\n"
		elif self.sort == TextEnum.Manga.value:
			msgtext += "MANGA\n"
		elif self.sort == TextEnum.Questioning.value:
			msgtext += "QUEST\n"
		elif self.sort == TextEnum.Greeting.value:
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
			if msg[2] == TextEnum.Personality.value:
				line += "PERSN"
			elif msg[2] == TextEnum.Notification.value:
				line += "NOTIF"
			elif msg[2] == TextEnum.Manga.value:
				line += "MANGA"
			elif msg[2] == TextEnum.Questioning.value:
				line += "QUEST"
			elif msg[2] == TextEnum.Greeting.value:
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
		if self.sort >= len(TextEnum):
			self.sort = -1
		await self.update()

class alarmView(discord.ui.View):
	def __init__(self, bot, msg, user, alarms, menutype):
		super().__init__()
		self.bot = bot 
		self.msg = msg
		self.user = user
		self.alarms = alarms
		self.menutype = menutype
		self.sort = -1
		self.selected = 0
		self.selectedNumber = 0
		self.selectedUnit = 0
		self.timeout = 0
	async def on_timeout(self):
		await self.msg.delete()
		self.stop()
	async def update(self, sysMsg=None):
		global con
		self.alarms = await getAlarms(self.sort)
		if self.sort < 0:
			sortText = "ALL"
		elif self.sort == 0:
			sortText = "ONCE"
		else:
			sortText = FreqUnit(self.sort).key
		if self.menutype == MenuType.MAIN:
			tabs = "\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t"
			tab2 = "\t\t\t\t\t"
			tab3 = "\t\t\t"
			msgtext = "```ALARMS" + tabs + "Date" + tab2 + "Frequency" + tab3 + "SORT:" + sortText + "\n"
		elif self.menutype == MenuType.PHONE:
			tabs = "\t"
			tab2 = "\n\t"
			tab3 = "\n\t"
			msgtext = "```ALARMS" + tabs + "SORT: "+ sortText + tab2 + "Date" + tab3 + "Frequency\n"
		count = max(self.selected - 4, 0)
		if self.selected > len(self.alarms) - 5:
			count = len(self.alarms) - 9
		if count < 0:
			count = 0
		else:
			msgtext += "...\n"
		for alarmList in self.alarms[count:count+9]:
			line = ""
			if self.selected == count:
				line += ">> "
			alarmName = alarmList[0]
			alarmDate = datetime.datetime.fromisoformat(alarmList[1])
			if self.menutype == MenuType.MAIN:
				max_length = 76
			elif self.menutype == MenuType.PHONE:
				max_length = 20
			if len(alarmName) > max_length:
				alarmName = alarmName[0:max_length] + "..."
			line += str(count+1) + ". " + alarmName
			if self.menutype == MenuType.MAIN:
				lineLen = len(line)
				for i in range(0, math.floor((78 - lineLen) / 4)):
					line += "    "
				for i in range(0, (78 - lineLen) % 4 + 1):
					line += " "
			elif self.menutype == MenuType.PHONE:
				msgtext += line + "\n"
				line = "\t"
			if alarmList[3] == None:
				#Full
				line += alarmDate.strftime("%a %m/%d/%y @ %I:%M %p")
			elif FreqUnit(int(alarmList[3])).name == "W":
				# Weekday + Time
				line += alarmDate.strftime("%As @ %I:%M %p")
			elif FreqUnit(int(alarmList[3])).name == "Y":
				# mm/dd/yy + Time
				line += alarmDate.strftime("%m/%d/%y @ %I:%M %p")
			else:
				#Full
				line += alarmDate.strftime("%a %m/%d/%y @ %I:%M %p")
			if self.menutype == MenuType.MAIN:
				lineLen = len(line)
				for i in range(0, math.floor((107 - lineLen) / 4)):
					line += "\t"
				for i in range(0, (107 - lineLen) % 4 + 1):
					line += " "
			elif self.menutype == MenuType.PHONE:
				msgtext += line + "\n"
				line = "\t"
			if alarmList[2] != None:
				line += str(alarmList[2]) + " / " + FreqUnit(int(alarmList[3])).name
			elif self.menutype == MenuType.PHONE:
				line += "Never Repeat"
			msgtext += line + "\n"
			count += 1
		if count < len(self.alarms):
			msgtext += "...\n"
		msgtext += "```"
		if sysMsg != None:
			msgtext += sysMsg
		await self.msg.edit(content=msgtext)
	@discord.ui.select(options=NumbersOptions, row=0)
	async def numsel(self, interaction: discord.Interaction, select: discord.ui.Select):
		self.selectedNumber = int(select.values[0])
		for i in NumbersOptions:
			if i.value == int(select.values[0]):
				i.default = True
			else:
				i.default = False
		select.options = NumbersOptions
		await interaction.response.edit_message(view=self)
	@discord.ui.select(options=UnitOptions, row=1)
	async def unitsel(self, interaction: discord.Interaction, select: discord.ui.Select):
		self.selectedUnit = int(select.values[0])
		for i in UnitOptions:
			if i.value == int(select.values[0]):
				i.default = True
			else:
				i.default = False
		select.options = UnitOptions
		await interaction.response.edit_message(view=self)
	@discord.ui.button(label='ᐱ', style=discord.ButtonStyle.secondary, row=2)
	async def up(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected -= 1
		if self.selected < 0:
			self.selected = len(self.alarms) - 1
		await self.update()
	@discord.ui.button(label='+', style=discord.ButtonStyle.primary, row=2)
	async def addAlarm(self, interaction: discord.Interaction, button: discord.ui.Button):
		guild = self.msg.guild
		channel = discord.utils.get(guild.text_channels, name="notifications")
		if self.selectedNumber == 0:
			await interaction.response.send_modal(alarmModal(view=self, chan=channel))
		else:
			await interaction.response.send_modal(alarmModal(view=self, number=self.selectedNumber, unit=self.selectedUnit, chan=channel))
	@discord.ui.button(label='REFRESH', style=discord.ButtonStyle.success, row=2)
	async def redo(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		await self.update()
	@discord.ui.button(label='ᐯ', style=discord.ButtonStyle.secondary, row=3)
	async def down(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		if self.selected + 1 >= len(self.alarms):
			self.selected = -1
		self.selected += 1
		await self.update()
	@discord.ui.button(label='-', style=discord.ButtonStyle.danger, row=3)
	async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		deleteID = self.alarms[self.selected][0]
		await deleteAlarm(deleteID)
		if self.selected >=  len(self.alarms) - 1:
			self.selected = -1
		await self.update("Alarm deleted!")
	@discord.ui.button(label='SORT', style=discord.ButtonStyle.success, row=3)
	async def sort(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected = 0
		self.sort += 1
		if self.sort > 4:
			self.sort = -1
		await self.update()

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
			msgText = await constructMessage(TextEnum.Personality)
			await chan.send(msgText)
		elif len(reminders) > 0:
			# Send low priority reminder
			rem = random.choice(reminders)[0]
			rem = rem[0].lower() + rem[1:]
			if rem.endswith('?'):
				msgText = await constructMessage(TextEnum.Questioning)
			else:
				msgText = await constructMessage(TextEnum.Notification)
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
			msgText = await constructMessage(TextEnum.Questioning)
		else:
			msgText = await constructMessage(TextEnum.Notification)
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
					msgText = await constructMessage(TextEnum.Manga)
					embed = discord.Embed().set_image(url=info.get("cover"))
					await chan.send(msgText.replace("***", info.get("title")).replace("###", newChap), embed=embed)
					await editManga(i, newChap)
	m_timer = Timer(mangaTime, manga_timer, args={'chan':chan})

async def alarm_timer(args):
	global alarmTimers
	chan = args["chan"]
	name = args["name"]
	alarmID = args["alarmID"]
	nextDate = args["nextDate"]
	waitTime = args["waitTime"]
	waitUnit = args["waitUnit"]
	# Send message
	mentionText = "<@&" + str(discord.utils.get(chan.guild.roles, name="Alarms").id) + "> "
	await chan.send(mentionText + name)
	# Check if needs to be repeated
	if waitTime != None:
		if waitUnit == FreqUnit(1):
			newDate = nextDate + datetime.timedelta(days=waitTime)
		if waitUnit == FreqUnit(2):
			newDate = nextDate + datetime.timedelta(days=waitTime*7)
		if waitUnit == FreqUnit(3):
			newDate = nextDate + datetime.timedelta(days=waitTime*30)
		if waitUnit == FreqUnit(4):
			newDate = nextDate + datetime.timedelta(days=waitTime*365)
		await updateAlarm(alarmID, newDate)
	# Delete if not
	else:
		await deleteAlarm(alarmID)
		if alarmID == len(alarmTimers) - 1:
			alarmTimers = alarmTimers[:-1]

async def constructMessage(msgType):
	greet = await getRandomTemplate(TextEnum.Greeting.value)
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
	try:
		cursor = con.execute("SELECT name, nextDate, waitTime, waitUnit FROM ALARMS")
	except:
		await msg.edit(content="```Creating ALARMS table```")
		cursor = con.execute("CREATE TABLE ALARMS (id INT PRIMARY KEY NOT NULL, name TEXT NOT NULL, nextDate DATETIME NOT NULL, waitTime INT, waitUnit CHAR);")
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
	if msgType == TextEnum.Greeting.value:
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

# Alarms
async def checkAlarms(chan):
	global con
	global alarmTimers
	cursor = con.execute("SELECT id, name, nextDate, waitTime, waitUnit FROM ALARMS")
	alarms = cursor.fetchall()
	count = 0
	now = datetime.datetime.now(EDT)
	today = datetime.date.today()
	for alarm in alarms:
		alarmDate = alarm[2]
		if (alarmDate - now).total_seconds() < 0:
			if alarm[3] == None:
				await chan.send("An alarm went off while I was gone! " + alarm[1])
			else:
				nextTime = datetime.time(alarmDate.hour, alarmDate.minute, tzinfo=EDT)
				if alarm[4] == FreqUnit(1): # Fix to go off if time is later that day
					tempDate = datetime.date(today.year, today.month, today.day + alarm[3])
				elif alarm[4] == FreqUnit(2):	# Fix to go off on the same weekday
					tempDate = datetime.date(today.year, today.month, today.day + alarm[3]*7)
				elif alarm[4] == FreqUnit(3):
					tempDate = datetime.date(today.year, today.month + alarm[3], alarmDate.day)
				elif alarm[4] == FreqUnit(4):
					tempDate = datetime.date(today.year + alarm[3], alarmDate.month, alarmDate.day)
				alarmDate = datetime.datetime.combine(tempDate, nextTime)
		if alarm[0] != count:
			await updateAlarmID(alarm[0], count)
			await setAlarm(chan, count, alarm[1], alarmDate, int(alarm[3]), alarm[4])
		else:
			await setAlarm(chan, int(alarm[0]), alarm[1], alarmDate, int(alarm[3]), alarm[4])
		count += 1

async def getNextID():
	global con
	cursor = con.execute("SELECT id FROM ALARMS")
	db_ids = cursor.fetchall()
	ids = []
	for alarm in db_ids:
		ids.append(int(alarm[0]))
	ids.sort()
	count = -1
	for i in ids:
		count += 1
		if i < 0:
			continue
		if i != count:
			return i
	return count + 1

async def getAlarms(waitUnit):
	global con
	if waitUnit < 0:
		cursor = con.execute("SELECT name, nextDate, waitTime, waitUnit FROM ALARMS")
	elif waitUnit == None:
		cursor = con.execute("SELECT name, nextDate, waitTime, waitUnit FROM ALARMS WHERE waitUnit=?", (None,))
	else:
		cursor = con.execute("SELECT name, nextDate, waitTime, waitUnit FROM ALARMS WHERE waitUnit=?", (waitUnit,))
	return cursor.fetchall()

async def setAlarm(chan, alarmID, name, nextDate, waitTime=None, waitUnit=None):
	global con
	global alarmTimers
	cursor = con.execute("SELECT id FROM ALARMS WHERE id!=?", (alarmID,))
	allAlarms = cursor.fetchall()
	count = len(allAlarms)
	delta = nextDate - datetime.datetime.now(EDT)
	if waitTime != None:
		args = {'chan':chan, 'alarmID':alarmID, 'name':name, 'nextDate':nextDate, 'waitTime':int(waitTime), 'waitUnit':FreqUnit(waitUnit)}
	else:
		args = {'chan':chan, 'alarmID':alarmID, 'name':name, 'nextDate':nextDate, 'waitTime':None, 'waitUnit':None}
	if alarmID >= count:
		alarmTimers.append(Timer(delta.total_seconds(), alarm_timer, args))
	else:
		alarmTimers[alarmID] = Timer(delta.total_seconds(), alarm_timer, args)

async def addAlarm(alarmID, name, nextDate, waitTime=None, waitUnit=None):
	global con
	con.execute("INSERT INTO ALARMS VALUES (?, ?, ?, ?, ?)", (alarmID, name, nextDate, waitTime, waitUnit))
	con.commit()

async def deleteAlarm(alarmID):
	global con
	con.execute("DELETE FROM ALARMS WHERE id=?", (alarmID,))
	con.commit()

async def updateAlarm(alarmID, nextDate):
	global con
	cursor = con.execute("UPDATE ALARMS SET nextDate=? WHERE id=?", (nextDate, alarmID))
	con.commit()

async def updateAlarmID(alarmID, newID):
	global con
	cursor = con.execute("UPDATE ALARMS SET id=? WHERE id=?", (newID, alarmID))
	con.commit()