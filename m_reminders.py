from m_functions import *
from m_vars import *

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

async def notify_timer(args):
	# Main Notification Function
	# On Alarm, check if a reminder should be sent
	global lowerFreq
	global maxTimers
	global notifyTime
	global timeNoLuck
	global personalityOverride
	global n_timer
	chan = args["chan"]
	mute = await checkMute()
	if random.random() <= lowerFreq and not mute:
		reminders = await getReminders(False)
		if random.random() <= personalityOverride:
			# Instead of notifying, send personal message
			msgText = await constructMessage(TextEnum.Personality)
			await chan.send(msgText)
		elif len(reminders) > 0:
			# Send low priority reminder
			await chan.send(await constructRandomReminder(), delete_after=360*5)
		timeNoLuck = 0
	elif not mute:
		# Do nothing
		timeNoLuck += notifyTime
	if timeNoLuck >= maxTimers * notifyTime:
		# Send high priority reminder
		await chan.send(await constructRandomReminder(), delete_after=360*5)
		timeNoLuck = 0
	n_timer = Timer(notifyTime, notify_timer, args={'chan':chan})

async def constructRandomReminder():
	reminders = await getReminders(True)
	rem = random.choice(reminders)[0]
	if rem.endswith('?'):
		msgText = await constructMessage(TextEnum.Questioning)
	else:
		msgText = await constructMessage(TextEnum.Notification)
	if msgText.startswith("***") and len(rem) > 1:
		msgText = msgText.replace("***", rem[0].upper() + rem[1:])
	elif len(rem) > 1:
		msgText = msgText.replace("***", rem[0].lower() + rem[1:])
	else:
		msgText = msgText.replace("***", rem)
	return msgText

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