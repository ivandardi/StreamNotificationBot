import inspect

import discord
from discord import utils
from discord.ext import commands

import util
from util import initial_extensions


class Admin:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(hidden=True)
    @util.is_owner()
    async def close(self):
        await self.bot.logout()

    @commands.command(hidden=True)
    @util.is_owner()
    async def say(self, channel_id: str, *, message: str):
        await self.bot.send_message(discord.Object(id=channel_id), message)

    @commands.command(hidden=True)
    @util.is_owner()
    async def status(self, *, status: str):
        """Changes the bot's status."""
        await self.bot.change_presence(game=discord.Game(name=status))

    # TODO this. use PonyORM
    async def change_prefix(self):
        pass

    @commands.command(hidden=True)
    @util.is_owner()
    async def info(self):
        """Provides some info about the bot.

        Currently only provides the servers that the bot is in.

        """

        embed = discord.Embed()
        embed.add_field(name='Servers',
                        value='\n'.join([server.name for server in self.bot.servers]),
                        inline=False)

        await self.bot.say(embed=embed)

    @commands.command(pass_context=True, hidden=True)
    @util.is_owner()
    async def clean(self, ctx: commands.context.Context, limit: int = 100):
        """Removes a specified amount of messages from the chat."""

        deleted = 0
        async for m in self.bot.logs_from(ctx.message.channel, limit=limit, before=ctx.message):
            if m.author == self.bot.user:
                await self.bot.delete_message(m)
                deleted += 1

        await self.bot.say(f'Deleted {deleted} message(s)', delete_after=5)

    @commands.command(name='reload', hidden=True)
    @util.is_owner()
    async def _reload(self, *, module: str = None):
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
            await self.bot.say('Failed to reload extensions!\n{}: {}'.format(type(e).__name__, e))
        else:
            await self.bot.say('\N{OK HAND SIGN}')

    @commands.command(aliases=['find_member'], hidden=True)
    @util.is_owner()
    async def find_user(self, *, user_id: int):
        """Finds a member."""

        member = utils.find(lambda m: m.id == str(user_id), self.bot.get_all_members())
        if member:
            await self.bot.say(f'Found user {member.name} in server {member.server.name}.')
        else:
            await self.bot.say('User not found.')

    @commands.command(pass_context=True, hidden=True)
    @util.is_owner()
    async def debug(self, ctx: commands.context.Context, *, code: str):
        """Evaluates code."""
        code = code.strip('` ')
        python = '```py\n{}\n```'

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'msg': ctx.message,
            'srv': ctx.message.server,
            'cnl': ctx.message.channel,
            'ath': ctx.message.author
        }

        env.update(globals())

        try:
            result = eval(code, env)
            if inspect.isawaitable(result):
                result = await result
        except Exception as e:
            await self.bot.say(python.format(type(e).__name__ + ': ' + str(e)))
            return

        await self.bot.say(python.format(result))


def setup(bot):
    bot.add_cog(Admin(bot))
