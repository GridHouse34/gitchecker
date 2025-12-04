import os
import asyncio
import aiohttp
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from commands import setup_commands
import datetime
import json

# ---------------------------
# Load ENV
# ---------------------------
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
DEFAULT_CHANNEL_ID = int(os.getenv("DEFAULT_CHANNEL_ID", 0))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 3600))
LAST_CHECK_FILE = "last_check_times.json"  # File to persist last commit times

# ---------------------------
# Bot + Intents
# ---------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------------------
# Bot State
# ---------------------------
class BotState:
    def __init__(self):
        self.last_repos = None
        self.channel = None
        self.interval = CHECK_INTERVAL
        self.last_check_times = {}  # per repo: ISO timestamp of last commit processed

state = BotState()

# ---------------------------
# Load / Save persistent last-check times
# ---------------------------
def load_last_check_times():
    if os.path.exists(LAST_CHECK_FILE):
        try:
            with open(LAST_CHECK_FILE, "r") as f:
                state.last_check_times = json.load(f)
        except:
            state.last_check_times = {}

def save_last_check_times():
    try:
        with open(LAST_CHECK_FILE, "w") as f:
            json.dump(state.last_check_times, f)
    except Exception as e:
        print("Error saving last_check_times:", e)

load_last_check_times()

# ---------------------------
# First-run initialization
# ---------------------------
async def initialize_last_check_times():
    # Only do this if last_check_times is empty (first run / JSON missing)
    if state.last_check_times:
        return  # Already loaded from JSON, nothing to do

    repos = await fetch_repos()
    for repo in repos:
        repo_name = repo["name"]
        # Use repo's last updated time as the starting point
        state.last_check_times[repo_name] = repo.get("updated_at") or datetime.datetime.now(datetime.timezone.utc).isoformat()

    save_last_check_times()

# ---------------------------
# Helper: Get commits since last check
# ---------------------------
async def get_commits_since(repo_name, since_iso):
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{repo_name}/commits"
    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    params = {}
    if since_iso:
        params["since"] = since_iso

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as resp:
            if resp.status != 200:
                return []
            commits = await resp.json()
            return commits

# ---------------------------
# Embed Builder
# ---------------------------
def build_change_embed(change_type, repo_name, update_kind, file_changed=None, timestamp=None, new_description=None):
    color_map = {
        "File Update": 0xFFD700,
        "Description Update": 0x3498DB,
        "Repository Created": 0x2ECC71,
        "General Update": 0x95A5A6
    }
    color = color_map.get(update_kind, 0x95A5A6)

    ts = timestamp
    if isinstance(ts, str):
        try:
            ts = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except:
            ts = datetime.datetime.now(datetime.timezone.utc)
    elif ts is None:
        ts = datetime.datetime.now(datetime.timezone.utc)

    ts_local = ts.astimezone()

    embed = discord.Embed(
        title=change_type,
        color=color,
        timestamp=ts_local
    )

    if update_kind == "Description Update":
        embed.add_field(
            name=f"Repository: {repo_name} | Description Updated",
            value=f"Description: {new_description}",
            inline=False
        )
        embed.add_field(
            name="Time",
            value=ts_local.strftime("%I:%M %p"),
            inline=False
        )
    elif update_kind == "File Update":
        embed.add_field(
            name=f"Repository: {repo_name} | File Update",
            value=f"{file_changed} | {ts_local.strftime('%I:%M %p')}",
            inline=False
        )
    elif update_kind == "Repository Created":
        embed.add_field(
            name=f"Repository Created: {repo_name}",
            value=f"Time: {ts_local.strftime('%I:%M %p')}",
            inline=False
        )
    else:
        embed.add_field(
            name=f"Repository: {repo_name} | General Update",
            value=f"Time: {ts_local.strftime('%I:%M %p')}",
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
# Detect changes
# ---------------------------
async def detect_changes(old, new):
    if old is None:
        return []

    changes = []
    old_repos = {r["name"]: r for r in old}
    new_repos = {r["name"]: r for r in new}

    for repo in new_repos:
        # New repository
        if repo not in old_repos:
            changes.append({
                "type": "Repository Created",
                "repo": repo,
                "update_kind": "Repository Created",
                "file": None,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
            continue

        # Detect description change
        old_desc = old_repos[repo].get("description")
        new_desc = new_repos[repo].get("description")
        if old_desc != new_desc:
            changes.append({
                "type": "Repository Updated",
                "repo": repo,
                "update_kind": "Description Update",
                "file": None,
                "new_description": new_desc or "No description",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })

        # Detect file updates via commits
        last_check = state.last_check_times.get(repo)
        commits = await get_commits_since(repo, last_check)

        latest_commit_time = last_check

        for commit in sorted(commits, key=lambda x: x["commit"]["author"]["date"]):
            commit_time = commit["commit"]["author"]["date"]
            files = commit.get("files", [])

            # Fetch files if not included
            if not files:
                async with aiohttp.ClientSession() as session:
                    commit_url = commit["url"]
                    async with session.get(commit_url, headers={"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            files = data.get("files", [])

            if files:
                file_names = ", ".join(f["filename"] for f in files)
                changes.append({
                    "type": "Repository Updated",
                    "repo": repo,
                    "update_kind": "File Update",
                    "file": file_names,
                    "timestamp": commit_time
                })

            if not latest_commit_time or commit_time > latest_commit_time:
                latest_commit_time = commit_time

        if latest_commit_time:
            state.last_check_times[repo] = latest_commit_time

    save_last_check_times()
    return changes

# ---------------------------
# Background loop
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
                    c.get("file"),
                    c["timestamp"],
                    c.get("new_description")
                )
                await state.channel.send(embed=embed)

    except Exception as e:
        print("ERROR in check_github:", e)

@check_github.before_loop
async def before_loop():
    await bot.wait_until_ready()
    if DEFAULT_CHANNEL_ID:
        state.channel = bot.get_channel(DEFAULT_CHANNEL_ID)
    # Initialize last_check_times safely
    await initialize_last_check_times()

# ---------------------------
# Force check
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
                    c.get("file"),
                    c["timestamp"],
                    c.get("new_description")
                )
                await channel.send(embed=embed)
        else:
            await channel.send("No changes detected.")

        state.last_repos = repos

    except Exception as e:
        await channel.send(f"Error during force check: {e}")

# ---------------------------
# Setup commands
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
