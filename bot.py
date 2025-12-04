import os
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from commands import setup_commands
import datetime

# ---------------------------
# Load ENV
# ---------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID", 0))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 3600))

# ---------------------------
# Bot + Intents
# ---------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------
# State Object
# ---------------------------
class BotState:
    def __init__(self):
        self.last_repos = None
        self.channel = None
        self.interval = CHECK_INTERVAL

state = BotState()

# ---------------------------
# GitHub: get commit files
# ---------------------------
async def get_latest_commit_files(repo_name):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                return ("General Update", None)

            commits = await resp.json()
            if not commits:
                return ("General Update", None)

            latest_sha = commits[0]["sha"]

        commit_url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits/{latest_sha}"

        async with session.get(commit_url, headers=headers) as resp2:
            if resp2.status != 200:
                return ("General Update", None)

            commit_data = await resp2.json()

    files = commit_data.get("files", [])
    if not files:
        return ("General Update", None)

    file_names = [f["filename"] for f in files]
    return ("File Update", file_names)

# ---------------------------
# Detect changes
# ---------------------------
async def detect_changes(old, new):
    if old is None:
        return []

    changes = []

    old_repos = {r["name"]: r for r in old}
    new_repos = {r["name"]: r for r in new}

    # New repos
    for repo in new_repos:
        if repo not in old_repos:
            changes.append({
                "type": "Repository Created",
                "repo": repo,
                "update_kind": "Repository Created",
                "file": None,
                "timestamp": new_repos[repo]["created_at"]
            })

    # Updated repos
    for repo in new_repos:
        if repo in old_repos:
            if new_repos[repo]["updated_at"] != old_repos[repo]["updated_at"]:

                update_kind, files = await get_latest_commit_files(repo)

                file_changed = None
                if files:
                    file_changed = ", ".join(files)

                changes.append({
                    "type": "Repository Updated",
                    "repo": repo,
                    "update_kind": update_kind,
                    "file": file_changed,
                    "timestamp": new_repos[repo]["updated_at"]
                })

    return changes

# ---------------------------
# Embed Builder
# ---------------------------
def build_change_embed(change_type, repo_name, update_kind, file_changed=None, timestamp=None):
    if timestamp:
        try:
            ts = datetime.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except:
            ts = datetime.datetime.utcnow()
    else:
        ts = datetime.datetime.utcnow()

    embed = discord.Embed(
        title=change_type,
        color=discord.Color.blue(),
        timestamp=ts
    )

    # General Update (no file changed)
    if update_kind == "General Update" or file_changed is None:
        embed.add_field(
            name="Repository",
            value=f"**{repo_name}** | **General Update**",
            inline=False
        )
        embed.add_field(
            name="Time",
            value=ts.strftime("%I:%M %p"),
            inline=False
        )

    else:
        embed.add_field(
            name="Repository",
            value=f"**{repo_name}** | **File Update**",
            inline=False
        )
        embed.add_field(
            name="File Changed",
            value=f"**{file_changed}** | {ts.strftime('%I:%M %p')}",
            inline=False
        )

    embed.set_footer(text="GitHub Activity Monitor")
    return embed

# ---------------------------
# Fetch all repos
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
            except:
                return []

# ---------------------------
# Background Loop
# ---------------------------
@tasks.loop(seconds=CHECK_INTERVAL)
async def check_github():
    try:
        repos = await fetch_repos()
        if not isinstance(repos, list):
            print("GitHub API error:", repos)
            return

        changes = await detect_changes(state.last_repos, repos)
        state.last_repos = repos

        if changes and state.channel:
            for c in changes:
                embed = build_change_embed(
                    c["type"],
                    c["repo"],
                    c["update_kind"],
                    c["file"],
                    c["timestamp"]
                )
                await state.channel.send(embed=embed)

    except Exception as e:
        print("ERROR in check_github:", e)

@check_github.before_loop
async def before_loop():
    await bot.wait_until_ready()
    if DEFAULT_CHANNEL_ID:
        state.channel = bot.get_channel(DEFAULT_CHANNEL_ID)

# ---------------------------
# Force Check
# ---------------------------
async def force_check(channel):
    try:
        repos = await fetch_repos()
        changes = await detect_changes(state.last_repos, repos)

        if changes:
            for c in changes:
                embed = build_change_embed(
                    c["type"],
                    c["repo"],
                    c["update_kind"],
                    c["file"],
                    c["timestamp"]
                )
                await channel.send(embed=embed)
        else:
            await channel.send("No changes detected.")

        state.last_repos = repos

    except Exception as e:
        await channel.send(f"Error during force check: {e}")

# ---------------------------
# Setup Commands
# ---------------------------
setup_commands(bot, force_check, check_github, state)

# ---------------------------
# Start bot
# ---------------------------
async def main():
    async with bot:
        check_github.start()
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
