from discord.ext import commands
import os
import aiohttp

def setup_commands(bot, force_check_func, check_loop, state):

    @bot.command(name="force")
    async def force_command(ctx):
        await ctx.send("Forcing GitHub check...")
        await force_check_func(ctx.channel)

    @bot.command(name="time")
    async def time_command(ctx, minutes: int):
        seconds = minutes * 60
        state.interval = seconds

        try:
            check_loop.change_interval(seconds=seconds)
            await ctx.send(f"⏱ Check interval updated to **{minutes} minutes**.")
        except Exception as e:
            await ctx.send(f"Error setting interval: {e}")

    @bot.command(name="channel")
    async def channel_command(ctx):
        state.channel = ctx.channel
        os.environ["DEFAULT_CHANNEL_ID"] = str(ctx.channel.id)
        await ctx.send(f"🔔 Notifications will now be sent in <#{ctx.channel.id}>.")

    # ---------------------------
    #   New command: !repos
    # ---------------------------
    @bot.command(name="repos")
    async def repos_command(ctx):
        """
        Displays the user's current public GitHub repository names.
        """
        GITHUB_USERNAME = os.getenv("GITHUB_USERNAME")
        GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

        url = f"https://api.github.com/users/{GITHUB_USERNAME}/repos"
        headers = {}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"token {GITHUB_TOKEN}"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    await ctx.send(f"❌ Could not fetch repos: {resp.status}")
                    return
                data = await resp.json()

        if not data:
            await ctx.send("No public repositories found.")
            return

        # Only display repository names
        repo_names = [repo["name"] for repo in data]
        message = "**Public repositories:**\n" + "\n".join(repo_names)

        # Ensure under Discord's 2000 character limit
        if len(message) > 2000:
            await ctx.send("Too many repositories to display.")
        else:
            await ctx.send(message)
