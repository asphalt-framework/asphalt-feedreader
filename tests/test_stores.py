import os

import pytest
from aioredis import create_reconnecting_redis
from asphalt.core import Context
from asphalt.feedreader.stores.redis import RedisStore
from asphalt.serialization.api import Serializer
from asphalt.serialization.serializers.json import JSONSerializer
from sqlalchemy.pool import StaticPool
from sqlalchemy import create_engine

from asphalt.feedreader.stores.sqlalchemy import SQLAlchemyStore


@pytest.fixture
def context(event_loop):
    with Context() as ctx:
        yield ctx


@pytest.fixture(params=[True, False])
def direct_resources(request):
    return request.param


@pytest.fixture
def serializer(context, direct_resources):
    serializer = JSONSerializer()
    if not direct_resources:
        context.add_resource(serializer, types=[Serializer])
        return 'default'
    else:
        return serializer


@pytest.fixture(params=['sqlalchemy', 'redis'])
def store(request, event_loop, context, direct_resources, serializer):
    if request.param == 'sqlalchemy':
        engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False},
                               poolclass=StaticPool)
        context.add_teardown_callback(engine.dispose)
        if not direct_resources:
            context.add_resource(engine)
            engine = 'default'

        store_ = SQLAlchemyStore(engine=engine, serializer=serializer)
    elif request.param == 'redis':
        address = (os.getenv('REDIS_HOST', 'localhost'), 6379)
        redis = event_loop.run_until_complete(create_reconnecting_redis(address))
        context.add_teardown_callback(redis.close)
        if not direct_resources:
            context.add_resource(redis)
            redis = 'default'

        store_ = RedisStore(client=redis, serializer=serializer)

    event_loop.run_until_complete(store_.start(context))
    return store_


@pytest.mark.asyncio
async def test_store_load_state(store):
    await store.store_state('feed', {'a': 5, 'b': 8})
    await store.store_state('feed', {'a': 5, 'b': [4, 5]})
    state = await store.load_state('feed')
    assert state == {'a': 5, 'b': [4, 5]}


@pytest.mark.asyncio
async def test_store_load_nonexistent_state(store):
    state = await store.load_state('blah')
    assert state is None
