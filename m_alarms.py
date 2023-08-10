from m_functions import *
from m_vars import *

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
			if self.alarmTime.value != "":
				convTime = strToTime(self.alarmTime.value)
			else:
				convTime = NOON
			alarmDateTime = datetime.datetime.combine(convDate, convTime)
		except:
			await self.view.update("Error with the selected time (24hr format)")
			await interaction.response.edit_message(view=self.view)
			return
		alarmID = await getNextID()
		if self.number is None:
			await addAlarm(alarmID, self.name.value, alarmDateTime)
			await setAlarm(self.chan, alarmID, self.name.value, alarmDateTime)
		else:
			await addAlarm(alarmID, self.name.value, alarmDateTime, self.number, self.unit)
			await setAlarm(self.chan, alarmID, self.name.value, alarmDateTime, self.number, FreqUnit(self.unit))
		await self.view.update("Alarm Set!")
		await interaction.response.edit_message(view=self.view)

	async def on_error(self, interaction: discord.Interaction, error):
		self.stop()

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
		if count <= 0:
			count = 0
		else:
			msgtext += "...\n"
		for alarm in self.alarms[count:count+9]:
			line = ""
			if self.selected == count:
				line += ">> "
			alarmName = alarm.get('name')
			alarmDate = alarm.get('nextDate')
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
			if alarm.get('waitTime') is None:
				#Full
				line += alarmDate.strftime("%a %m/%d/%y @ %I:%M %p")
			elif alarm.get('waitUnit').name == "D":
				# Daily + Time
				line += alarmDate.strftime("Daily @ %I:%M %p")
			elif alarm.get('waitUnit').name == "W":
				# Weekday + Time
				line += alarmDate.strftime("%As @ %I:%M %p")
			elif alarm.get('waitUnit').name == "Y":
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
			if alarm.get('waitTime') != None:
				line += str(alarm.get('waitTime')) + " / " + alarm.get('waitUnit').name
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
		deleteID = int(self.alarms[self.selected].get('id'))
		await deleteAlarm(deleteID)
		await unsetAlarm(deleteID)
		if self.selected >=  len(self.alarms) - 1:
			self.selected = -1
		await self.update("Alarm deleted!")
	@discord.ui.button(label='SORT', style=discord.ButtonStyle.success, row=3)
	async def sort(self, interaction: discord.Interaction, button: discord.ui.Button):
		await interaction.response.edit_message(view=self)
		self.selected = 0
		self.sort += 1
		if self.sort > len(list(FreqUnit)):
			self.sort = -1
		await self.update()

async def alarm_timer(args):
	global alarmTimers
	chan = args["chan"]
	name = args["name"]
	alarmID = args["alarmID"]
	waitTime = args["waitTime"]
	waitUnit = args["waitUnit"]
	adjust = args["adjust"]
	# Send message
	mentionText = "<@&" + str(discord.utils.get(chan.guild.roles, name="Alarms").id) + "> "
	await chan.send(mentionText + name)
	# Check if needs to be repeated
	if waitTime != None:
		now = datetime.datetime.now()
		if waitUnit == FreqUnit(1):
			newDate = now + datetime.timedelta(days=waitTime)
		elif waitUnit == FreqUnit(2):
			newDate = now + datetime.timedelta(days=waitTime*7)
		elif waitUnit == FreqUnit(3):
			try:
				if now.month + waitTime > 12:
					month = now.month + waitTime - 12
					newDate = now.replace(year=now.year+1, month=month)
				else:
					month = now.month+waitTime
					newDate = now.replace(month=month)
				if adjust:
					newDate = newDate + datetime.timedelta(days=5)
					adjust = await editAlarmAdjustment(alarmID, False)
			except ValueError:
				adjust = await editAlarmAdjustment(alarmID, True)
				newDate = now.replace(month=month, day=now.day-5)
		elif waitUnit == FreqUnit(4):
			try:
				newDate = now.replace(year=now.year+waitTime)
			except ValueError:
				newDate = now.replace(year=now.year+waitTime, day=now.day-1)
		else:
			print("\n\n\n\nError: Should not be arriving at 'Else' statement on line 697\n\n\n\n")
			return
		await setAlarm(chan, alarmID, name, newDate, waitTime, waitUnit, adjust)
		await updateAlarm(alarmID, newDate)
	# Delete if not
	else:
		await deleteAlarm(alarmID)
		if alarmID == len(alarmTimers) - 1:
			alarmTimers = alarmTimers[:-1]

