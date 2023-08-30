import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio, sqlite3, random, math, requests, json, os
import datetime
from datetime import time, tzinfo, timedelta
from m_vars import *

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

async def checkConnection(chan):
	global con
	con = sqlite3.connect("db/m_db.db")
	msg = await chan.send("```Attempting database connection```")
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
		cursor = con.execute("CREATE TABLE ALARMS (id INT PRIMARY KEY NOT NULL, name TEXT NOT NULL, nextDate DATETIME NOT NULL, waitTime INT, waitUnit INT, adjust BOOL DEFAULT False);")
	try:
		cursor = con.execute("SELECT setting, folder, value FROM SETTINGS")
	except:
		await msg.edit(content="```Creating SETTINGS table```")
		cursor = con.execute("CREATE TABLE SETTINGS (setting TEXT PRIMARY KEY NOT NULL, folder TEXT, value TEXT)")
	for setting in list(Settings):
		cursor = con.execute("SELECT value FROM SETTINGS WHERE setting=?", (setting,))
		if len(cursor.fetchall()) == 0:
			await msg.edit(content="```Updating SETTINGS table```")
			cursor = con.execute("INSERT INTO SETTINGS VALUES (?, ?, NULL)", (setting, SettingFolders.get(setting)))
			con.commit()
	await msg.edit(content="```Connection successful!```")

async def constructMessage(msgType):
	msgText = await getRandomTemplate(msgType.value)
	if msgText.upper() == msgText:
		return msgText
	else:
		greet = await getRandomTemplate(TextEnum.Greeting.value)
	if len(msgText) > 1:
		if msgText[1] == " " or greet == "":
			msgText = msgText[0].upper() + msgText[1:]
		else:
			msgText = msgText[0].lower() + msgText[1:]
	if greet == "":
		return msgText
	else:
		return greet[0].upper() + greet[1:].lower() + " " + msgText

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

async def checkMute():
	dawn = await getSetting("dawn")
	dusk = await getSetting("dusk")
	sleepAtNight = await getSetting("sleepAtNight")
	if dawn is None or dusk is None or sleepAtNight is None or not sleepAtNight:
		return False
	now = datetime.datetime.now()
	today = datetime.datetime.today()
	dawn = datetime.datetime.combine(today, strToTime(dawn))
	dusk = datetime.datetime.combine(today, strToTime(dusk))
	if (dawn - dusk).total_seconds() > 0:
		# If dusk is after midnight
		if dawn.hour > now.hour and dusk.hour < now.hour:
			return True
		elif dawn.hour == now.hour and dusk.hour == dawn.hour:
			if dawn.minute > now.minute and dusk.minute <= now.minute:
				return True
			else:
				return False
		elif dawn.hour == now.hour:
			if dawn.minute > now.minute:
				return True
			else:
				return False
		elif dusk.hour == now.hour:
			if dusk.minute <= now.minute:
				return True
			else:
				return False
		else:
			return False
	elif (dawn - dusk).total_seconds() < 0:
		# If dusk is before midnight
		if dawn.hour > now.hour and dusk.hour > now.hour:
			return True
		elif dawn.hour == now.hour:
			if dawn.minute > now.minute:
				return True
			else:
				return False
		elif dusk.hour == now.hour:
			if dusk.minute <= now.minute:
				return True
			else:
				return False
		else:
			return False

def strToTime(string):
	#assumes string in ##:## format
	hour, minute = string.split(":")
	return datetime.time(hour=int(hour), minute=int(minute))

### Database Functions
async def updateSetting(setting, value):
	global con
	cursor = con.execute("UPDATE SETTINGS SET value=? WHERE setting=?", (value, setting))
	con.commit()

async def getSetting(setting):
	global con
	cursor = con.execute("SELECT setting, value FROM SETTINGS WHERE setting=?", (setting,))
	fetch = cursor.fetchall()[0]
	if fetch[0] == None:
		print("m_functions:159: Setting '" + setting + "' not found")
		return None
	if fetch[1] is None:
		return None
	return str(fetch[1])
