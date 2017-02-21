import logging
from typing import Iterable

from discord.utils import find
from twitch.api.v3 import streams

from notification import database
from .service import Service, Notification

log = logging.getLogger('stream_notif_bot')


class Twitch(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def check_and_notify(self) -> Iterable[Notification]:

        streamers = await self._get_online_streamers()

        notifications = []

        for streamer in database.get_all_streamers_from_service(service=self.service):

            streamer_is_online = find(lambda o: o['channel']['name'] == streamer['username'], streamers) is not None

            if streamer_is_online and not streamer['is_online']:

                for (channel_id,) in database.get_subscribers_from_streamer(streamer['streamer_id']):
                    notif = Notification(
                        channel_id=channel_id,
                        username=streamer['username'],
                        service=self.service,
                        icon_url=self.icon_url,
                        stream_url=self.stream_url.format(streamer['username']),
                    )
                    notifications.append(notif)

                database.set_online(streamer['streamer_id'], True)

            elif not streamer_is_online and streamer['is_online']:

                database.set_online(streamer['streamer_id'], False)

        return notifications

    async def add_subscription(self, *, subscriber_id: str, channel_id: str, username: str):
        database.add_subscription(subscriber_id=subscriber_id, channel_id=channel_id,
                                  service=self.service, username=username, service_id='TWITCH')

    async def _get_online_streamers(self):
        """Get all online streamers"""

        # NOTE: I don't know if the twitch API lib is currently using pagination

        streamers = database.get_all_streamers_from_service(service=self.service)
        return streams.all(client_id=self.api_key, channel=','.join(s['username'] for s in streamers))['streams']

    @property
    def icon_url(self):
        return 'https://i.imgur.com/miKaDpC.png'

    @property
    def stream_url(self):
        return 'https://twitch.tv/{}'

    @property
    def service(self):
        return 'twitch'
