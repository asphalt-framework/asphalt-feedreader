import logging
from string import whitespace
from typing import List, Dict, Any, Tuple, Optional

from dateutil.parser import parse
from defusedxml import ElementTree

from asphalt.feedreader.readers.base import BaseFeedReader, FeedEntry

logger = logging.getLogger(__name__)


class RSSEntry(FeedEntry):
    """
    Represents an entry from an RSS feed.

    :ivar author: email address of author
    :vartype author: Optional[str]
    :ivar comments: URL that links to a web page with comments related to the entry
    :vartype comments: Optional[str]
    """

    __slots__ = ('author', 'comments')

    def __init__(self, *, author: str = None, comments: str = None, **kwargs):
        super().__init__(**kwargs)
        self.author = author
        self.comments = comments


class RSSFeedReader(BaseFeedReader):
    """
    Represents an RSS 2.0 (Really Simple Syndication) feed.

    :param respect_rate_limits: respect the rate limits (if any) set by the publisher
    """

    def __init__(self, respect_rate_limits: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.http_headers.setdefault('accept', 'application/rss+xml; text/xml')
        self.respect_rate_limits = respect_rate_limits

    @classmethod
    def can_parse(cls, document: str, content_type: str) -> Optional[str]:
        if content_type not in ('application/rss+xml', 'text/xml'):
            return ("Incompatible content type (got %r, needs to be either 'application/rss+xml' "
                    "or 'text/xml')" % content_type)

        try:
            root = ElementTree.fromstring(document)
        except ElementTree.ParseError as e:
            return 'Error parsing the document as XML: %s' % e

        if root.tag != 'rss':
            return 'Incompatible root tag (got <%s>, needs to be <rss>)' % root.tag
        if 'version' not in root.attrib:
            return 'No "version" tag present in the <rss> element'
        if root.attrib.get('version') != '2.0':
            return "Incompatible RSS version (got %r, needs to be '2.0')" % root.attrib['version']

        return None

    @classmethod
    def parse_document(cls, document: str) -> Tuple[Dict[str, Any], List[FeedEntry]]:
        root = ElementTree.fromstring(document)
        if root.tag != 'rss':
            raise ValueError('XML root tag was "%s"; expected "rss"' % root.tag)
        elif 'version' not in root.attrib:
            raise ValueError('no "version" attribute was found in the "rss" tag')
        elif root.attrib['version'] != '2.0':
            raise ValueError('unsupported RSS version: %s' % root.attrib['version'])

        channel = root.find('channel')
        if channel is None:
            raise ValueError('missing "channel" element in RSS feed')

        metadata = {}
        for tag in channel:
            tag_text = tag.text.strip(whitespace) if tag.text else None
            if tag.tag in ('title', 'link', 'description'):
                metadata[tag.tag] = tag_text
            elif tag.tag == 'lastBuildDate':
                metadata['updated'] = parse(tag_text)

        events = []  # type: List[RSSEntry]
        for item in channel.iter('item'):
            kwargs = {}
            for tag in item:
                if tag.tag in ('title', 'link', 'author', 'comments'):
                    kwargs[tag.tag] = tag.text
                elif tag.tag == 'guid':
                    kwargs['id'] = tag.text
                elif tag.tag == 'description':
                    kwargs['summary'] = tag.text
                elif tag.tag == 'pubDate':
                    kwargs['published'] = parse(tag.text)
                elif tag.tag == 'enclosure':
                    kwargs['enclosure_url'] = tag.attrib['url']
                    if 'length' in tag.attrib:
                        kwargs['enclosure_length'] = int(tag.attrib['length'])
                    if 'type' in tag.attrib:
                        kwargs['enclosure_type'] = tag.attrib['type']
                elif tag.tag == 'category':
                    kwargs.setdefault('categories', []).append(tag.text)

            if 'id' in kwargs:
                events.insert(0, RSSEntry(**kwargs))
            else:
                logger.warning('Encountered item without a "guid" element')

        return metadata, events
