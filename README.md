---
name: GitChecker
description: A Python bot that monitors GitHub profile changes and sends notifications to Discord.
tags: [Python, Discord, GitHub, Bot, Automation]
---

# GitChecker
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](./LICENSE)
[![Python: 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Platform: Discord](https://img.shields.io/badge/Platform-Discord-purple)](https://discord.com/)
[![Status: Public](https://img.shields.io/badge/Status-Ready_for_Deployment-green)](https://github.com/GridHouse34/gitchecker)


**GitChecker** is a Python bot that monitors your GitHub profile for changes (new repositories or updates) and sends notifications to a Discord server and specified channel. It’s simple, self-hostable, and "easy" to configure.

---

## Features

- Automatically detects **new repositories** or **updated repositories** on your GitHub profile.  
- Sends **notifications to Discord**.  
- Configurable check interval.  
- Easy to deploy using Python 3.12 and a virtual environment.  

---

## Requirements

- **Python 3.12** (recommended; `audioop` is not available in newer versions and it won't stop nagging about it unless you find a solution).  
- Discord bot token.  
- GitHub username (and a Personal Access Token (fine-grained)).
  
requirements.txt as well.
```
python-dotenv
discord.py==2.3.2
aiohttp
```
---

## Installation

### 1️⃣ Create and activate a virtual environment

**Linux / Mac:**
```
python3.12 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell)**
```
python3.12 -m venv venv
.\venv\Scripts\activate
```

### 2️⃣ Install dependencies
```
pip install -r requirements.txt
```

### 3️⃣ Configure the bot

Create a .env file in the project root with the following content:
```
DISCORD_TOKEN=your_discord_bot_token
GITHUB_USERNAME=your_github_username
GITHUB_TOKEN=fine_grained_token
DEFAULT_CHANNEL_ID=0
CHECK_INTERVAL=3600
```

Notes:

DISCORD_TOKEN: Token for your Discord bot (Discord Developer Portal
).

GITHUB_USERNAME: Your GitHub username (from your profile URL).

GITHUB_TOKEN: Required Personal Access Token for GitHub (needed because you will receive a "Bad credentials" error without it).

DEFAULT_CHANNEL_ID: ID of the Discord channel for notifications (can be updated later with !channel).

CHECK_INTERVAL: How often the bot checks GitHub for changes, in seconds (default is 3600 = 1 hour).

### 4️⃣ Run the bot
```
python bot.py
```

## Once running, the bot will:

- Check for repository updates at the configured interval.
- Send notifications to your Discord channel when changes are detected.
- Shows currently public repositories in a list
---

### Discord Commands

!force → Force a GitHub check immediately.

!time <minutes> → Change the check interval.

!channel → Set the current channel as the notification channel.

!repos → Check every repo that is publicly available on defined profile.

💡 Tip: Ensure Message Content Intent is enabled in the Discord Developer Portal to allow command recognition.

---

### Tips

Keep the terminal open while the bot is running; closing it will disconnect the bot.

Use !force to test if everything is working correctly.

---

### LICENSE
This project uses the MIT License. Read more about it [here](https://github.com/GridHouse34/gitchecker/blob/main/LICENSE)

### Contributions/issues
Got an issue or wish to contribute? Submit pull requests, open issues, or contact the maintainer on Discord (GridHouse)!
