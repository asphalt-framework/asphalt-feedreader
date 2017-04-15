from typing import Dict, Any

from asphalt.core import Event
from typeguard import check_argument_types

from asphalt.feedreader.metadata import FeedEntry


class EntryEvent(Event):
    """
    Signals that a new news entry has been discovered in a syndication feed.

    :ivar FeedEntry entry: the entry that was discovered
    """

    __slots__ = 'entry'

    def __init__(self, source, topic: str, entry: FeedEntry):
        assert check_argument_types()
        super().__init__(source, topic)
        self.entry = entry


class MetadataEvent(Event):
    """
    Signals that one or more metadata attributes on a feed have changed

    :ivar changes: a dictionary of attribute name ⭢ new value
    :vartype changes: Dict[str, Any]
    """

    __slots__ = 'changes'

    def __init__(self, source, topic: str, changes: Dict[str, Any]):
        assert check_argument_types()
        super().__init__(source, topic)
        self.changes = changes
