import json
import logging
from logging.handlers import TimedRotatingFileHandler

initial_extensions = [
    'cogs.admin',
    'cogs.fun',
    'cogs.meta',
    'cogs.repl',
    'cogs.stream',
]

with open('credentials.json') as f:
    credentials = json.load(f)


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