async def checkAlarms(chan):
	global alarmTimers
	alarms = await getAlarms(-1)
	count = 0
	now = datetime.datetime.now()
	lateText = ""
	for alarm in alarms:
		# Iterate through every alarm in db
		adjust = False
		alarmID = alarm.get("id")
		alarmDate = alarm.get("nextDate")
		alarmFreq = alarm.get("waitTime")
		alarmUnit = alarm.get("waitUnit")
		if (now - alarmDate).total_seconds() > 0:
			# Notify about alarms that already occurred
			if lateText == "":
				lateText = "An alarm went off while I was gone!\n\t" + alarm.get("name")
			elif lateText.startswith("An"):
				lateText = "A few alarms went off while I was gone! Here they are...\n\t" + lateText[37:] + "\n\t" + alarm.get("name")
			else:
				lateText += "\n\t" + alarm.get("name")
			if alarmFreq is None:
				# Remove unique alarms
				await deleteAlarm(alarmID)
				continue
			else:
				# Repeat necessary alarms
				nextTime = datetime.time(alarmDate.hour, alarmDate.minute)
				if alarmUnit == FreqUnit(1):
					delta = datetime.timedelta(days=alarmFreq)
					while (now - alarmDate).total_seconds() > 0:
						alarmDate = alarmDate + delta
				elif alarmUnit == FreqUnit(2):
					delta = datetime.timedelta(days=alarmFreq*7)
					while (now - alarmDate).total_seconds() > 0:
						alarmDate = alarmDate + delta
				elif alarmUnit == FreqUnit(3):
					while (now - alarmDate).total_seconds() > 0:
						try:
							if alarmDate.month + alarmFreq > 12:
								month = alarmDate.month + alarmFreq - 12
								alarmDate = datetime.date(alarmDate.year + 1, month, alarmDate.day)
							else:
								alarmDate = datetime.date(alarmDate.year, alarmDate.month + alarmFreq, alarmDate.day)
							if adjust:
								adjust = await editAlarmAdjustment(alarmID, False)
								alarmDate = alarmDate + datetime.timedelta(days=5)
						except ValueError:
							adjust = await editAlarmAdjustment(alarmID, True)
							alarmDate = datetime.date(alarmDate.year, alarmDate.month + alarmFreq, alarmDate.day - 5)
						alarmDate = datetime.datetime.combine(alarmDate, nextTime)
				elif alarmUnit == FreqUnit(4):
					while (now - alarmDate).total_seconds() > 0:
						try:
							alarmDate = datetime.date(alarmDate.year + alarmFreq, alarmDate.month, alarmDate.day)
						except ValueError:
							alarmDate = datetime.date(alarmDate.year + alarmFreq, alarmDate.month, alarmDate.day-1)
						alarmDate = datetime.datetime.combine(alarmDate, nextTime)
				else:
					print("\n\n\n\nError: Should not be arriving at 'Else' statement on line 697\n\n\n\n")
				await updateAlarm(alarmID, alarmDate)
		if alarmID != count:
			# If ID and index are desynced, fix
			await updateAlarmID(alarmID, count)
			await setAlarm(chan, count, alarm.get("name"), alarmDate, alarmFreq, alarmUnit, adjust)
		else:
			await setAlarm(chan, alarmID, alarm.get("name"), alarmDate, alarmFreq, alarmUnit, adjust)
		count += 1
	if lateText != "":
		# Notify about missed alarms
		await chan.send(lateText)

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
		cursor = con.execute("SELECT id, name, nextDate, waitTime, waitUnit FROM ALARMS")
	elif waitUnit is None:
		cursor = con.execute("SELECT id, name, nextDate, waitTime, waitUnit FROM ALARMS WHERE waitUnit=?", (None,))
	else:
		cursor = con.execute("SELECT id, name, nextDate, waitTime, waitUnit FROM ALARMS WHERE waitUnit=?", (waitUnit,))
	cursor = cursor.fetchall()
	returnList = []
	for i in cursor:
		if i[3] is None:
			temp = {"id":int(i[0]), "name":i[1], "nextDate":datetime.datetime.fromisoformat(i[2]), "waitTime":None, "waitUnit":None}
		else:
			temp = {"id":int(i[0]), "name":i[1], "nextDate":datetime.datetime.fromisoformat(i[2]), "waitTime":int(i[3]), "waitUnit":FreqUnit(int(i[4]))}
		returnList.append(temp)
	return returnList

async def setAlarm(chan, alarmID, name, nextDate, waitTime=None, waitUnit=None, adjust=False):
	global alarmTimers
	delta = nextDate - datetime.datetime.now()
	if waitTime != None:
		args = {'chan':chan, 'alarmID':alarmID, 'name':name, 'waitTime':int(waitTime), 'waitUnit':waitUnit, 'adjust':adjust}
	else:
		args = {'chan':chan, 'alarmID':alarmID, 'name':name, 'waitTime':None, 'waitUnit':None, 'adjust':adjust}
	if alarmID >= len(alarmTimers):
		alarmTimers.append(Timer(delta.total_seconds(), alarm_timer, args))
	else:
		alarmTimers[alarmID] = Timer(delta.total_seconds(), alarm_timer, args)

async def unsetAlarm(alarmID):
	global alarmTimers
	alarmTimers[alarmID].cancel()
	if alarmID == len(alarmTimers) - 1:
		alarmTimers = alarmTimers[:-1]

async def addAlarm(alarmID, name, nextDate, waitTime=None, waitUnit=None):
	global con
	con.execute("INSERT INTO ALARMS VALUES (?, ?, ?, ?, ?, False)", (alarmID, name, nextDate, waitTime, waitUnit))
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

async def editAlarmAdjustment(alarmID, adjust):
	global con
	cursor = con.execute("UPDATE ALARMS SET adjust=? WHERE id=?", (adjust, alarmID))
	con.commit()
	return adjust