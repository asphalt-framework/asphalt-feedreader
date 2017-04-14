from typing import Union

from asphalt.core import Context, executor
from asphalt.serialization.api import Serializer
from asphalt.serialization.serializers.json import JSONSerializer
from sqlalchemy import Table, MetaData, Column, LargeBinary, select, Unicode
from sqlalchemy.engine import Connectable
from typeguard import check_argument_types

from asphalt.feedreader.api import FeedStateStore


class SQLAlchemyStore(FeedStateStore):
    """
    Stores feed states in a relational database using SQLAlchemy.
    """

    def __init__(self, engine: Union[str, Connectable] = 'default',
                 serializer: Union[str, Serializer] = None,
                 table_name: str = 'feed_states'):
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
            self.engine = await ctx.request_resource(Connectable, self.engine)

        await ctx.call_in_executor(self.feeds_table.create, self.engine, checkfirst=True)

    @executor
    def store_state(self, feed_id: str, state) -> None:
        query = self.feeds_table.update().where(name=feed_id).values(state=state)
        if self.engine.execute(query).rowcount == 0:
            query = self.feeds_table.insert().values(name=feed_id, state=state)
            self.engine.execute(query)

    @executor
    def load_state(self, feed_id: str):
        query = select(self.feeds_table.c.state).where(self.feeds_table.c.name == feed_id)
        serialized = self.engine.scalar(query)
        return self.serializer.deserialize(serialized)
