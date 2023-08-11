import discord
from discord.ext import commands
from enum import Enum
import sqlite3, datetime
from datetime import time, tzinfo, timedelta

on_check = False
con = sqlite3.connect("m_db.db")
timeNoLuck = 0
lowerFreq = 0.20	# Frequency of lower priority reminders			DEFAULT: lowerFreq = 0.125
personalityOverride = 0.2	# Chance of notifications to be overriden by personality message	DEFAULT: personalityOverride = 0.20
maxTimers = 15		# Amount of timers before higher priority reminder		DEFAULT: maxTimers = 15
notifyTime = 603	# Global timer length in seconds		DEFAULT: notifyTime = 603
mangaTime = 300		# Time between manga checks		DEFAULT: mangaTime = 300
alarmTimers = []

class TextEnum(Enum):
	Personality = 0
	Notification = 1
	Manga = 2
	Questioning = 3
	Greeting = 4
	#startup = 4
	#status = 6

class MenuType(Enum):
	MAIN = 0
	PHONE = 1

class FreqUnit(Enum):
	D = 1
	W = 2
	M = 3
	Y = 4

#EST = datetime.timezone(timedelta(hours=-5), "EST") #EST=-5 / EDT=-4
#EDT = datetime.timezone(timedelta(hours=-4), "EDT")
NOON = datetime.time(12, 0, 0, 0)

ReminderPriorities = []
ReminderPriorities.append(discord.SelectOption(label="LP", value=0, default=True))
ReminderPriorities.append(discord.SelectOption(label="HP", value=1))

WeightDescription = "Respond with the messages weight\n"
for i in ['0', '20', '40', '60', '80', '100']:
	WeightDescription += i + " - "
	if i == '0':
		WeightDescription += "Never used"
	elif i == '20':
		WeightDescription += "Fun to see, hard to get"
	elif i == '40':
		WeightDescription += "Not too often"
	elif i == '60':
		WeightDescription += "More often than not"
	elif i == '80':
		WeightDescription += "Good not too often"
	elif i == '100':
		WeightDescription += "Full weight"
	WeightDescription +='\n'

TemplateTypes = []
for i in list(TextEnum):
	if i.value == 0:
		TemplateTypes.append(discord.SelectOption(label=i.name, value=i.value, default=True))
	else:
		TemplateTypes.append(discord.SelectOption(label=i.name, value=i.value))

NumbersOptions = []
for i in range(0, 10):
	if i == 0:
		NumbersOptions.append(discord.SelectOption(label="Never", value=i, default=True))
	else:
		NumbersOptions.append(discord.SelectOption(label=str(i), value=i))

UnitOptions = []
for i in list(FreqUnit):
	if i.value == 0:
		UnitOptions.append(discord.SelectOption(label=i.name, value=i.value, default=True))
	else:
		UnitOptions.append(discord.SelectOption(label=i.name, value=i.value))

Settings = {
	# name: description
	"dusk": "(##:##) Time to pause MiniBot reminders every night",
	"dawn": "(##:##) Time to resume MiniBot reminders every morning",
	"sleepAtNight": "(BOOL) Toggle reminders between dusk and dawn"
}

SettingFolders = {
	# name: folder
	"dusk": None,
	"dawn": None,
	"sleepAtNight": None
}