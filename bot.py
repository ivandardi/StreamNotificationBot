import datetime
import logging
import traceback

import discord
from discord.ext import commands

from notification.database import get_prefix
from utils.misc import initial_extensions, credentials, setup_logger

description = """
Hello! I am a bot created to notify you when streamers go online!
Author: MelodicStream#1336


==== HOW TO USE THE BOT ====

Currently supported services: Twitch and Picarto.

To add a streamer to your subscription list, use the following command:

snb?add <service> <username>
Example: snb?add picarto mykegreywolf

For more help about any command, type snb?help <command>.
Examples:
snb?help add
snb?help del
snb?help list

==== COMMANDS ====

"""

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)

log = setup_logger('stream_notif_bot')


class StreamNotificationBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uptime = None

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

        if not self.uptime:
            self.uptime = datetime.datetime.utcnow()

        await self.change_presence(game=discord.Game(name='snb?help'))

    async def on_command_error(self, exception, context):
        if isinstance(exception, commands.NoPrivateMessage):
            await context.send_message(context.message.author, 'This command cannot be used in private messages.')
        elif isinstance(exception, commands.DisabledCommand):
            await context.send_message(context.message.author, 'Sorry. This command is disabled and cannot be used.')
        elif isinstance(exception, commands.CommandInvokeError):
            log.error('Command error in {0.command.qualified_name}:'.format(context))
            traceback.print_tb(exception.original.__traceback__)
            log.error('{0.__class__.__name__}: {0}'.format(exception.original))

    async def on_command(self, ctx):
        if isinstance(ctx.channel, discord.abc.PrivateChannel):
            destination = 'Private Message'
        else:
            destination = f'#{ctx.channel.name} ({ctx.guild.name})'

        log.info('{0.author.name} in {1}: {0.content}'.format(ctx.message, destination))

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author.id == '129819557115199488' and message.content.lower().endswith('thunderlane'):
            await message.channel.send(message.channel, 'is best pony!')

        await self.process_commands(message)


if __name__ == '__main__':

    bot = StreamNotificationBot(
        command_prefix=get_prefix,
        description=description,
        pm_help=True,
        help_attrs=dict(hidden=True),
    )

    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

    bot.run(credentials['token'])

    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
