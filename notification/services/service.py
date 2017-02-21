from typing import Iterable

import discord
from discord import Color


class StreamerNotFoundError(Exception):
    pass


class Notification:
    def __init__(self, *, channel_id: str, stream_url: str, icon_url: str, username: str, service: str):
        self.channel_id = channel_id
        self.stream_url = stream_url
        self.icon_url = icon_url
        self.username = username
        self.service = service

    def get_embed(self):
        emb = discord.Embed(color=Color.orange(), description=self.stream_url)
        emb.set_author(name=f'{self.username} is online on {self.service.capitalize()}!',
                       url=self.stream_url,
                       icon_url=self.icon_url)
        return emb

    @property
    def channel_id(self):
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value):
        self._channel_id = value

    @property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        self._username = value


class Service:
    def __init__(self, api_key):
        self.api_key = api_key

    async def check_and_notify(self) -> Iterable[Notification]:
        raise NotImplementedError

    async def add_subscription(self, *, subscriber_id: str, channel_id: str, username: str):
        raise NotImplementedError

    @property
    def icon_url(self) -> str:
        raise NotImplementedError

    @property
    def stream_url(self) -> str:
        raise NotImplementedError

    @property
    def service(self) -> str:
        raise NotImplementedError
