from typing import Union

from asphalt.core import Context, executor
from asphalt.serialization.api import Serializer
from asphalt.serialization.serializers.json import JSONSerializer
from sqlalchemy import Table, MetaData, Column, LargeBinary, select, Unicode
from sqlalchemy.engine import Engine
from typeguard import check_argument_types

from asphalt.feedreader.api import FeedStateStore


class SQLAlchemyStore(FeedStateStore):
    """
    Stores feed states in a relational database using SQLAlchemy.

    This store imposes a maximum limit of 191 characters to length of the state id due to that
    being the maximum size of mysql index entries for columns with the utf8mb4 encoding.

    :param engine: an SQLAlchemy engine or the resource name of one
    :param serializer: a serializer or the resource name of one (creates a new JSONSerializer if
        none is specified)
    :param table_name: name of the table in which to store the feed states
    """

    def __init__(self, engine: Union[str, Engine] = 'default',
                 serializer: Union[str, Serializer] = None, table_name: str = 'feed_states'):
        assert check_argument_types()
        self.engine = engine
        self.serializer = serializer or JSONSerializer()
        self.table_name = table_name

        # 191 = max key length in MySQL for InnoDB/utf8mb4 tables
        self.feeds_table = Table(table_name, MetaData(),
                                 Column('id', Unicode(191), primary_key=True),
                                 Column('state', LargeBinary, nullable=False),
                                 mysql_charset='utf8mb4')

    async def start(self, ctx: Context):
        if isinstance(self.serializer, str):
            self.serializer = await ctx.request_resource(Serializer, self.serializer)
        if isinstance(self.engine, str):
            self.engine = await ctx.request_resource(Engine, self.engine)

        await ctx.call_in_executor(self.feeds_table.create, self.engine, checkfirst=True)

    @executor
    def store_state(self, feed_id: str, state) -> None:
        query = self.feeds_table.update().where(id=feed_id).values(state=state)
        if self.engine.execute(query).rowcount == 0:
            query = self.feeds_table.insert().values(id=feed_id, state=state)
            self.engine.execute(query)

    @executor
    def load_state(self, feed_id: str):
        query = select(self.feeds_table.c.state).where(self.feeds_table.c.id == feed_id)
        serialized = self.engine.scalar(query)
        return self.serializer.deserialize(serialized)
