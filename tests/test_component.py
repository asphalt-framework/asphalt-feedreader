from aiohttp import web

from asphalt.core.context import Context
import pytest

from asphalt.feedreader import FeedReader, FeedReaderComponent, create_feed
from asphalt.feedreader.readers.atom import AtomFeedReader
from asphalt.feedreader.readers.rss import RSSFeedReader


def rss_handler(request):
    return web.Response(body='<rss version="2.0"><channel></channel></rss>',
                        content_type='application/rss+xml')


def atom_handler(request):
    return web.Response(body='<feed xmlns="http://www.w3.org/2005/Atom"></feed>',
                        content_type='application/atom+xml')


@pytest.fixture
def context(event_loop):
    ctx = Context()
    yield ctx
    event_loop.run_until_complete(ctx.close())


@pytest.fixture
def webapp(event_loop, unused_tcp_port):
    app = web.Application(loop=event_loop)
    app.router.add_get('/rss', rss_handler)
    app.router.add_get('/atom', atom_handler)
    handler = app.make_handler(loop=event_loop)
    server = event_loop.run_until_complete(
        event_loop.create_server(handler, host='localhost', port=unused_tcp_port))
    yield
    server.close()
    event_loop.run_until_complete(server.wait_closed())


@pytest.mark.parametrize('reader', ['rss', RSSFeedReader], ids=['entrypoint', 'class'])
async def test_create_feed(reader):
    feed = await create_feed(context, url='http://example.org/feed', reader=reader, interval=None)
    assert isinstance(feed, RSSFeedReader)


@pytest.mark.parametrize('reader, reader_class', [
    ('rss', RSSFeedReader),
    ('atom', AtomFeedReader)
], ids=['rss', 'atom'])
@pytest.mark.asyncio
async def test_create_feed_autodetect(webapp, context, unused_tcp_port, reader, reader_class):
    feed = await create_feed(context, url='http://localhost:%d/%s' % (unused_tcp_port, reader),
                             interval=None)
    assert isinstance(feed, reader_class)


@pytest.mark.asyncio
async def test_component_start(context):
    component = FeedReaderComponent(feeds={
        'foo': dict(url='http://example.org/rss', reader='rss', interval=None),
        'bar': dict(url='http://example.org/atom', reader='atom', interval=None)
    })
    await component.start(context)

    context.require_resource(RSSFeedReader, 'foo')
    context.require_resource(AtomFeedReader, 'bar')
    foo = context.require_resource(FeedReader, 'foo')
    bar = context.require_resource(FeedReader, 'bar')
    assert context.foo is foo
    assert context.bar is bar


@pytest.mark.asyncio
async def test_default_config(context):
    component = FeedReaderComponent(url='http://example.org/rss', reader='rss', interval=None)
    await component.start(context)

    resource = await context.request_resource(FeedReader)
    assert isinstance(resource, RSSFeedReader)
    assert context.feed is resource
