import atexit
import logging
import re
import sqlite3

import discord
from discord.ext import commands

log = logging.getLogger('stream_notif_bot')

################################################################################
# Globals
################################################################################

# Database connection
_db = None

# Prefix cache
_pcache = None


def open_database():
    global _db
    if not _db:
        log.info('Opening database...')
        _db = sqlite3.connect('db.sqlite3')
        _db.row_factory = sqlite3.Row


@atexit.register
def close_database():
    global _db
    if not _db:
        log.info('Closing database safely...')
        _db.close()
        _db = None


# todo: add `remove_subscriber` if the user doesn't allow DM


################################################################################
# Exceptions
################################################################################

class InvalidServiceError(Exception):
    pass


class InvalidUsernameError(Exception):
    pass


################################################################################
# Database access functions
################################################################################


def validate_username(username: str):
    """ Validates the username passed

    A valid username matches the regex `^\w{3,24}$`.

    If the username is invalid, it raises a `InvalidUsernameError`.
    Otherwise, it returns the validated username.

    :param username: the username to be validated
    :return: the validated username
    """

    if not username:
        raise InvalidUsernameError

    if username is None or not re.fullmatch(r'^\w{3,24}$', username, re.IGNORECASE):
        raise InvalidUsernameError

    return username


def add_subscriber(*, subscriber_id: str, channel_id: str):
    """Adds a new subscriber to the subscribers table

    :param subscriber_id: Subscriber id
    :param channel_id: ID of the channel where the notification will be sent
    """

    sql = '''
    INSERT OR IGNORE INTO subscribers (subscriber_id, channel_id)
    VALUES (?, ?)
    '''
    with _db:
        _db.execute(sql, (subscriber_id, channel_id))


def add_streamer(*, service: str, username: str, service_id: str):
    """Adds a new streamer to the streamers table

    :param service: Streaming service of the user
    :param username: Username of the user
    :param service_id: the internal ID of the streamer in whichever service they're in
    :return: inserted streamer's ID
    """

    username = validate_username(username)

    sql = '''
    INSERT OR IGNORE INTO streamers (username, service, service_id)
    VALUES (?, ?, ?)
    '''
    with _db:
        _db.execute(sql, (username, service, service_id))

    sql = '''
    SELECT streamer_id
      FROM streamers
     WHERE username = ?
       AND service = ?
    '''
    return _db.execute(sql, (username, service)).fetchone()[0]


def add_subscription(*, subscriber_id: str, channel_id: str, service: str, username: str, service_id: str):
    """Adds a new subscription

    :param service_id: the internal ID of the streamer in whichever service they're in
    :param subscriber_id: Subscriber id
    :param channel_id: ID of the channel where the notification will be sent
    :param service: Streaming service of the user
    :param username: Username of the user
    """

    username = validate_username(username)

    add_subscriber(subscriber_id=subscriber_id, channel_id=channel_id)
    streamer_id = add_streamer(service=service, username=username, service_id=service_id)

    sql = '''
    INSERT OR IGNORE INTO subscriptions (subscriber_id, streamer_id)
    VALUES (?, ?)
    '''
    with _db:
        _db.execute(sql, (subscriber_id, streamer_id))


def del_subscription(*, subscriber_id: str, service: str, username: str):
    """Deletes a subscription

    If the subscription doesn't exist, it just fails silently.

    :param subscriber_id: Subscriber id
    :param service: Streaming service of the user
    :param username: Username of the user
    """

    username = validate_username(username)

    sql = '''
    DELETE FROM subscriptions
    WHERE streamer_id IN (
          SELECT streamer_id
            FROM streamers
           WHERE service = ?
             AND username = ?
    )
    AND subscriber_id = ?
    '''
    with _db:
        _db.execute(sql, (service, username, subscriber_id))


def set_online(streamer_id: int, status: int):
    """Sets the online status of a streamer

    :param streamer_id: the ID of the streamer
    :param status: the new status of the streamer
    """

    sql = '''
    UPDATE streamers
       SET is_online = ?
     WHERE streamer_id = ?
    '''
    with _db:
        _db.execute(sql, (status, streamer_id))


def get_all_streamers_from_service(*, service: str):
    """Returns all streamers related to a service

    :param service: The service to get the streamers from
    :return: The streamers related to the service
    """

    sql = '''
    SELECT *
      FROM streamers
     WHERE service = ?
    '''
    return _db.execute(sql, (service,))


def get_all_subscribers():
    """Returns all the subscribers

    :return: Iterable of IDs of the subscribers
    """
    sql = '''
    SELECT channel_id
      FROM subscribers
    '''
    return _db.execute(sql)


def get_subscribers_from_streamer(streamer_id: int):
    """Returns all the subscribers that are subscribed to a streamer

    :param streamer_id: ID of the streamer
    :return: Iterable of channel IDs of the streamer's subscribers
    """
    sql = '''
    SELECT channel_id
      FROM subscribers
           INNER JOIN subscriptions
           USING (subscriber_id)
           INNER JOIN streamers
           USING (streamer_id)
     WHERE streamer_id = ?
    '''
    return _db.execute(sql, (streamer_id,))


def get_subscriptions_from_subscriber(subscriber_id: str):
    """Returns all the streamers that the subscriber is subscribed to

    :param subscriber_id: ID of the subscriber
    :return: Iterable of (username, service) of all the streamers that the subscriber is currently subscribed to
    """
    sql = '''
    SELECT username,
           service
      FROM subscriptions
           INNER JOIN subscribers
           USING (subscriber_id)
           INNER JOIN streamers
           USING (streamer_id)
     WHERE subscriber_id = ?
    ORDER BY username
    '''
    return _db.execute(sql, (subscriber_id,))


################################################################################
# Prefix functions
################################################################################

def change_prefix(guild_id: str, prefix: str):
    """Changes the prefix related to a server

    :param guild_id: ID of the guild
    :param prefix: The new prefix
    """
    sql = '''
    INSERT OR REPLACE INTO prefixes (guild_id, prefix)
    VALUES (?, ?)
    '''
    with _db:
        _db.execute(sql, (guild_id, prefix))

    update_prefix_cache()


def get_prefix(bot, msg):
    """Function that should be given as the `command_prefix` argument of Discord clients

    The bot has 3 prefixes that always work:

    1. A mention followed by a space
    2. snb!
    3. snb?

    Additionally, if the bot is called in a DM channel, it also listens to two more prefixes:

    1. !
    2. ?

    :param bot: The current bot
    :param msg: The current message
    :return: A list of prefixes that the bot is listening to
    """
    if msg.guild:

        # There's a guild to check
        guild_id = str(msg.guild.id)

        # If there's something in the cache, then get that prefix, else return an empy list
        prefix = [_pcache[guild_id]] if guild_id in _pcache else []
    else:
        prefix = []

    # Extend the list with the default commands
    prefix.extend([commands.when_mentioned(bot, msg), 'snb!', 'snb?'])

    # If it's a private channel allow the bot to be called with no prefix
    if isinstance(msg.channel, discord.abc.PrivateChannel):
        prefix += ['!', '?']

    return prefix


def update_prefix_cache():
    """Updates the prefix cache from the database"""

    sql = '''
    SELECT *
      FROM prefixes
    '''
    prefixes = _db.execute(sql)

    global _pcache
    _pcache = {guild_id: prefix for guild_id, prefix in prefixes}

    log.info('Updated prefix cache')


# Call it once to fill the cache
open_database()
update_prefix_cache()
