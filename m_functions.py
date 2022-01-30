import asyncio
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
	#await chan.send("```Awaking MiniBot!```")
	#await chan.send("Hello! I'm getting ready to help you out!")
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