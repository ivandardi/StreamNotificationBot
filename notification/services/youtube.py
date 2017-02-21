import logging
from typing import Iterable

from notification import database
from notification import httpclient
from .service import Service, Notification

log = logging.getLogger('stream_notif_bot')


class Youtube(Service):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def check_and_notify(self) -> Iterable[Notification]:

        notifications = []

        for streamer in database.get_all_streamers_from_service(service=self.service):

            streamer_is_online = await self._is_streamer_online(youtube_id=streamer['service_id'])

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
        youtube_id = await self._get_id_from_username(username)

        database.add_subscription(subscriber_id=subscriber_id, channel_id=channel_id,
                                  service=self.service, username=username, service_id=youtube_id)

    async def _is_streamer_online(self, youtube_id: str) -> bool:

        # Get stream info
        params = {
            'key': self.api_key,
            'channelId': youtube_id,
            'eventType': 'live',
            'type': 'video',
            'part': 'snippet',
        }
        async with httpclient.client.get('https://www.googleapis.com/youtube/v3/search', params=params) as r:
            try:
                info = await r.json()
                return info['pageInfo']['totalResults'] > 0
            except Exception as e:
                log.exception('_is_streamer_online: ', e)
                return False

    async def _get_id_from_username(self, username: str):

        # Get streamer ID
        params = {
            'key': self.api_key,
            'forUsername': username,
            'part': 'id',
        }
        async with httpclient.client.get('https://www.googleapis.com/youtube/v3/channels', params=params) as r:
            try:
                info = await r.json()
                if info['pageInfo']['totalResults'] <= 0:
                    return None
            except Exception as e:
                log.exception('_get_id_from_username: ', e)
                return None

        # We can access the streamer ID
        return info['items'][0]['id']

    @property
    def icon_url(self):
        return 'https://s-media-cache-ak0.pinimg.com/originals/c2/f0/6e/c2f06ec927ed43a5328ec30b4079da7f.png'

    @property
    def stream_url(self):
        return 'https://gaming.youtube.com/user/{}/live'

    @property
    def service(self):
        return 'youtube'
