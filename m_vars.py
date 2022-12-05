import discord
from discord.ext import commands

global timeNoLuck
global on_check
global lowerFreq			# Frequency of lower priority reminders 							DEFAULT: lowerFreq = 0.125
global personalityOverride	# Chance of notifications to be overriden by personality message	DEFAULT: personalityOverride = 0.20
global maxTimers			# Amount of timers before higher priority reminder 					DEFAULT: maxTimers = 15
global notifyTime			# Global timer length in seconds 									DEFAULT: notifyTime = 603
global mangaTime			# Time between manga checks 										DEFAULT: mangaTime = 300
global con

timeNoLuck = 0
on_check = False
lowerFreq = 0.125
personalityOverride = 0.20
maxTimers = 15
notifyTime = 603
mangaTime = 300

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
		WeightDescription += "idk"
	elif i == '80':
		WeightDescription += "Good not too often"
	elif i == '100':
		WeightDescription += "Full weight"
	WeightDescription +='\n'

TemplateTypes = []
TemplateTypes.append(discord.SelectOption(label="Personal", value=0, default=True))
TemplateTypes.append(discord.SelectOption(label="Notification", value=1))
TemplateTypes.append(discord.SelectOption(label="Manga", value=2))
TemplateTypes.append(discord.SelectOption(label="Questioning", value=3))
TemplateTypes.append(discord.SelectOption(label="Greeting", value=4))
