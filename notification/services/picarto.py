import logging
from typing import Iterable

from notification import database
from notification import httpclient
from .service import Service, Notification, StreamerNotFoundError

log = logging.getLogger('stream_notif_bot')


class Picarto(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def check_and_notify(self) -> Iterable[Notification]:

        pstreams = await self._get_online_streamers()
        if not pstreams:
            return []

        notifications = []

        all_streamers = database.get_all_streamers_from_service(service=self.service)
        for streamer_id, service_id, service, username, is_online in all_streamers:

            streamer_is_online = username in pstreams

            if streamer_is_online and not is_online:

                for row in database.get_subscribers_from_streamer(streamer_id):
                    notif = Notification(
                        subscriber_id=int(row['subscriber_id']),
                        channel_id=int(row['channel_id']),
                        username=username,
                        icon_url=self.icon_url,
                        stream_url=self.stream_url.format(username),
                    )
                    notifications.append(notif)

                database.set_online(streamer_id, 1)

            elif not streamer_is_online and is_online:

                database.set_online(streamer_id, 0)

        return notifications

    async def add_subscription(self, *, subscriber_id: str, channel_id: str, username: str):

        # Validate the username before we send a request
        username = database.validate_username(username)

        async with httpclient.client.get(f'https://api.picarto.tv/channel/{username}/{self.api_key}') as r:
            if r.status != 200:
                raise StreamerNotFoundError

            response = await r.json()
            service_id = response['id']
            database.add_subscription(subscriber_id=subscriber_id, channel_id=channel_id,
                                      service=self.service, username=username, service_id=service_id)

    async def _get_online_streamers(self):
        """Get all online streamers"""
        try:
            params = {'key': self.api_key}
            async with httpclient.client.get('https://api.picarto.tv/online/all', params=params) as r:
                streams = await r.json()

            pstreams = list(map(lambda elem: elem['channel_name'].lower(), streams))
        except Exception as e:
            # Probably reached the 3000 checks/day limit
            log.exception(f'check_and_notify: {type(e).__name__}: {e}')
            pstreams = None

        return pstreams

    @property
    def icon_url(self):
        return 'https://picarto.tv/images/Picarto_logo.png'

    @property
    def stream_url(self):
        return 'https://picarto.tv/{}'

    @property
    def service(self):
        return 'picarto'
