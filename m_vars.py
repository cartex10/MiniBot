import discord
from discord.ext import commands
from enum import Enum
import datetime
from datetime import time, tzinfo, timedelta

global timeNoLuck
timeNoLuck = 0
global on_check
on_check = False
global lowerFreq			# Frequency of lower priority reminders 							DEFAULT: lowerFreq = 0.125
global personalityOverride	# Chance of notifications to be overriden by personality message	DEFAULT: personalityOverride = 0.20
global maxTimers			# Amount of timers before higher priority reminder 					DEFAULT: maxTimers = 15
global notifyTime			# Global timer length in seconds 									DEFAULT: notifyTime = 603
global mangaTime			# Time between manga checks 										DEFAULT: mangaTime = 300
global con
global alarmTimers
alarmTimers = []

lowerFreq = 0.125
personalityOverride = 0.20
maxTimers = 15
notifyTime = 603
mangaTime = 300

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

EDT = datetime.timezone(timedelta(hours=-5), "EDT")
NOON = datetime.time(12, 0, 0, 0, EDT)

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

