from typing import Dict, Type, Union

import aiohttp
import logging

from asphalt.core import Component, Context, PluginContainer, merge_config
from typeguard import check_argument_types

from asphalt.core.utils import qualified_name
from asphalt.feedreader.api import FeedReader

feed_readers = PluginContainer('asphalt.feedreader.readers')
feed_stores = PluginContainer('asphalt.feedreader.stores')
logger = logging.getLogger(__name__)


async def create_feed(url: str, kind: Union[str, Type[FeedReader]] = None,
                      **config) -> FeedReader:
    """
    Create a syndication feed.

    The returned feed needs to be started (using :meth:`~asphalt.feedreader.api.FeedReader.start`).

    :param url: the address of the feed
    :param kind: either a feed reader class or the entry point name of one, or ``None`` to
        attempt automatic detection of the feed type
    :param config: keyword arguments passed to the feed reader class
    :return: a feed reader

    """
    assert check_argument_types()
    if isinstance(kind, type):
        feed_class = kind
    elif kind:
        feed_class = feed_readers.resolve(kind)
    else:
        feed_class = None
        async with aiohttp.request('GET', url) as response:
            response.raise_for_status()
            text = await response.text()
            for cls in feed_readers.all():
                if cls.can_parse(text, response.content_type):
                    feed_class = cls

    if feed_class:
        return feed_class(url=url, **config)
    else:
        raise RuntimeError('unable to detect the feed type for url: ' + url)


class FeedReaderComponent(Component):
    """
    Creates :class:`~asphalt.feedreader.api.FeedReader` resources.

    :param feeds: a dictionary of resource name ⭢ feed configuration
    :param stores: a dictionary of resource name ⭢ feed state store configuration
    :param feed_defaults: defaults for keyword arguments passed to the constructors of the chosen
        feed class(es)
    """

    def __init__(self, feeds: Dict[str, dict] = None, stores: Dict[str, dict] = None,
                 **feed_defaults):
        assert check_argument_types()
        if not feeds:
            feed_defaults.setdefault('context_attr', 'feed')
            feeds = {'default': feed_defaults}

        self.feeds = []
        for resource_name, config in feeds.items():
            config = merge_config(feed_defaults, config)
            context_attr = config.pop('context_attr', resource_name)
            self.feeds.append((resource_name, context_attr, config))

        self.stores = []
        if stores:
            for resource_name, config in stores.items():
                store = feed_stores.create_object(**config)
                self.stores.append((resource_name, store))

    async def start(self, ctx: Context):
        for resource_name, store in self.stores:
            await store.start(ctx)
            ctx.add_resource(store, resource_name)
            logger.info('Configured feed state store (%s; class=%s)', resource_name,
                        qualified_name(store))

        for resource_name, context_attr, config in self.feeds:
            feed = await create_feed(**config)
            await feed.start(ctx)
            ctx.add_resource(feed, resource_name, context_attr)
            logger.info('Configured feed (%s / ctx.%s; url=%s)', resource_name, context_attr,
                        feed.url)
