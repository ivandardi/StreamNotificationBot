import logging

import discord
from discord.ext import commands

from notification import database
from utils import checks
from utils.misc import initial_extensions

log = logging.getLogger('stream_notif_bot')


class Admin:
    """Bot owner commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @checks.is_owner()
    async def close(self, ctx):
        """Closes the bot safely."""
        await self.bot.logout()

    @commands.command(hidden=True)
    @checks.is_owner()
    async def status(self, ctx, *, status: str):
        """Changes the bot's status."""
        await self.bot.change_presence(game=discord.Game(name=status))

    @commands.command(hidden=True)
    @checks.is_owner()
    async def broadcast(self, ctx, *, message: str):
        """Broadcasts a message to all subscribers."""
        for subscriber_id, channel_id in database.get_all_subscribers():
            channel = self.bot.get_channel(int(channel_id))
            try:
                await channel.send(message)
            except Exception as e:
                log.exception(f'Error happened when trying to broadcast to channel {channel_id}!')
                log.exception(f'broadcast: {e}')

    @commands.command(hidden=True)
    @checks.is_owner()
    async def info(self, ctx):
        """Provides some info about the bot.

        Currently only provides the guilds that the bot is in.
        """

        await ctx.send('\n'.join([guild.name for guild in ctx.bot.guilds]))

    @commands.command(name='reload', hidden=True)
    @checks.is_owner()
    async def _reload(self, ctx, *, module: str = None):
        """Reloads a module."""

        try:
            if module:
                self.bot.unload_extension(module)
                self.bot.load_extension(module)
            else:
                for m in initial_extensions:
                    self.bot.unload_extension(m)
                    self.bot.load_extension(m)
        except Exception as e:
            await ctx.send('Failed to reload extensions!\n{}: {}'.format(type(e).__name__, e))
        else:
            await ctx.send('\N{OK HAND SIGN}')


def setup(bot):
    bot.add_cog(Admin(bot))
