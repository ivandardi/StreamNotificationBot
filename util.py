import json
import logging

from discord.ext import commands

initial_extensions = [
    'cogs.admin',
    'cogs.fun',
    'cogs.meta',
    'cogs.repl',
    'cogs.stream',
]


def setup_logger(name: str):
    handler = logging.FileHandler(filename='logging.log', encoding='utf-8', mode='w')

    formatter = logging.Formatter(fmt='%(asctime)s [%(levelname)s] %(module)s - %(message)s')
    handler.setFormatter(formatter)

    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    return log


def load_credentials():
    with open('credentials.json') as f:
        return json.load(f)


def is_owner_check(message):
    return message.author.id == '129819557115199488'


def is_owner():
    return commands.check(lambda ctx: is_owner_check(ctx.message))
