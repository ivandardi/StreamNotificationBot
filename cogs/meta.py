import datetime

import discord.utils
from discord.ext import commands
from discord.permissions import Permissions


class Meta:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def uptime(self):
        """Tells you how long the bot has been up for.

        """

        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        fmt = '{h}h {m}m {s}s'
        if days:
            fmt = '{d}d ' + fmt

        await self.bot.say(f'Uptime: **{fmt.format(d=days, h=hours, m=minutes, s=seconds)}**')

    @commands.command()
    async def invite(self):
        """Provides the invite link for the bot.

        """

        await self.bot.say(
            f'Invite link: {discord.utils.oauth_url(self.bot.user.id, permissions=Permissions.text())}')


def setup(bot):
    bot.add_cog(Meta(bot))
