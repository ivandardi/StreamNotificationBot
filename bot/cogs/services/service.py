import asyncio
import itertools
import logging
import random
from abc import ABC, abstractmethod
from typing import Dict, Type

import discord
from discord.ext import commands

from ...utils import errors, strings

log = logging.getLogger(__name__)


def anticache():
    rand = lambda: random.randint(0, 2 ** 64 - 1)
    return f'?useless_int={rand()}'


def chunks(collection, n):
    """Yield successive n-sized chunks from collection."""
    collection = iter(collection)
    while True:
        chunk = list(itertools.islice(collection, n))
        if not chunk:
            return
        yield chunk


async def validate_notification_channel(ctx, channel: discord.abc.GuildChannel):
    """Returns True if channel is valid"""

    if not channel:
        return channel

    # If there isn't a guild aka it's a PrivateGuild
    if not ctx.guild:
        raise errors.InvalidChannelError("This command doesn't work here.")

    # Only people with manage_channels can subscribe channels
    perms = channel.permissions_for(ctx.author)
    if not perms.manage_channels:
        raise errors.InvalidChannelError("You don't have enough permissions to subscribe the channel.")

    return channel


class Subscriber:
    def __init__(self, subscriber, notification_channel_id):
        self.subscriber = subscriber
        self.id = self.subscriber.id
        self.notification_channel_id = notification_channel_id

    @classmethod
    async def get_subscriber_id_and_notification_channel(cls, subscriber):
        if isinstance(subscriber, (discord.User, discord.Member)):
            subscriber_channel = await subscriber.create_dm()
            notification_channel_id = subscriber_channel.id
            return cls(subscriber, notification_channel_id)
        if isinstance(subscriber, discord.TextChannel):
            notification_channel_id = subscriber.id
            return cls(subscriber, notification_channel_id)
        raise ValueError("Passed subscriber isn't an User nor a TextChannel")


class Streamer(ABC):
    def __init__(self, *, db_id, service_id, channel_name):
        self.db_id = db_id
        self.service_id = service_id
        self.channel_name = channel_name

    @classmethod
    def from_database_record(cls, record):
        return cls(
            db_id=record['streamer_id'],
            service_id=record['service_id'],
            channel_name=record['username'],
        )

    def create_notification_embed(self):
        embed = discord.Embed(
            colour=discord.Color.green(),
            url=self.stream_url,
            description=self.stream_url
        )
        embed.set_author(
            name=f'{self.channel_name} is online on {self.service_name.capitalize()}!',
            url=self.stream_url,
            icon_url=self.service_icon_url,
        )
        embed.set_image(url=self.thumbnail_url)
        embed.set_thumbnail(url=self.avatar_url)
        embed.set_footer(text=self.service_name.capitalize())
        embed.add_field(name='Viewers', value=self.channel_viewers)

        return embed

    def __eq__(self, other):
        return self.service_id == other.service_id

    @property
    @abstractmethod
    def service_name(self):
        pass

    @property
    @abstractmethod
    def thumbnail_url(self):
        pass

    @property
    @abstractmethod
    def service_icon_url(self):
        pass

    @property
    @abstractmethod
    def stream_url(self):
        pass

    @property
    @abstractmethod
    def avatar_url(self):
        pass

    @property
    @abstractmethod
    def channel_viewers(self):
        pass


