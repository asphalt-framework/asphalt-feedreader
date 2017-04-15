import logging
from typing import Dict, Type, Union, Any

import aiohttp
from asphalt.core import Component, Context, PluginContainer, merge_config, qualified_name
from typeguard import check_argument_types

from asphalt.feedreader.api import FeedReader

feed_readers = PluginContainer('asphalt.feedreader.readers')
feed_stores = PluginContainer('asphalt.feedreader.stores')
logger = logging.getLogger(__name__)


async def create_feed(ctx: Context, reader: Union[str, Type[FeedReader]] = None,
                      **reader_args) -> FeedReader:
    """
    Create and start a syndication feed.

    .. note:: This function does **NOT** add the feed to the context as a resource.

    :param ctx: a context object (passed to the :meth:`~asphalt.feedreader.api.FeedReader.start`
        method)
    :param reader: specifies the feed reader class by one of the following means:

       * a subclass of :class:`~asphalt.feedreader.api.FeedReader`
       * the entry point name of one
       * a ``module:varname`` reference to one
       * ``None`` to attempt automatic detection of the feed type
    :param reader_args: keyword arguments passed to the feed reader class
    :return: a feed reader

    """
    assert check_argument_types()
    if isinstance(reader, type):
        feed_class = reader
    elif reader:
        feed_class = feed_readers.resolve(reader)
    else:
        try:
            url = reader_args['url']
        except KeyError:
            raise LookupError('no "url" option was specified – it is required for feed reader '
                              'autodetection') from None

        feed_class = None
        async with aiohttp.request('GET', url) as response:
            response.raise_for_status()
            text = await response.text()
            for cls in feed_readers.all():
                logger.info('Attempting autodetection of feed reader class for %s', url)
                reason = cls.can_parse(text, response.content_type)
                if reason:
                    logger.info('%s: %s', qualified_name(cls), reason)
                else:
                    logger.info('Selected reader class %s for %s', qualified_name(cls), url)
                    feed_class = cls
                    break
            else:
                raise RuntimeError('unable to detect the feed type for url: ' + url)

    feed = feed_class(**reader_args)
    await feed.start(ctx)
    return feed


class FeedReaderComponent(Component):
    """
    Creates :class:`~asphalt.feedreader.api.FeedReader` resources.

    :param feeds: a dictionary of resource name ⭢ keyword arguments to :func:`~.create_feed`
    :param stores: a dictionary of resource name ⭢ feed state store configuration
    :param feed_defaults: defaults for keyword arguments passed to the  :func:`~.create_feed`
    """

    def __init__(self, feeds: Dict[str, Dict[str, Any]] = None,
                 stores: Dict[str, Dict[str, Any]] = None, **feed_defaults):
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
            feed = await create_feed(ctx, **config)
            ctx.add_resource(feed, resource_name, context_attr, types=[type(feed), FeedReader])
            logger.info('Configured feed (%s / ctx.%s; url=%s)', resource_name, context_attr,
                        feed.url)
