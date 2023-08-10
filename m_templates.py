from m_functions import *
from m_vars import *

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