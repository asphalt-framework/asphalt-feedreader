Configuration
=============

.. highlight:: yaml

The component configuration of asphalt-feedreader lets you configure a number of syndication feeds
and a number of *state stores* for them (see below).

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

Setting up state stores
-----------------------

State stores are repositories where a feed can save its persistent state, including its current
metadata and the entry IDs it has already seen. You can use feeds without state stores but if you
restart the application, they may then report previously seen entries again.

The following state stores are provided out of the box:

* :mod:`asphalt.feedreader.stores.sqlalchemy <sqlalchemy>`
* :mod:`asphalt.feedreader.stores.redis <redis>`
* :mod:`asphalt.feedreader.stores.mongodb <mongodb>`

Each of these stores requires some database client resource, and the easiest way to get it is to
use the corresponding Asphalt component. For example, to configure a simple sqlite based SQLAlchemy
store, you'd first install asphalt-sqlalchemy and write the following configuration (following up
from the previous examples)::

    components:
      sqlalchemy:
        url: sqlite:///feeds.sqlite
      feedreader:
        feeds:
          cnn:
            url: http://rss.cnn.com/rss/edition.rss
            reader: rss
            store: default
        stores:
          default:
            type: sqlalchemy

Any options under each state store configuration besides ``type`` will be directly passed to the
constructor of the store class.

It is also possible to use a custom serializer with the built-in state stores, but that is usually
unnecessary.
