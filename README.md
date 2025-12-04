---
name: GitChecker
description: A Python bot that monitors GitHub profile changes and sends notifications to Discord.
tags: [Python, Discord, GitHub, Bot, Automation]
---

# GitChecker

![GitChecker](https://img.shields.io/badge/Status-Beta-orange) ![Python](https://img.shields.io/badge/Python-3.12-blue)

**GitChecker** is a Python bot that monitors your GitHub profile for changes (new repositories or updates) and sends notifications to a Discord channel. It’s simple, self-hostable, and easy to configure.

---

## Features

- Automatically detects **new repositories** or **updated repositories** on your GitHub profile.  
- Sends **notifications to Discord**.  
- Configurable check interval.  
- Easy to deploy using Python 3.12 and a virtual environment.  

---

## Requirements

- **Python 3.12** (recommended; `audioop` is not available in newer versions).  
- Discord bot token.  
- GitHub username (optionally a Personal Access Token for private repos).  

---

## Installation

### 1️⃣ Create and activate a virtual environment

**Linux / Mac:**
```bash
python3.12 -m venv venv
source venv/bin/activate
