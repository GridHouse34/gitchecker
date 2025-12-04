import os
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime
from commands import setup_commands


# ---------------------------
#   Load ENV
# ---------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID", 0))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 3600))


# ---------------------------
#   Bot + Intents
# ---------------------------
intents = discord.Intents.default()
intents.message_content = True  # VERY IMPORTANT

bot = commands.Bot(command_prefix="!", intents=intents)



# ---------------------------
#   State Object (NO GLOBALS!)
# ---------------------------
class BotState:
    def __init__(self):
        self.last_repos = None
        self.channel = None
        self.interval = CHECK_INTERVAL


state = BotState()


# ---------------------------
#   GitHub Fetching
# ---------------------------
async def fetch_repos():
    url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
    headers = {}

    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            try:
                return await resp.json()
            except Exception:
                return []


def detect_changes(old, new):
    """Return a list of detected changes."""
    if old is None:
        return []  # First run: no changes

    changes = []

    old_repos = {r["name"]: r for r in old}
    new_repos = {r["name"]: r for r in new}

    # New repos
    for repo in new_repos:
        if repo not in old_repos:
            changes.append(f"🆕 New repository created: **{repo}**")

    # Updated repos
    for repo in new_repos:
        if repo in old_repos:
            if new_repos[repo]["updated_at"] != old_repos[repo]["updated_at"]:
                changes.append(f"♻️ Updated repository: **{repo}**")

    return changes


# ---------------------------
#   Background GitHub Loop
# ---------------------------
@tasks.loop(seconds=CHECK_INTERVAL)
async def check_github():
    try:
        repos = await fetch_repos()

        if not isinstance(repos, list):
            print("GitHub API error:", repos)
            return

        changes = detect_changes(state.last_repos, repos)

        state.last_repos = repos

        # Only notify if something changed
        if changes and state.channel:
            for c in changes:
                await state.channel.send(c)

    except Exception as e:
        # Log errors without crashing the bot
        print("ERROR in check_github:", e)


@check_github.before_loop
async def before_loop():
    await bot.wait_until_ready()
    if DEFAULT_CHANNEL_ID:
        state.channel = bot.get_channel(DEFAULT_CHANNEL_ID)


# ---------------------------
#   Force Check (command uses this)
# ---------------------------
async def force_check(channel):
    try:
        repos = await fetch_repos()
        changes = detect_changes(state.last_repos, repos)

        if changes:
            for c in changes:
                await channel.send(c)
        else:
            await channel.send("No changes detected.")

        state.last_repos = repos

    except Exception as e:
        await channel.send(f"Error during force check: {e}")


# ---------------------------
#   Setup commands
# ---------------------------
setup_commands(bot, force_check, check_github, state)


# ---------------------------
#   Start bot
# ---------------------------
async def main():
    async with bot:
        check_github.start()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except Exception as e:
        print("Fatal bot error:", e)

