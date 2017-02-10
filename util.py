import json
import logging
from logging.handlers import TimedRotatingFileHandler

from discord.ext import commands

initial_extensions = [
    'cogs.admin',
    'cogs.fun',
    'cogs.meta',
    'cogs.repl',
    'cogs.stream',
]


def setup_logger(name: str):
    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(module)s - %(message)s')

    rotating_handler = TimedRotatingFileHandler(filename='logs/logging.log', encoding='utf-8', when='midnight',
                                                backupCount=7, utc=True)
    rotating_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)

    log.addHandler(rotating_handler)
    log.addHandler(stream_handler)

    return log


def load_credentials():
    with open('credentials.json') as f:
        return json.load(f)


def is_owner_check(message):
    return message.author.id == '129819557115199488'


def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))
