import asyncio, sqlite3
import nextcord as discord
from nextcord.ext import commands
import random
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

async def start_timer(args):
	chan = args["chan"]
	await timesUp(chan)

async def timesUp(chan):
	global lowerFreq
	global higherTime
	global globalTime
	if random.random() <= lowerFreq:
		await chan.send("Lower")
	else:
		await chan.send("Higher")

	timer = Timer(globalTime, start_timer, args={'chan':chan})

async def checkConnection(chan):
	await chan.send("```Attempting database connection```")
	con = sqlite3.connect("m_db.db")
	try:
		cursor = con.execute("SELECT userID, guild, title, priority FROM REMINDERS")
		await chan.send("```Connection successful!```")
	except:
		await chan.send("```Creating REMINDERS table```")
		cursor = con.execute("CREATE TABLE REMINDERS (userID INT PRIMARY KEY NOT NULL, guild INT NOT NULL, title TEXT NOT NULL, priority BOOL NOT NULL);")