import datetime
import logging

import discord.utils
from discord.ext import commands

log = logging.getLogger(__name__)


class Meta:
    """Commands that deal with the bot itself."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    async def clean(self, ctx: commands.Context, limit=100):
        """Deletes the bot's messages up to the most 100 recent messages."""

        def is_me(m):
            return m.author.id == self.bot.user.id

        deleted = await ctx.channel.purge(limit=limit, check=is_me)
        await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Tell for how long the bot has been up."""

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt

        uptime = fmt.format(d=days, h=hours, m=minutes, s=seconds)
        await ctx.send(f'Uptime: **{uptime}**')

    @commands.command(aliases=['join'])
    async def invite(self, ctx: commands.Context):
        """Provide the invite link for the bot."""

        perms = discord.Permissions()
        perms.add_reactions = True
        perms.read_messages = True
        perms.send_messages = True
        perms.embed_links = True
        perms.read_message_history = True

        link = discord.utils.oauth_url(self.bot.user.id, permissions=perms)
        await ctx.send(f'Invite link: {link}')

    @commands.command()
    async def source(self, ctx: commands.Context):
        """Provide the Discord server invite for the bot."""

        await ctx.send('https://discord.gg/xrzJhqq')

    @commands.command()
    async def version(self, ctx: commands.Context):
        """Tell the version of the bot"""

        await ctx.send('The StreamNotificationBot is currently in version 2.0.0')


def setup(bot):
    bot.add_cog(Meta(bot))
