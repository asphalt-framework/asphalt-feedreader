Creating custom feed parsers
============================

If you have a website that does not provide an RSS or Atom feed natively, but nonetheless contain
news items structured in a manner that *could* be syndicated, it is possible to construct a
tailored feed reader class for that particular website. The parser would take the HTML content,
parse it into a structured form (using BeautifulSoup_ or a similar tool) and then extract the
necessary information. The process is of course vulnerable to any structural changes made in the
HTML, but it's still better than nothing.

To implement an HTML feed parser, you should inherit from the
:class:`~asphalt.feedreader.readers.base.BaseFeedReader` class and implement the
:meth:`~asphalt.feedreader.readers.base.BaseFeedReader.parse_document` method.
This method must return a two element tuple containing:

* a dictionary of metadata attributes and values (can be just an empty dict)
* a list of dictionaries, each dictionary representing the constructor keyword arguments for
  :class:`~asphalt.feedreader.events.EntryEvent`

How the method extracts this information is entirely up to the implementation, but using either
`lxml.html`_ or BeautifulSoup_ directly is usually the most robust method. The implementation
needs to return **all** the events found in the document. The matter of filtering already seen
events is taken care of in the :meth:`~asphalt.feedreader.readers.base.BaseFeedReader.update`
method.

The **only** required piece of information for each event is the ``id`` of the event. This is the
unique identifier of the event which will be used for preventing already seen events from being
dispatched from the ``event_discovered`` signal of the feed. Other than that, you can fill in as
many of the fields of :class:`~asphalt.feedreader.events.EntryEvent` as you like, or subclass the
class to contain extra attributes.

An example of a custom feed reader has been provided in
`examples/custom_html.py <https://github.com/asphalt-framework/asphalt-feedreader/blob/master/examples/custom_html.py>`_.

.. _lxml.html: http://lxml.de/lxmlhtml.html
.. _BeautifulSoup: https://www.crummy.com/software/BeautifulSoup/
