import datetime
import logging

import discord.utils
from discord.ext import commands
from discord.permissions import Permissions

from notification.database import change_prefix
from utils import checks

log = logging.getLogger('stream_notif_bot')


class Meta:
    """Commands that deal with the bot itself."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='prefix', invoke_without_command=True)
    async def prefix(self, ctx):
        """Returns the current prefixes of the bot."""

        prefixes = ', '.join(await self.bot.get_prefix(ctx.message))
        await ctx.send(f'Current prefixes: {prefixes}')

    @prefix.command(aliases=['set'])
    @commands.has_permissions(manage_guild=True)
    async def change(self, ctx, prefix: str):
        """Changes the current prefix of the bot on the current guild."""

        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            await ctx.send('Can\'t change prefix in a private channel!')
            return

        try:
            guild_id = str(ctx.guild.id)
            change_prefix(guild_id, prefix)
        except Exception as e:
            ctx.send('Failed to change prefix.')
            log.exception('prefix change: ', e)
        else:
            ctx.send(f'Prefix successfully changed to {prefix}')

    @commands.command()
    @checks.is_owner()
    @commands.has_permissions(manage_messages=True)
    async def clean(self, ctx, limit: int = 100):
        """Removes a specified amount of messages from the chat."""

        deleted = 0
        async for m in self.bot.logs_from(ctx.message.channel, limit=limit, before=ctx.message):
            if m.author == self.bot.user:
                await self.bot.delete_message(m)
                deleted += 1

        await self.bot.say(f'Deleted {deleted} message(s)', delete_after=5)

    @commands.command()
    async def uptime(self, ctx):
        """Tells how long the bot has been up for."""

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt

        await ctx.send(f'Uptime: **{fmt.format(d=days, h=hours, m=minutes, s=seconds)}**')

    @commands.command()
    async def invite(self, ctx):
        """Provides the invite link for the bot."""

        await ctx.send(f'Invite link: {discord.utils.oauth_url(self.bot.user.id, permissions=Permissions.text())}')


def setup(bot):
    bot.add_cog(Meta(bot))
