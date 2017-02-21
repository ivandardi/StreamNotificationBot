import inspect

import discord
from discord import utils
from discord.ext import commands

from notification import database
from utils import checks
from utils.misc import initial_extensions


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
        for channel_id in database.get_all_subscribers():
            channel = self.bot.get_channel(channel_id)
            await channel.send(message)

    @commands.command()
    @checks.is_owner()
    async def info(self, ctx):
        """Provides some info about the bot.

        Currently only provides the guilds that the bot is in.
        """

        await ctx.send('\n'.join([guild.name for guild in ctx.bot.guilds]))

    @commands.command(name='reload')
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

    @commands.command(aliases=['find_member'], hidden=True)
    @checks.is_owner()
    async def find_user(self, ctx, *, user_id: int):
        """Finds a member."""

        member = utils.find(lambda m: m.id == str(user_id), self.bot.get_all_members())
        if member:
            await ctx.send(f'Found user {member.name} in guild {member.guild.name}.')
        else:
            await ctx.send('User not found.')

    @commands.command(hidden=True)
    @checks.is_owner()
    async def debug(self, ctx, *, code: str):
        """Evaluates code."""

        code = code.strip('` ')
        python = '```py\n{}\n```'

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'msg': ctx.message,
            'gld': ctx.guild,
            'cnl': ctx.channel,
            'ath': ctx.author,
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await ctx.send(python.format(type(e).__name__ + ': ' + str(e)))
            return

        await ctx.send(python.format(result))


def setup(bot):
    bot.add_cog(Admin(bot))
