import logging
import os
import re
from functools import lru_cache
from typing import Dict, Type

from .service import Service, Streamer, chunks, anticache
from ...utils import errors

log = logging.getLogger(__name__)


def _get_service_id(api):
    try:
        service_id = api['channel']['_id']
    except KeyError:
        try:
            service_id = api['_id']
        except KeyError:
            raise errors.UnexpectedApiError

    return str(service_id)


class TwitchStreamer(Streamer):
    def __init__(self, *, db_id, service_id, channel_name):
        super().__init__(
            db_id=db_id,
            service_id=service_id,
            channel_name=channel_name
        )
        self.api = None

    @classmethod
    def from_api_response(cls, api, database):
        log.debug(api)
        service_id = _get_service_id(api)
        database_streamer = database.get(service_id, None)
        streamer = cls(
            db_id=database_streamer.db_id if database_streamer else None,
            service_id=service_id,
            channel_name=api.get('display_name', None) or api['channel']['display_name'],
        )
        streamer.api = api
        return service_id, streamer

    @property
    def service_name(self):
        return 'twitch'

    @property
    def thumbnail_url(self):
        return self.api['preview']['large'] + anticache()

    @property
    def service_icon_url(self):
        return 'https://i.imgur.com/miKaDpC.png'

    @property
    def channel_viewers(self):
        return self.api['viewers']

    @property
    def stream_url(self):
        return self.api['channel']['url']

    @property
    def avatar_url(self):
        return self.api.get('logo', None) or self.api['channel']['logo']


class Twitch(Service):
    """Twitch notifications"""

    def __init__(self, bot):
        super().__init__(
            bot=bot,
            service_name='twitch',
            api_key=os.environ['TOKEN_TWITCH'],
            update_period=60,
        )

    def __unload(self):
        self._cog__unload()

    async def __error(self, ctx, error):
        await self._cog__error(ctx, error)

    async def get_online_streamers(self) -> Dict[str, Streamer]:

        online_streamers = {}
        db = await self.database_cache()

        TWITCH_MAX_LIMIT = 100
        streamer_batch = chunks(db, TWITCH_MAX_LIMIT)
        for i, chunk in enumerate(streamer_batch):
            params = {
                'channel': ','.join(chunk),
                'limit': TWITCH_MAX_LIMIT,
                'offset': TWITCH_MAX_LIMIT * i,
            }
            response = await self.api_request(endpoint='/streams', params=params)
            for s in response['streams']:
                service_id, streamer = TwitchStreamer.from_api_response(
                    api=s,
                    database=db,
                )
                online_streamers[service_id] = streamer

        return online_streamers

    @lru_cache()
    async def get_streamer_from_API(self, username: str) -> TwitchStreamer:
        params = {
            'login': username,
        }
        response = await self.api_request(endpoint='/users', params=params)
        if response['_total'] != 1:
            raise errors.StreamerNotFoundError
        streamer = response['users'][0]
        return TwitchStreamer.from_api_response(
            api=streamer,
            database=await self.database_cache(),
        )[1]

    async def api_request(self, *, endpoint, params):
        headers = {
            'Accept': 'application/vnd.twitchtv.v5+json',
            'Client-ID': self.api_key,
        }
        async with self.bot.session.get('https://api.twitch.tv/kraken' + endpoint, headers=headers, params=params) as r:
            response = await r.json()
        return response

    async def validate_username(self, username: str) -> str:
        if not username:
            raise errors.InvalidUsernameError
        if not re.fullmatch(r'^\w{3,24}$', username, re.IGNORECASE):
            raise errors.InvalidUsernameError

        return username.lower()

    def stream_url(self, username: str) -> str:
        return f'https://twitch.tv/{username}'

    @property
    def streamer_class(self) -> Type[Streamer]:
        return TwitchStreamer
