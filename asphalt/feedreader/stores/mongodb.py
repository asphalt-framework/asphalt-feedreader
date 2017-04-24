from typing import Union

from asphalt.core import Context
from asphalt.serialization.api import Serializer
from asphalt.serialization.serializers.json import JSONSerializer
from motor.motor_asyncio import AsyncIOMotorClient
from typeguard import check_argument_types

from asphalt.feedreader.api import FeedStateStore


class MongoDBStore(FeedStateStore):
    """
    Stores feed states in a MongoDB database.

    :param client: a Redis client
    :param serializer: a serializer or the resource name of one (creates a new JSONSerializer if
        none is specified)
    :param db: database to store the states in
    :param collection: name of the collection in the database
    """

    def __init__(self, client: Union[str, AsyncIOMotorClient] = 'default',
                 serializer: Union[str, Serializer] = None, db: str = 'asphalt',
                 collection: str = 'feed_states'):
        assert check_argument_types()
        self.client = client
        self.serializer = serializer or JSONSerializer()
        self.db = db
        self.collection_name = collection
        self.collection = None

    async def start(self, ctx: Context):
        if isinstance(self.serializer, str):
            self.serializer = await ctx.request_resource(Serializer, self.serializer)
        if isinstance(self.client, str):
            self.client = await ctx.request_resource(AsyncIOMotorClient, self.client)

        self.collection = self.client[self.db][self.collection_name]
        await self.collection.create_index('feed_id')

    async def store_state(self, feed_id: str, state) -> None:
        serialized = self.serializer.serialize(state)
        document = dict(feed_id=feed_id, state=serialized)
        await self.collection.find_one_and_replace({'feed_id': feed_id}, document, upsert=True)

    async def load_state(self, feed_id: str):
        document = await self.collection.find_one({'feed_id': feed_id}, {'state': True})
        return self.serializer.deserialize(document['state']) if document else None
