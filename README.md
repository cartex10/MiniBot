# MiniBot

## A Bot for sending common reminders throughout the day

## Can be run as a simple Python script, or as a Docker container

## Installation
The database will be created automatically, just make sure to create a ".env" file with the guild token, bot token, and mangalist id.

### Python Script
- Make sure your python version is >= 3.10
- Using pip, install Discord.py, python-dotenv, and requests
- Run using "python minibot.py"

### Docker container
- After pulling the repo and installing docker, run "docker build . -t minibot:latest"
- Then, modify "docker-compose.yml" as necessary and run "docker compose up -d"

## Current Functions
- Discord view/modal UI to add reminders/templates/alarms
- Randomly notify user throughout the day
- Randomly send personality messages
- Using Mangadex api, notify user on manga updates from CustomList
- Randomized messages depending on message sent
- Calendar alerts with optional repeat

## Future Plans
- Notes with dynamic line structure
- Connection with RoboDachi (far in future)