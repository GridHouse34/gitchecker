from discord.ext import commands
import os


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