class Service(ABC):
    """Base Service class"""

    def __init__(self, *, bot, service_name, api_key, update_period):
        self.bot = bot
        self.service_name = service_name
        self.api_key = api_key
        self.update_period = update_period
        self.live_streamers_cache = {}
        setattr(self, self.service_name, self._make_commands())

        self.task = self.bot.loop.create_task(self._notify_subscribers())

    def _cog__unload(self):
        self.task.cancel()

    async def _cog__error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            original = error.original
            if isinstance(original, errors.InvalidUsernameError):
                await ctx.send(f'Invalid username: {str(original)}')
            if isinstance(original, errors.StreamerNotFoundError):
                await ctx.send(f'Streamer not found: {str(original)}')
            if isinstance(original, errors.NotSubscribedError):
                await ctx.send(f"You're not subscriber to the streamer {str(original)}")
            if isinstance(original, errors.StreamerAlreadyExists):
                await ctx.send("You're already subscribed to this streamer!")
            if isinstance(original, errors.InvalidChannelError):
                await ctx.send(str(original))
        if isinstance(error, commands.BadArgument):
            await ctx.send(str(error))

    def _make_commands(self):
        group = commands.Group(
            name=self.service_name,
            callback=self._group_command,
            help=self._make_help_string(strings.group_command_help),
        )
        group.instance = self
        cmd = commands.Command(
            name='add',
            aliases=['subscribe'],
            callback=self._add_command,
            help=self._make_help_string(strings.add_command_help),
        )
        cmd.instance = self
        group.add_command(cmd)
        cmd = commands.Command(
            name='del',
            aliases=['unsubscribe', 'remove', 'delete'],
            callback=self._del_command,
            help=self._make_help_string(strings.del_command_help),
        )
        cmd.instance = self
        group.add_command(cmd)
        cmd = commands.Command(
            name='list',
            callback=self._list_command,
            help=self._make_help_string(strings.list_command_help),
        )
        cmd.instance = self
        group.add_command(cmd)

        return group

    def _make_help_string(self, help_string):
        return help_string.format(service_upper=self.service_name.capitalize(), service=self.service_name)

    @staticmethod
    async def _group_command(self, ctx):
        """group command"""
        if ctx.invoked_subcommand is None:
            await ctx.send(f'```{self._make_help_string(strings.group_command_help)}```')

    @staticmethod
    async def _add_command(self, ctx, username: str = None, channel: discord.TextChannel = None):
        """add command"""
        username = await self.validate_username(username)
        channel = await validate_notification_channel(ctx, channel)
        async with ctx.typing():
            subscriber = await Subscriber.get_subscriber_id_and_notification_channel(channel or ctx.author)
            await self._subscribe_to_streamer(subscriber, username)

        await ctx.send(f'{subscriber.subscriber} subscribed to {username} successfully!')

    async def _subscribe_to_streamer(self, subscriber: Subscriber, username: str):
        streamer = await self.get_streamer_from_API(username)
        await self._add_subscription(subscriber, streamer)

    async def _add_subscription(self, subscriber: Subscriber, streamer: Streamer):
        await self.bot.database.add_subscription(
            subscriber_id=subscriber.id,
            channel_id=subscriber.notification_channel_id,
            service=self.service_name,
            username=streamer.channel_name.lower(),
            service_id=streamer.service_id,
        )

    @staticmethod
    async def _del_command(self, ctx, username: str = None, channel: discord.TextChannel = None):
        """del command"""
        username = await self.validate_username(username)
        channel = await validate_notification_channel(ctx, channel)
        async with ctx.typing():
            subscriber = await Subscriber.get_subscriber_id_and_notification_channel(channel or ctx.author)
            await self._del_subscription(subscriber, username)

        await ctx.send(f'{subscriber.subscriber} unsubscribed to {username} successfully!')

    async def _del_subscription(self, subscriber: Subscriber, streamer_username: str):
        await self.bot.database.del_subscription(
            subscriber_id=subscriber.id,
            service=self.service_name,
            username=streamer_username,
        )

    @staticmethod
    async def _list_command(self, ctx, channel: discord.TextChannel = None):
        """list command"""
        subscriber = await Subscriber.get_subscriber_id_and_notification_channel(channel or ctx.author)
        channel = await validate_notification_channel(ctx, channel)
        async with ctx.typing():
            streamers = await self.bot.database.get_subscriptions_from_subscriber(subscriber.id, self.service_name)
            embed = self._make_list_embed(streamers, subscriber.subscriber)

        await ctx.send(embed=embed)

    def _make_list_embed(self, streamers, subscriber):
        streams = '\n'.join(f'[{username}]({self.stream_url(username)})' for (username,) in streamers)
        if len(streams) > 1024:
            log.warning('Embed value length is over 1024!')
            return discord.Embed(
                description='Please complain about embed pagination in https://discord.gg/xrzJhqq',
                color=discord.Color.red()
            )

        embed = discord.Embed(description=streams, color=discord.Color.blue())
        embed.set_author(name=f"{self.service_name.capitalize()} subscriptions for {subscriber}")
        return embed

    async def on_private_channel_delete(self, channel: discord.abc.PrivateChannel):
        await self._remove_channels_from_database(channel)

    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        await self._remove_channels_from_database(channel)

    async def on_guild_remove(self, guild: discord.Guild):
        await self._remove_channels_from_database(*guild.channels)

    async def _remove_channels_from_database(self, *channels):
        for channel in channels:
            if isinstance(channel, discord.TextChannel):
                await self.bot.database.delete_subscriber(channel.id)
                log.info('Deleted subscriber channel %s from database', channel)

    async def database_streamers(self):
        database_streamers = await self.bot.database.get_all_streamers_from_service(service=self.service_name)
        database_streamers = {
            s['service_id']: self.streamer_class.from_database_record(s) for s in database_streamers
        }
        return database_streamers

    async def _notify_subscribers(self):
        while not self.bot.is_closed():
            await self.bot.wait_until_ready()
            try:
                log.debug('Checking %s streamers', self.service_name)
                currently_online_streamers = await self.get_online_streamers()
                for service_id, streamer in currently_online_streamers.items():
                    if service_id not in self.live_streamers_cache:
                        await self._notify_subscribers_of_streamer(streamer)
                self.live_streamers_cache = currently_online_streamers
            except Exception as e:  # noqa
                log.exception('notify_subscribers: %s', e)

            await asyncio.sleep(self.update_period)

    async def _notify_subscribers_of_streamer(self, streamer: Streamer):
        subscribers = await self.bot.database.get_subscribers_from_streamer(streamer.db_id)
        for (notification_channel_id,) in subscribers:
            channel = self.bot.get_channel(notification_channel_id)
            if channel:
                notification_embed = streamer.create_notification_embed()
                try:
                    await channel.send(embed=notification_embed)
                except Exception as e:
                    log.exception('_notify_subscribers_of_streamer: %s', e)
            else:
                log.error('Notification channel not found: %s', notification_channel_id)

    @abstractmethod
    async def get_online_streamers(self) -> Dict[str, Streamer]:
        """Retrieves all streamers that are online and that have
        at least one subscriber in the database
        """
        raise NotImplementedError

    @abstractmethod
    async def get_streamer_from_API(self, username: str) -> Streamer:
        raise NotImplementedError

    @abstractmethod
    async def validate_username(self, username: str):
        raise NotImplementedError

    @abstractmethod
    def stream_url(self, username: str) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def streamer_class(self) -> Type[Streamer]:
        raise NotImplementedError
