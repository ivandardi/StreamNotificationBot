import asyncio
import logging
import re
import sqlite3

import aiohttp
import discord
from discord import Forbidden, NotFound, Colour, InvalidArgument
from discord.ext import commands
from discord.utils import find

import util

log = logging.getLogger('stream_notif_bot')


def _get_icon_url(service: str):
    icon_url = {
        'picarto': 'https://picarto.tv/images/Picarto_logo.png',
        'twitch': 'https://i.imgur.com/miKaDpC.png',
        'youtube': 'https://s-media-cache-ak0.pinimg.com/originals/c2/f0/6e/c2f06ec927ed43a5328ec30b4079da7f.png',
    }

    return icon_url[service]


def _get_stream_url(service: str, username: str):
    service_url = {
        'picarto': 'https://picarto.tv/{}',
        'twitch': 'https://twitch.tv/{}',
        'youtube': 'https://gaming.youtube.com/user/{}/live',
    }

    return service_url[service].format(username)


def is_service_valid(service: str):
    return service == 'picarto' or service == 'twitch' or service == 'youtube'


class Notifications:
    """
    Notification related commands.

    Supported services: Twitch, Youtube and Picarto.

    == How to add a streamer to your notification list ==

    @StreamNotificationBot add <service> <username>
    Example: @StreamNotificationBot add picarto mykegreywolf

     == How to delete a streamer to your notification list ==

    @StreamNotificationBot del <service> <username>
    Example: @StreamNotificationBot del picarto mykegreywolf

    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = sqlite3.connect('db.sqlite3') # TODO use PonyORM
        self.client = aiohttp.ClientSession()

        credentials = util.load_credentials()
        self.key_picarto = credentials['picarto_API']
        self.key_twitch = credentials['twitch_API']
        self.key_youtube = credentials['youtube_API']

        self.task = self.bot.loop.create_task(self._check_streamers())

    def __unload(self):
        log.info('Unloading Notifications cog and closing database...')
        self.db.close()
        self.task.cancel()
        self.client.close()

    @commands.command(hidden=True)
    @util.is_owner()
    async def broadcast(self, *, message: str):
        users = self.db.execute('SELECT * FROM users')

        for user_id, channel_id in users:
            await self.bot.send_message(discord.Object(id=channel_id), message)

    @commands.command(aliases=['subscribe'], pass_context=True)
    async def add(self, ctx: commands.context.Context, service: str, username: str = None):
        """Adds a streamer to your notification list.

        Supported services: Twitch, Youtube and Picarto.

        It's case insensitive, meaning upper and lower case letters don't matter. MYKEgreyWOLF is the same as mykegreywolf.

        Aliases: subscribe

        == How to add a streamer to your notification list ==

        @StreamNotificationBot add <service> <username>
        Example: @StreamNotificationBot add picarto mykegreywolf

        """

        service = service.lower()
        if not is_service_valid(service) or username is None:
            await self.bot.send_message(ctx.message.author,
                                        f'Command error.\n\nPlease take note of the proper format:\n\n'
                                        '@StreamNotificationBot add <service> <username>\n'
                                        'Example: @StreamNotificationBot add picarto mykegreywolf')
            return

        username = username.lower()

        if not re.fullmatch(r'^\w{3,24}$', username, re.IGNORECASE):
            log.warning(f'Command add: Invalid username {username}.')
            await self.bot.send_message(ctx.message.author, f'Invalid username {username}.')
            return

        if not ctx.message.channel.is_private:
            log.warning('Command add: This command only works in private messages!')
            await self.bot.send_message(ctx.message.author, 'This command only works in private messages!')
            return

        user_id = self._db_add_user(ctx.message.author.id, ctx.message.channel.id)
        streamer_id = self._db_add_streamer(service, username)
        self._db_add_subscription(user_id, streamer_id)

        log.info(f'{ctx.message.author} subscribed to {username}')
        await self.bot.send_message(ctx.message.author,
                                    f'You\'ll will be notified when `{username}` goes online!')

    @commands.command(name='del', aliases=['unsubscribe', 'remove', 'delete'], pass_context=True)
    async def _del(self, ctx: commands.context.Context, service: str, username: str = None):
        """
        Deletes a streamer from your notification list.

        Supported services: Twitch, Youtube and Picarto.

        It's case insensitive, meaning upper and lower case letters don't matter. MYKEgreyWOLF is the same as mykegreywolf.

        Aliases: delete, unsubscribe, remove

        == How to delete a streamer to your notification list ==

        @StreamNotificationBot del <service> <username>
        Example: @StreamNotificationBot del picarto mykegreywolf

        """

        service = service.lower()
        if not is_service_valid(service) or username is None:
            await self.bot.send_message(ctx.message.author,
                                        f'Command error.\n\nPlease take note of the proper format:\n\n'
                                        '@StreamNotificationBot del <service> <username>\n'
                                        'Example: @StreamNotificationBot del picarto mykegreywolf')
            return

        username = username.lower()

        sql = '''
        DELETE FROM subscriptions
              WHERE streamer_id IN (
                    SELECT streamer_id
                      FROM streamers
                     WHERE service = ?
                       AND username = ?
              )
        '''
        self._db_execute(sql, service, username)

        await self.bot.send_message(ctx.message.author, 'Streamer deleted.')

    @commands.command(pass_context=True)
    async def list(self, ctx: commands.context.Context):
        """
        Lists all the streams in your notification list.

        NOTE: only the usernames should show up here. If a full URL is showing, then you did something wrong.

        """

        sql = '''
        SELECT username,
               service
          FROM subscriptions
               INNER JOIN users
               USING (user_id)
               INNER JOIN streamers
               USING (streamer_id)
         WHERE user_id = ?
        ORDER BY username
        '''
        subs = self.db.execute(sql, [ctx.message.author.id]).fetchall()

        embed = discord.Embed()
        embed.colour = Colour.blue()
        embed.set_author(name='Streamers you\'re subscribed to')

        picarto_streams = '\n'.join(
            ['[{0}](https://picarto.tv/{0})'.format(username) for username, service in subs if service == 'picarto'])

        twitch_streams = '\n'.join(
            ['[{0}](https://twitch.tv/{0})'.format(username) for username, service in subs if service == 'twitch'])

        youtube_streams = '\n'.join(
            ['[{0}](https://gaming.youtube.com/user/{0}/live)'.format(username) for username, service in subs if
             service == 'youtube'])

        if len(picarto_streams) > 1024 or len(twitch_streams) > 1024 or len(youtube_streams) > 1024:
            await self.bot.send_message(ctx.message.author,
                                        'Go tell MelodicStream#1336 to stop being lazy and implement proper pagination')
            log.warning('Embed value length is over 1024!')
            return

        if picarto_streams:
            embed.add_field(name='Picarto', value=picarto_streams)

        if twitch_streams:
            embed.add_field(name='Twitch', value=twitch_streams)

        if youtube_streams:
            embed.add_field(name='Youtube', value=youtube_streams)

        await self.bot.send_message(ctx.message.author, embed=embed)

    def _db_add_user(self, user_id: str, channel_id: str):
        """
        Adds a new user to the users table
        :param user_id: User id
        :param channel_id: User's private channel's ID
        :return: inserted streamer's ID
        """

        sql = '''
        INSERT OR IGNORE INTO users (user_id, channel_id)
        VALUES (?, ?)
        '''
        self._db_execute(sql, user_id, channel_id)
        return user_id

    def _db_add_streamer(self, service: str, username: str):
        """
        Adds a new streamer to the streamers table
        :param service: Streaming service of the user
        :param username: Username of the user
        :return: inserted streamer's ID
        """

        sql = '''
        INSERT OR IGNORE INTO streamers (username, service)
        VALUES (?, ?)
        '''
        self._db_execute(sql, username, service)

        sql = '''
        SELECT streamer_id
          FROM streamers
         WHERE username = ?
           AND service = ?
        '''
        streamer_id = self.db.execute(sql, [username, service])

        return streamer_id.fetchone()[0]

    def _db_add_subscription(self, user_id, streamer_id):
        """
        Adds a new subscription to the subscriptions table
        :param user_id: Discord ID of the user
        :param streamer_id: ID of the streamer
        """

        sql = '''
        INSERT OR IGNORE INTO subscriptions (user_id, streamer_id)
        VALUES (?, ?)
        '''
        self._db_execute(sql, user_id, streamer_id)

    async def _check_streamers(self):
        await self.bot.wait_until_ready()

        while not self.bot.is_closed:
            try:
                await self._check_and_notify()
            except Exception as e:
                # Probably a connection error
                log.error(f'_check_streamers: {e}')

            await asyncio.sleep(45)

    async def _check_and_notify(self):

        # Get all online streamers from picarto
        try:
            params = {'key': self.key_picarto}
            async with self.client.get('https://api.picarto.tv/online/all', params=params) as r:
                if r.status == 200:
                    pstreams = await r.json()
        except Exception as e:
            # Probably reached the 3000 checks/day limit
            log.exception(f'_check_and_notify: {type(e).__name__}: {e}')
            pstreams = None

        # Get all subscriptions
        streamers = self.db.execute('SELECT * FROM streamers')

        for streamer_id, username, service, online in streamers:

            streamer_is_online = await self._is_streamer_online(service, username, pstreams)

            if streamer_is_online and online == 0:

                stream_url = _get_stream_url(service, username)

                emb = discord.Embed()
                emb.set_author(name=f'{username} is online on {service.capitalize()}!',
                               url=stream_url,
                               icon_url=_get_icon_url(service))
                emb.description = stream_url
                emb.colour = Colour.orange()

                sql = '''
                SELECT user_id,
                       channel_id
                  FROM users
                       INNER JOIN subscriptions
                       USING (user_id)
                       INNER JOIN streamers
                       USING (streamer_id)
                 WHERE streamer_id = ?
                '''
                subs = self.db.execute(sql, [streamer_id])

                for user_id, channel_id in subs:
                    try:
                        msg = await self.bot.send_message(discord.Object(id=channel_id), embed=emb)
                        log.info(f'Notified {msg.channel.recipients[0].name} that {username} is online')
                    except Forbidden as e:
                        log.exception(f'User {user_id} cannot accept DMs!')
                        log.exception(f'_check_and_notify: {e}')
                    except NotFound as e:
                        log.exception(f'User {user_id} was not found!')
                        log.exception(f'_check_and_notify: {e}')
                    except InvalidArgument as e:
                        log.exception(f'User {user_id} was an invalid destination!')
                        log.exception(f'_check_and_notify: {e}')

                self._set_online(streamer_id, 1)
            elif not streamer_is_online and online == 1:
                self._set_online(streamer_id, 0)

    async def _is_streamer_online(self, service: str, username: str, pstreams: list) -> bool:

        if service == 'picarto' and pstreams is not None:
            return find(lambda o: o['channel_name'].lower() == username, pstreams) is not None

        if service == 'twitch':
            params = {'client_id': self.key_twitch}
            async with self.client.get(f'https://api.twitch.tv/kraken/streams/{username}', params=params) as r:
                if r.status != 200:
                    return False

                stream = await r.json()
                return stream['stream'] is not None if 'stream' in stream else False

        if service == 'youtube':
            # Get streamer ID
            params = {
                'key': self.key_youtube,
                'forUsername': username,
                'part': 'id',
            }
            async with self.client.get('https://www.googleapis.com/youtube/v3/channels', params=params) as r:
                if r.status != 200:
                    return False

                info = await r.json()
                if info['pageInfo']['totalResults'] <= 0:
                    return False

                # We can access the streamer ID
                streamer_id = info['items'][0]['id']


            # Get stream info
            params = {
                'key': self.key_youtube,
                'channelId': streamer_id,
                'eventType': 'live',
                'type': 'video',
                'part': 'snippet',
            }
            async with self.client.get('https://www.googleapis.com/youtube/v3/search', params=params) as r:
                if r.status == 200:
                    info = await r.json()
                    return info['pageInfo']['totalResults'] > 0

        return False

    def _set_online(self, streamer_id: str, status: int):
        sql = '''
        UPDATE streamers
           SET is_online = ?
         WHERE streamer_id = ?
        '''
        self._db_execute(sql, status, streamer_id)

    def _db_execute(self, sql: str, *args):
        cur = self.db.cursor()
        cur.execute(sql, args)
        self.db.commit()
        return cur


def setup(bot):
    bot.add_cog(Notifications(bot))
