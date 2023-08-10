import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio, sqlite3, random, math, requests, json, os
from m_vars import *
import datetime
from datetime import time, tzinfo, timedelta

global con

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

def strToTime(string):
	#assumes string in ##:## format
	hour, minute = string.split(":")
	return datetime.time(hour=int(hour), minute=int(minute))

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

async def updateSetting(setting, value):
	global con
	cursor = con.execute("UPDATE SETTINGS SET value=? WHERE setting=?", (value, setting))
	con.commit()

async def getSetting(setting):
	global con
	cursor = con.execute("SELECT setting, value FROM SETTINGS WHERE setting=?", (setting,))
	fetch = cursor.fetchall()[0]
	if fetch[0] == None:
		return None
	if fetch[1] is None:
		return "[ ]"
	return str(fetch[1])
