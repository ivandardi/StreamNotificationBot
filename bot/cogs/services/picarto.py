import logging
import os
import re
from functools import lru_cache
from typing import Dict, Type

from .service import Service, Streamer, anticache
from ...utils import errors

log = logging.getLogger(__name__)


class PicartoStreamer(Streamer):
    def __init__(self, *, db_id, service_id, channel_name):
        super().__init__(
            db_id=db_id,
            service_id=service_id,
            channel_name=channel_name
        )
        self.api = None

    @classmethod
    def from_api_response(cls, api, database):
        service_id = str(api['user_id'])
        database_streamer = database.get(service_id, None)
        streamer = cls(
            db_id=database_streamer.db_id if database_streamer else None,
            service_id=service_id,
            channel_name=api['name'],
        )
        streamer.api = api
        return service_id, streamer

    @property
    def service_name(self):
        return 'picarto'

    @property
    def thumbnail_url(self):
        return f'https://thumb.picarto.tv/thumbnail/{self.channel_name.lower()}.jpg' + anticache()

    @property
    def service_icon_url(self):
        return 'https://picarto.tv/images/Picarto_logo.png'

    @property
    def channel_viewers(self):
        return self.api['viewers']

    @property
    def stream_url(self):
        return f'https://picarto.tv/{self.channel_name}'

    @property
    def avatar_url(self):
        return f'https://picarto.tv/user_data/usrimg/{self.channel_name.lower()}/dsdefault.jpg'


class Picarto(Service):
    """Picarto notifications"""

    def __init__(self, bot):
        super().__init__(
            bot=bot,
            service_name='picarto',
            api_key=os.environ['TOKEN_PICARTO'],
            update_period=60,
        )

    def __unload(self):
        self._cog__unload()

    async def __error(self, ctx, error):
        await self._cog__error(ctx, error)

    async def get_online_streamers(self) -> Dict[str, Streamer]:
        all_online_streamers = await self.get_all_online_streamers()

        db = await self.database_cache()
        online_streamers = dict(
            PicartoStreamer.from_api_response(s, db)
            for s in all_online_streamers
            if str(s['user_id']) in db
        )

        return online_streamers

    @lru_cache()
    async def get_streamer_from_API(self, username: str) -> PicartoStreamer:
        streamer = await self.get_channel_by_name(username)
        if not streamer:
            raise errors.StreamerNotFoundError(username)
        return PicartoStreamer.from_api_response(
            api=streamer,
            database=await self.database_cache(),
        )[1]

    async def get_all_online_streamers(self):
        params = {
            'adult': 'true',
            'gaming': 'true',
        }
        return await self.api_request(endpoint='/online', params=params)

    @lru_cache()
    async def get_channel_by_name(self, username: str):
        return await self.api_request(endpoint=f'/channel/name/{username}')

    async def api_request(self, *, endpoint, params=None):
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        async with self.bot.session.get('https://api.picarto.tv/v1' + endpoint, headers=headers, params=params) as r:
            if r.status != 200:
                return None
            return await r.json()

    async def validate_username(self, username: str) -> str:
        if not username:
            raise errors.InvalidUsernameError(username)
        if not re.fullmatch(r'^\w{3,24}$', username, re.IGNORECASE):
            raise errors.InvalidUsernameError(username)

        return username.lower()

    def stream_url(self, username: str) -> str:
        return f'https://picarto.tv/{username}'

    @property
    def streamer_class(self) -> Type[Streamer]:
        return PicartoStreamer
