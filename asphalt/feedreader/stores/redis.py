from typing import Union

from aioredis import Redis
from asphalt.core import Context
from asphalt.serialization.api import Serializer
from asphalt.serialization.serializers.json import JSONSerializer
from typeguard import check_argument_types

from asphalt.feedreader.api import FeedStateStore


class RedisStore(FeedStateStore):
    """
    Stores feed states in a Redis database.

    :param client: a Redis client
    :param serializer: a serializer or the resource name of one (creates a new JSONSerializer if
        none is specified)
    :param db: number of the database to use
    :param feeds_key: key in the database to store the states in
    """

    def __init__(self, client: Union[str, Redis] = 'default',
                 serializer: Union[str, Serializer] = None, db: int = 0,
                 feeds_key: str = 'feed_states'):
        assert check_argument_types()
        self.client = client
        self.serializer = serializer or JSONSerializer()
        self.db = db
        self.feeds_key = feeds_key

    async def start(self, ctx: Context):
        if isinstance(self.serializer, str):
            self.serializer = await ctx.request_resource(Serializer, self.serializer)
        if isinstance(self.client, str):
            self.client = await ctx.request_resource(Redis, self.client)

    async def store_state(self, feed_id: str, state) -> None:
        serialized = self.serializer.serialize(state)
        await self.client.hset(self.feeds_key, feed_id, serialized)

    async def load_state(self, feed_id: str):
        serialized = await self.client.hget(self.feeds_key, feed_id)
        return self.serializer.deserialize(serialized) if serialized is not None else None
