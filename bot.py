import datetime
import logging
import traceback

import discord
from discord.ext import commands

import util
from util import initial_extensions

description = """
Hello! I am a bot created to notify you when streamers go online!
Author: MelodicStream#1336


==== HOW TO USE THE BOT ====

Currently supported services: Twitch, Youtube and Picarto.

To add a streamer to your subscription list, use the following command:

@StreamNotificationBot add <service> <username>
Example: @StreamNotificationBot add picarto mykegreywolf

For more help about any command, type @StreamNotificationBot help <command>.
Example: @StreamNotificationBot help add


==== COMMANDS ====

"""

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)

log = util.setup_logger('stream_notif_bot')

help_attrs = dict(hidden=True)

bot = commands.Bot(command_prefix=commands.when_mentioned, description=description, pm_help=True, help_attrs=help_attrs)


@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.NoPrivateMessage):
        await bot.send_message(ctx.message.author, 'This command cannot be used in private messages.')
    elif isinstance(error, commands.DisabledCommand):
        await bot.send_message(ctx.message.author, 'Sorry. This command is disabled and cannot be used.')
    elif isinstance(error, commands.CommandInvokeError):
        log.error('Command error')
        log.error('In {0.command.qualified_name}:'.format(ctx))
        traceback.print_tb(error.original.__traceback__)
        log.error('{0.__class__.__name__}: {0}'.format(error.original))


@bot.event
async def on_ready():
    print('Logged in as:')
    print('Username: ' + bot.user.name)
    print('ID: ' + bot.user.id)
    print('------')
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.datetime.utcnow()

    await bot.change_presence(game=discord.Game(name='mention help'))


@bot.event
async def on_command(command, ctx):
    message = ctx.message
    if message.channel.is_private:
        destination = 'Private Message'
    else:
        destination = '#{0.channel.name} ({0.server.name})'.format(message)

    log.info('{0.author.name} in {1}: {0.content}'.format(message, destination))


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.author.id == '129819557115199488' and message.content.lower().endswith('thunderlane'):
        await bot.send_message(message.channel, 'is best pony!')

    await bot.process_commands(message)


if __name__ == '__main__':
    token = util.load_credentials()['token']

    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print('Failed to load extension {}\n{}: {}'.format(extension, type(e).__name__, e))

    bot.run(token)
    handlers = log.handlers[:]
    for hdlr in handlers:
        hdlr.close()
        log.removeHandler(hdlr)
