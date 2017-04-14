from datetime import datetime  # noqa
from typing import Dict, Any, Tuple  # noqa

from dateutil.parser import parse


class FeedMetadata:
    """
    Contains feed metadata.

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
            key: getattr(self, value) for key, value in
            ('categories', 'icon', 'title', 'link', 'generator', 'copyright')
            if getattr(self, value) is not None
        }
        state['version'] = 1
        if self.updated:
            state['updated'] = self.updated.isoformat()

        return state

    def __setstate__(self, state: Dict[str, Any]):
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
