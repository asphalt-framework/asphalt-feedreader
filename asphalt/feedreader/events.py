from datetime import datetime
from typing import Iterable, Dict, Any

from asphalt.core import Event
from typeguard import check_argument_types


class EntryEvent(Event):
    """
    Base class for feed entry events.

    :ivar str id: globally unique identifier of the entry
    :ivar title: short title of the entry
    :vartype title: Optional[str]
    :ivar summary: a short description of the entry
    :vartype summary: Optional[str]
    :ivar categories: a tuple of category names for the entry
    :vartype categories: Tuple[str, ...]
    :ivar link: a URL that links to the relevant web page
    :vartype link: Optional[str]
    :ivar published: a timezone aware date/time when the entry was published
    :vartype published: Optional[datetime]
    :ivar enclosure_url: URL to a related media object
    :vartype enclosure_url: Optional[str]
    :ivar enclosure_length: size (in bytes) of the related media object
    :vartype enclosure_length: Optional[int]
    :ivar enclosure_type: MIME type of the related media object
    :vartype enclosure_type: Optional[str]
    """

    __slots__ = ('id', 'title', 'summary', 'categories', 'link', 'published', 'enclosure_url',
                 'enclosure_length', 'enclosure_type')

    def __init__(self, source, topic: str, id: str, *, title: str = None,
                 summary: str = None, categories: Iterable[str] = (), link: str = None,
                 published: datetime = None, enclosure_url: str = None,
                 enclosure_length: int = None, enclosure_type: str = None):
        assert check_argument_types()
        super().__init__(source, topic)
        self.id = id
        self.title = title
        self.summary = summary
        self.categories = tuple(categories)
        self.link = link
        self.published = published
        self.enclosure_url = enclosure_url
        self.enclosure_length = enclosure_length
        self.enclosure_type = enclosure_type


class MetadataEvent(Event):
    """
    Signals that one or more metadata attributes on a feed have changed

    :ivar changes: a dictionary of attribute name ⭢ new value
    :vartype changes: Dict[str, Any]
    """

    __slots__ = ('changes',)

    def __init__(self, source, topic: str, changes: Dict[str, Any]):
        super().__init__(source, topic)
        self.changes = changes
