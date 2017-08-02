import asyncio
import datetime
import logging
import os
import traceback
from logging.handlers import TimedRotatingFileHandler

import aiohttp
import discord
from discord.ext import commands

from .utils import Database, strings, errors


def setup_logging():
    dt_fmt = '%Y-%m-%d %H:%M:%S'
    formatter = logging.Formatter('[{asctime}] [{levelname:<7}] {name}: {message}', dt_fmt, style='{')

    rotating_handler = TimedRotatingFileHandler(
        filename='logs/logging.log',
        encoding='utf-8',
        when='midnight',
        backupCount=3,
        utc=True,
    )
    rotating_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    logger.addHandler(rotating_handler)
    logger.addHandler(stream_handler)

    return logger


log = setup_logging()


def get_prefix(bot, msg):
    """Function that should be given as the `command_prefix` argument of Discord clients.

    The bot has 3 prefixes that always work:

    1. A mention followed by a space
    2. snb!
    3. snb?

    Additionally, if the bot is called in a private channel, it also listens to two more prefixes:

    1. !
    2. ?

    """

    prefix = commands.when_mentioned(bot, msg) + ['snb!', 'snb?']

    if isinstance(msg.channel, discord.abc.PrivateChannel):
        prefix += ['!', '?']

    return prefix


class StreamNotificationBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.version = '2.2.0'
        self.uptime = datetime.datetime.utcnow()
        self.database = kwargs['database']
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.initial_extensions = [
            'bot.cogs.services',
            'bot.cogs.admin',
            'bot.cogs.meta',
        ]

        for extension in self.initial_extensions:
            try:
                self.load_extension(extension)
            except Exception as e:  # noqa
                print(f'Failed to load extension {extension}\n{type(e).__name__}: {e}')

    async def logout(self):
        log.info('Logging out...')
        await self.database.close()
        await self.session.close()
        await super().logout()

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

        await self.change_presence(game=discord.Game(name='snb?help'))

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.NoPrivateMessage):
            return await ctx.send('This command cannot be used in private messages.')
        if isinstance(error, commands.DisabledCommand):
            return await ctx.send('Sorry. This command is disabled and cannot be used.')
        if isinstance(error, commands.CommandNotFound):
            return await ctx.send('Type `snb?help` for help on valid commands.')
        if isinstance(error, errors.StreamNotificationBotError):
            return log.error('StreamNotificationBotError: %s', error)
        if isinstance(error, commands.CommandInvokeError):
            return log.error('CommandInvokeError: %s', error)
        tb = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
        log.error(f'Command error in %s:\n%s', ctx.command.qualified_name, tb)

    async def on_command(self, ctx):
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            destination = 'Private Message'
        else:
            destination = f'#{ctx.channel.name} ({ctx.guild.name})'
        log.info('%s in %s: %s', ctx.message.author.name, destination, ctx.message.content)


def main():
    loop = asyncio.get_event_loop()
    database = loop.run_until_complete(Database.create_database(
        loop=loop,
        username='snb_role',
        password='snb_role',
        database='snb_db',
    ))

    snb = StreamNotificationBot(
        command_prefix=get_prefix,
        description=strings.bot_description,
        help_attrs=dict(hidden=True),
        loop=loop,
        database=database,
    )

    snb.run(os.environ['TOKEN_DISCORD'])

    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)


main()
