import logging
import pathlib

import asyncpg

from .errors import StreamerAlreadyExists
from ..utils import strings

log = logging.getLogger(__name__)


class Database:
    def __init__(self, pool):
        self.pool = pool
        self.sql = strings.database_queries

    @staticmethod
    async def create_database(*, loop, username, password, database, hostname='localhost', port=5432):
        dsn = "postgres://{}:{}@{}:{}/{}".format(username, password, hostname, port, database)
        pool = await asyncpg.create_pool(dsn, loop=loop)
        sql = pathlib.Path('tables.sql').read_text()
        await pool.execute(sql)

        return Database(pool)

    async def close(self):
        await self.pool.close()

    async def add_subscription(self, *, subscriber_id: int, service: str, username: str, service_id: str):
        """Adds a new subscription

        :param service_id: the internal ID of the streamer in whichever service they're in
        :param subscriber_id: Subscriber id
        :param service: Streaming service of the user
        :param username: Username of the user
        """

        async with self.pool.acquire() as con:
            async with con.transaction():
                record = await con.fetchrow(self.sql['insert_streamers'], username, service, service_id)
                streamer_id = record['streamer_id']
            async with con.transaction():
                try:
                    await con.execute(self.sql['insert_subscriptions'], subscriber_id, streamer_id)
                except asyncpg.UniqueViolationError as e:
                    raise StreamerAlreadyExists from e

    async def del_subscription(self, *, subscriber_id: int, service: str, username: str):
        """Deletes a subscription

        If the subscription doesn't exist, it just fails silently.

        :param subscriber_id: Subscriber id
        :param service: Streaming service of the user
        :param username: Username of the user
        """
        async with self.pool.acquire() as con:
            async with con.transaction():
                await con.execute(self.sql['del_subscription'], service, username, subscriber_id)

    async def delete_subscriber(self, *, subscriber_id: int):
        """Deletes all subscriptions from a subscriber

        :param subscriber_id: Subscriber id
        """
        async with self.pool.acquire() as con:
            await con.execute(self.sql['delete_subscriber'], subscriber_id)

    async def get_all_streamers_from_service(self, *, service: str):
        """Returns all streamers related to a service

        :param service: The service to get the streamers from
        :return: The streamers related to the service
        """
        async with self.pool.acquire() as con:
            return await con.fetch(self.sql['get_all_streamers_from_service'], service)

    async def get_subscribers_from_streamer(self, streamer_id: str):
        """Returns all the subscribers that are subscribed to a streamer

        :param streamer_id: ID of the streamer
        :return: Iterable of channel IDs of the streamer's subscribers
        """
        async with self.pool.acquire() as con:
            return await con.fetch(self.sql['get_subscribers_from_streamer'], streamer_id)

    async def get_subscriptions_from_subscriber(self, subscriber_id: int, service: str):
        """Returns all the streamers that the subscriber is subscribed to

        :param subscriber_id: ID of the subscriber
        :param service: The service that the subscriber is referring to
        :return: Iterable of (username, service) of all the streamers that the subscriber is currently subscribed to
        """
        async with self.pool.acquire() as con:
            return await con.fetch(self.sql['get_subscriptions_from_subscriber'], subscriber_id, service)
