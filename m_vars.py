global timeNoLuck
global on_check
global lowerFreq			# Frequency of lower priority reminders 							DEFAULT: 0.125
global personalityOverride	# Chance of notifications to be overriden by personality message	DEFAULT: 0.33
global maxTimers			# Amount of timers before higher priority reminder 					DEFAULT: 10
global notifyTime			# Global timer length in seconds 									DEFAULT: 153
global mangaTime			# Time between manga checks 										DEFAULT: 300
global con

timeNoLuck = 0
on_check = False
lowerFreq = 0.125
personalityOverride = 0.33
maxTimers = 10
notifyTime = 153
mangaTime = 300