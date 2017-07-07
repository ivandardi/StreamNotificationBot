import logging

import discord
from discord.ext import commands

log = logging.getLogger(__name__)


class Admin:
    """Bot owner commands."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(hidden=True)
    @commands.is_owner()
    async def close(self, ctx):
        """Close the bot safely."""

        await self.bot.logout()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def status(self, ctx, *, status: str):
        """Change the bot's status."""

        await self.bot.change_presence(game=discord.Game(name=status))

    @commands.command(hidden=True)
    @commands.is_owner()
    async def info(self, ctx: commands.Context):
        """Provide some info about the bot.

        Currently only provides the guilds that the bot is in.
        """

        await ctx.send(f'Currently in {len(self.bot.guilds)} servers!')
        await ctx.send('\n'.join([guild.name for guild in self.bot.guilds]))

    @commands.command(name='reload', hidden=True)
    @commands.is_owner()
    async def _reload(self, ctx, *, ext: str = None):
        """Reloads a module. Can only be used by the owner."""

        if ext:
            self.bot.unload_extension(ext)
            self.bot.load_extension(ext)
        else:
            for m in self.bot.initial_extensions:
                log.info('Reloading cog %s', m)
                self.bot.unload_extension(m)
                self.bot.load_extension(m)

    @_reload.error
    async def meta_error(self, ctx: commands.Context, error):
        await ctx.message.add_reaction('❌')
        await ctx.send(f'Failed to execute command!\n{type(error).__name__}: {error}')

    @_reload.after_invoke
    async def ok_hand(self, ctx: commands.Context):
        await ctx.message.add_reaction('👌')


def setup(bot):
    bot.add_cog(Admin(bot))
