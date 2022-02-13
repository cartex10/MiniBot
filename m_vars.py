global timeNoLuck
global on_check
global lowerFreq			# Frequency of lower priority reminders 							DEFAULT: lowerFreq = 0.125
global personalityOverride	# Chance of notifications to be overriden by personality message	DEFAULT: personalityOverride = 0.20
global maxTimers			# Amount of timers before higher priority reminder 					DEFAULT: maxTimers = 15
global notifyTime			# Global timer length in seconds 									DEFAULT: notifyTime = 603
global mangaTime			# Time between manga checks 										DEFAULT: mangaTime = 300
global con
global n_timer
global m_timer

timeNoLuck = 0
on_check = False
lowerFreq = 0.125
personalityOverride = 0.20
maxTimers = 15
notifyTime = 603
mangaTime = 300