import asyncio
import logging

import discord
from discord import Color
from discord.ext import commands

from notification import database
from notification import services
from utils.misc import credentials

log = logging.getLogger('stream_notif_bot')


async def validate_notification_channel(ctx: commands.Context, channel: discord.abc.GuildChannel):
    """Returns True if channel is valid"""

    # If there's no channel, then it will just list the user subscriptions
    if not channel:
        return True

    # If there isn't a guild aka it's a PrivateGuild
    if not ctx.guild:
        await ctx.send('This command doesn\'t work here.')
        return False

    # Only people with manage_channels can subscribe channels
    perms = channel.permissions_for(ctx.author)
    if not perms.manage_channels:
        await ctx.send('You don\'t have enough permissions to subscribe a channel.')
        return False

    # If channel doesn't belong to the list of text_channels of the guild
    if not discord.utils.find(lambda c: c == channel, ctx.guild.text_channels):
        await ctx.send('This channel doesn\'t belong to this guild.')
        return False

    return True


class Notifications:
    """
    Notification related commands.

    Supported services: Twitch and Picarto.

    == How to add a streamer to your notification list ==

    snb?add <service> <username>
    Example: snb?add picarto mykegreywolf

     == How to delete a streamer to your notification list ==

    snb?del <service> <username>
    Example: snb?del picarto mykegreywolf

    """

    def __init__(self, bot):
        self.bot = bot

        database.open_database()

        self.services = {
            'picarto': services.Picarto(credentials['picarto_API']),
            'twitch': services.Twitch(credentials['twitch_API']),
            # 'youtube': services.Youtube(credentials['youtube_API']),
        }

        self.task = self.bot.loop.create_task(self._check_streamers())

    def __unload(self):
        self.task.cancel()
        database.close_database()

    @commands.command(aliases=['subscribe'])
    async def add(self, ctx, service=None, username=None, notification_channel: discord.TextChannel = None):
        """Adds a streamer to your notification list.

        Supported services: Twitch and Picarto.

        It's case insensitive, meaning upper and lower case letters don't matter. MYKEgreyWOLF is the same as mykegreywolf.

        Aliases: subscribe

        == How to add a streamer to your notification list ==

        snb?add <service> <username>

        Example: snb?add picarto mykegreywolf

        == How to add a streamer to a channel's notification list ==

        snb?add <service> <username> <channel>

        Example: snb?add picarto mykegreywolf #general

        NOTE: You can only subscribe a channel if you have the manage_channels permission!

        """

        if not await validate_notification_channel(ctx, notification_channel):
            return

        subscriber = ctx.author if not notification_channel else notification_channel
        subscriber_id = str(subscriber.id)

        try:
            channel_id = await self._get_notification_channel_id(subscriber)
            service = self._validate_service(service)

            await self.services[service].add_subscription(subscriber_id=subscriber_id, channel_id=channel_id,
                                                          username=username)

        except database.InvalidServiceError:
            log.warning(f'Command add: Invalid service {service}.')
            await ctx.send(f'Invalid service.\n\nPlease take note of the proper format:\n\n'
                           '`snb?add <service> <username>`\n\n'
                           'Example: `snb?add picarto mykegreywolf`')
        except database.InvalidUsernameError:
            log.warning(f'Command add: Invalid username {username}.')
            await ctx.send(f'Invalid username {username}.')
        except services.StreamerNotFoundError:
            log.warning(f'Command add: streamer {username} not found.')
            await ctx.send(f'The streamer {username} doesn\'t exist.')
        except Exception as e:
            log.exception(f'add command exception: {e}')
            await ctx.send(f'Something bad happened. 😐')
        else:
            log.info(f'{subscriber} subscribed to {username}({service})')
            await ctx.send(
                f'{subscriber.name} will be notified when `{username}` goes online on {service.capitalize()}!')

    @commands.command(name='del', aliases=['unsubscribe', 'remove', 'delete'])
    async def _del(self, ctx, service=None, username=None, notification_channel: discord.TextChannel = None):
        """
        Deletes a streamer from your notification list.

        Supported services: Twitch and Picarto.

        It's case insensitive, meaning upper and lower case letters don't matter. MYKEgreyWOLF is the same as mykegreywolf.

        Aliases: delete, unsubscribe, remove

        == How to delete a streamer to your notification list ==

        snb?del <service> <username>
        Example: snb?del picarto mykegreywolf

        == How to delete a streamer to a channel's notification list ==

        snb?del <service> <username> <channel>

        Example: snb?del picarto mykegreywolf #general

        NOTE: You can only unsubscribe a channel if you have the manage_channels permission!

        """

        if not await validate_notification_channel(ctx, notification_channel):
            return

        channel = ctx.author if not notification_channel else notification_channel
        channel_id = await self._get_notification_channel_id(channel)

        try:
            service = self._validate_service(service)
            database.del_subscription(subscriber_id=channel_id, service=service, username=username)
        except database.InvalidServiceError:
            log.warning(f'Command del: Invalid service {service}.')
            await ctx.send(f'Invalid service.\n\nPlease take note of the proper format:\n\n'
                           '`snb?del <service> <username>`\n\n'
                           'Example: `snb?del picarto mykegreywolf`')
        except database.InvalidUsernameError:
            log.warning(f'Command del: Invalid username {username}.')
            await ctx.send(f'Invalid username {username}.')
        except Exception as e:
            log.exception(f'Command del: {e}')
            await ctx.send(f'Something bad happened. 😐')
        else:
            log.info(f'{ctx.message.author} unsubscribed from {username}({service})')
            await ctx.send(f'Unsubscribed from `{username}` on {service.capitalize()}!')

    @commands.command()
    async def list(self, ctx, notification_channel: discord.TextChannel = None):
        """
        Lists all the streams in your notification list.

        NOTE: only the usernames should show up here. If a full URL is showing, then you did something wrong.

        """

        if not await validate_notification_channel(ctx, notification_channel):
            return

        channel = ctx.author if not notification_channel else notification_channel

        subscriber_id = str(channel.id)

        subscriptions = database.get_subscriptions_from_subscriber(subscriber_id).fetchall()

        service_list = {
            k: '\n'.join(f'[{username}]({self.services[service].stream_url.format(username)})'
                         for username, service in subscriptions if service == k)
            for k in self.services.keys()
            }

        embed = discord.Embed(color=Color.blue())
        embed.set_author(name='Subscriptions')

        for service, streamer_list in service_list.items():
            if len(streamer_list) > 1024:
                await ctx.send('Go tell <@272829831304183808> to stop being lazy and implement proper pagination')
                log.warning('Embed value length is over 1024!')
                return
            if streamer_list:
                embed.add_field(name=service.capitalize(), value=streamer_list)

        if not embed.fields:
            embed.description = 'You\'re not subscribed to anyone yet!'

        await ctx.send(embed=embed)

    def _validate_service(self, service: str):
        """ Validates the service passed

        If the service is invalid, it raises a `InvalidServiceError`.
        Otherwise, it returns the validated service.

        :param service: the service to be validated
        :return: the validated service
        """

        if not service:
            raise database.InvalidServiceError

        service = service.lower()

        if service not in self.services:
            raise database.InvalidServiceError

        return service

    async def _get_notification_channel_id(self, channel) -> str:
        """Retrieves the ID of the channel where the notifications will be sent to

        If the channel is a User or Member, it will return the DMChannel related to that user.

        :param channel: The channel where the notifications will be sent to
        :return: The channel's ID
        """

        # `channel` might be an actual channel or an user
        if isinstance(channel, discord.abc.User):
            channel = await channel.create_dm()

        return str(channel.id)

    async def _check_streamers(self):
        """Background task that checks streamers for online status and notifies the channels subscribed to them"""

        log.info('Waiting for the bot to login...')
        await asyncio.sleep(5)
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            log.info('Checking online streamers...')
            try:
                for service_name, service in self.services.items():
                    for notif in await service.check_and_notify():
                        channel = self.bot.get_channel(int(notif.channel_id))
                        try:
                            await channel.send(embed=notif.get_embed())
                        except discord.Forbidden as e:
                            log.exception(f'Cannot send messages to {channel}')
                            log.exception(f'_check_and_notify: {e}')
                        except discord.HTTPException as e:
                            log.exception(f'Sending the message failed!')
                            log.exception(f'_check_and_notify: {e}')
                        except Exception as e:
                            log.exception(f'No idea what happened when trying to notify channel {notif.channel_id}!')
                            log.exception(f'_check_and_notify: {e}')
                        else:
                            log.info(f'Notified {channel} that {notif.username}({service_name}) is online')
            except Exception as e:
                # Probably a connection error
                log.exception(f'_check_streamers: {e}')

            await asyncio.sleep(45)


def setup(bot):
    bot.add_cog(Notifications(bot))
