import logging
from string import whitespace
from typing import List, Dict, Any, Tuple, Optional

from dateutil.parser import parse
from defusedxml import ElementTree

from asphalt.feedreader.readers.base import BaseFeedReader, FeedEntry

logger = logging.getLogger(__name__)


class Person:
    """
    Represents an author or contributor in an Atom feed entry.

    The following parameters are also available as instance attributes:

    :param name: the full name of the person
    :param email: the person's email address
    :param uri: URI of the person's home page (or similar web page)
    """

    __slots__ = ('name', 'email', 'uri')

    def __init__(self, name: str, email: str = None, uri: str = None):
        self.name = name
        self.email = email
        self.uri = uri

    def __eq__(self, other):
        if isinstance(other, Person):
            return self.name == other.name and self.email == other.email and self.uri == other.uri

        return NotImplemented

    def __ne__(self, other):
        return not self == other


class AtomEntry(FeedEntry):
    """
    Represents an entry from an Atom feed.

    :ivar updated: time when this entry was updated
    :vartype updated: Optional[datetime]
    :ivar authors: authors of this entry
    :vartype authors: Tuple[Person, ...]
    :ivar contributors: contributors for this entry
    :vartype contributors: Tuple[Person, ...]
    """

    __slots__ = ('content', 'content_type', 'authors', 'contributors', 'updated')

    def __init__(self, *, content: str = None, content_type: str = None, updated: str = None,
                 authors: List[Person] = (), contributors: List[Person] = (), **kwargs):
        super().__init__(**kwargs)
        self.content = content
        self.content_type = content_type
        self.authors = tuple(authors)
        self.contributors = tuple(contributors)
        self.updated = updated


class AtomFeedReader(BaseFeedReader):
    """Represents an Atom (:rfc:`4287`) feed."""

    NAMESPACE = '{http://www.w3.org/2005/Atom}'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.http_headers.setdefault('accept', 'application/rss+atom; text/xml')

    @classmethod
    def can_parse(cls, document: str, content_type: str) -> Optional[str]:
        if content_type not in ('application/atom+xml', 'text/xml'):
            return ("Incompatible content type (got %r, needs to be either 'application/atom+xml' "
                    "or 'text/xml')" % content_type)

        try:
            root = ElementTree.fromstring(document)
        except ElementTree.ParseError as e:
            return 'Error parsing the document as XML: %s' % e

        if root.tag != cls.NAMESPACE + 'feed':
            return ('Incompatible root tag (got <%s>, needs to be <feed> in the %s namespace)' %
                    (root.tag, cls.NAMESPACE[1:-1]))

        return None

    @classmethod
    def parse_document(cls, document: str) -> Tuple[Dict[str, Any], List[FeedEntry]]:
        root = ElementTree.fromstring(document)
        metadata_changes = {}
        for tag in root:
            tag_name = tag.tag.replace(cls.NAMESPACE, '')
            tag_text = tag.text.strip(whitespace) if tag.text else None
            if tag_name in ('id', 'title', 'icon', 'generator'):
                metadata_changes[tag_name] = tag_text
            elif tag_name == 'updated':
                metadata_changes[tag_name] = parse(tag_text)
            elif tag_name == 'subtitle':
                metadata_changes['description'] = tag_text
            elif tag_name == 'rights':
                metadata_changes['copyright'] = tag_text
            elif tag_name == 'link':
                if tag.attrib.get('rel') == 'alternate':
                    metadata_changes['link'] = tag.attrib['href']

        events = []  # type: List[AtomEntry]
        for entry in root.iter(cls.NAMESPACE + 'entry'):
            kwargs = {}
            for tag in entry:
                tag_name = tag.tag.replace(cls.NAMESPACE, '')
                tag_text = tag.text.strip(whitespace) if tag.text else None
                if tag_name in ('title', 'id', 'summary'):
                    kwargs[tag_name] = tag_text
                elif tag_name in ('published', 'updated'):
                    kwargs[tag_name] = parse(tag_text)
                elif tag_name == 'content':
                    kwargs[tag_name] = tag_text
                    kwargs['content_type'] = tag.attrib.get('type', 'text')
                elif tag_name == 'category':
                    kwargs.setdefault('categories', []).append(tag_text)
                elif tag_name == 'link':
                    if tag.attrib.get('rel') == 'alternate':
                        kwargs['link'] = tag.attrib['href']
                    elif tag.attrib.get('rel') == 'enclosure':
                        kwargs['enclosure_url'] = tag.attrib['href']
                        if 'length' in tag.attrib:
                            kwargs['enclosure_length'] = int(tag.attrib['length'])
                        if 'type' in tag.attrib:
                            kwargs['enclosure_type'] = tag.attrib['type']
                elif tag_name == 'author':
                    attrs = {subtag.tag.replace(cls.NAMESPACE, ''): subtag.text.strip(whitespace)
                             for subtag in tag if subtag.text}
                    kwargs.setdefault('authors', []).append(Person(**attrs))
                elif tag_name == 'contributor':
                    attrs = {subtag.tag.replace(cls.NAMESPACE, ''): subtag.text.strip(whitespace)
                             for subtag in tag if subtag.text}
                    kwargs.setdefault('contributors', []).append(Person(**attrs))

            if 'id' in kwargs:
                events.insert(0, AtomEntry(**kwargs))
            else:
                logger.warning('Encountered entry without an "id" element')

        return metadata_changes, events
