Configuration
-------------

.. highlight:: yaml

The component configuration of asphalt-feedreader lets you configure a number of syndication feeds
and a number of *state stores* for them.

State stores are repositories where a feed can save its persistent state, including its current
metadata and the entry IDs it has already seen. Using a state store is completely optional.

A basic configuration that creates a single feed pointing to CNN's top stories might look like
this::

    components:
      feedreader:
        url: http://rss.cnn.com/rss/edition.rss

Once the component has started, the feed will be available as a resource of type
:class:`~asphalt.feedreader.api.FeedReader` named default and accessible as ``ctx.feed``.

Notice that the above configuration automatically detects the feed reader class. To avoid the
overhead of the initial autodetection, we can tell the component directly what feed reader class to
use. Since we know this particular feed is an RSS feed, we can specify the ``reader`` option
accordingly::

    components:
      feedreader:
        url: http://rss.cnn.com/rss/edition.rss
        reader: rss

For reference on what kinds of values are acceptable for the ``reader`` option, see the
documentation of :func:`~asphalt.feedreader.create_feed`.
