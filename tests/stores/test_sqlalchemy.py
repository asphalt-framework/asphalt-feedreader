import pytest
from sqlalchemy.pool import StaticPool

from asphalt.core import Context
from asphalt.serialization.api import Serializer
from asphalt.serialization.serializers.json import JSONSerializer
from sqlalchemy import create_engine

from asphalt.feedreader.stores.sqlalchemy import SQLAlchemyStore


@pytest.fixture
def context(event_loop):
    with Context() as ctx:
        yield ctx


@pytest.fixture(params=[True, False])
def store(request, event_loop, context):
    direct_resources = request.param

    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False},
                           poolclass=StaticPool)
    context.add_teardown_callback(engine.dispose)
    if not direct_resources:
        context.add_resource(engine)
        engine = 'default'

    serializer = JSONSerializer()
    if not direct_resources:
        context.add_resource(serializer, types=[Serializer])
        serializer = 'default'

    store_ = SQLAlchemyStore(engine=engine, serializer=serializer)
    event_loop.run_until_complete(store_.start(context))
    return store_


@pytest.mark.asyncio
async def test_store_load_state(store):
    await store.store_state('feed', {'a': 5, 'b': 8})
    await store.store_state('feed', {'a': 5, 'b': [4, 5]})
    state = await store.load_state('feed')
    assert state == {'a': 5, 'b': [4, 5]}
