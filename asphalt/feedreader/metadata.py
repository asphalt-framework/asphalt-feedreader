from datetime import datetime
from typing import Dict, Any, Tuple, Iterable  # noqa

from dateutil.parser import parse
from typeguard import check_argument_types


class FeedEntry:
    """
    Represents a news item in a syndication feed.

    The following parameters are also available as instance variables:

    :param id: globally unique identifier of the entry
    :param title: short title of the entry
    :param summary: a short description of the entry
    :param categories: a tuple of category names for the entry
    :param link: a URL that links to the relevant web page
    :param published: a timezone aware date/time when the entry was published
    :param enclosure_url: URL to a related media object
    :param enclosure_length: size (in bytes) of the related media object
    :param enclosure_type: MIME type of the related media object
    """

    __slots__ = ('id', 'title', 'summary', 'categories', 'link', 'published', 'enclosure_url',
                 'enclosure_length', 'enclosure_type')

    def __init__(self, id: str, *, title: str = None, summary: str = None,
                 categories: Iterable[str] = (), link: str = None, published: datetime = None,
                 enclosure_url: str = None, enclosure_length: int = None,
                 enclosure_type: str = None):
        assert check_argument_types()
        self.id = id
        self.title = title
        self.summary = summary
        self.categories = tuple(categories)
        self.link = link
        self.published = published
        self.enclosure_url = enclosure_url
        self.enclosure_length = enclosure_length
        self.enclosure_type = enclosure_type


class FeedMetadata:
    """
    Contains metadata for a syndication feed.

    :ivar icon: URL pointing to the image representing this feed
    :vartype icon: Optional[str]
    :ivar title: title of this feed
    :vartype title: Optional[str]
    :ivar link: link to the HTML website related to this feed
    :vartype link: Optional[str]
    :ivar generator: name of the software used to generate this feed
    :vartype generator: Optional[str]
    :ivar copyright: copyright statement
    :vartype copyright: Optional[str]
    :ivar updated: the last time this feed was updated
    :vartype updated: Optional[datetime]
    """

    categories = None  # type: Tuple[str, ...]
    icon = None  # type: str
    title = None  # type: str
    link = None  # type: str
    generator = None  # type: str
    copyright = None  # type: str
    updated = None  # type: datetime

    def __getstate__(self) -> Dict[str, Any]:
        state = {
            key: getattr(self, key) for key in
            ('categories', 'icon', 'title', 'link', 'generator', 'copyright')
            if getattr(self, key) is not None
        }
        state['version'] = 1
        if self.updated:
            state['updated'] = self.updated.isoformat()

        return state

    def __setstate__(self, state: Dict[str, Any]):
        assert check_argument_types()
        version = state.get('version')
        if version != 1:
            raise ValueError('cannot handle {} state version {}'.
                             format(self.__class__.__name__, version))

        for attr, value in state.items():
            if attr == 'updated':
                self.updated = parse(value)
            elif attr == 'categories':
                self.categories = tuple(value)
            elif attr in ('icon', 'title', 'link', 'generator', 'copyright'):
                setattr(self, attr, value)
