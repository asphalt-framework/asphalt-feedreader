from abc import ABCMeta, abstractmethod
from typing import Awaitable, Dict, Any, Optional

from asphalt.core import Context, Signal

from asphalt.feedreader.events import EntryEvent, MetadataEvent
from asphalt.feedreader.metadata import FeedMetadata


class FeedReader(metaclass=ABCMeta):
    """
    Interface for feed readers.

    :var entry_discovered: a signal dispatched when a resource has been published in this context
    :vartype entry_discovered: Signal[EntryEvent]
    :var metadata_changed: a signal dispatched when the feed metadata has been changed
    :vartype metadata_changed: Signal[MetadataEvent]
    :ivar str url: the feed URL
    """

    entry_discovered = Signal(EntryEvent)
    metadata_changed = Signal(MetadataEvent)
    url = None  # type: str

    @abstractmethod
    def start(self, ctx: Context) -> Awaitable[None]:
        """
        Initialize the feed.

        This should do the following:

        * Claim any required resources (including the state store if defined)
        * Load the state from the store (if a store was defined)
        * Conditionally start a timer task that calls :meth:`~.update` on the configured intervals
        """

    @abstractmethod
    def __getstate__(self) -> Dict[str, Any]:
        """
        Return persistable state of the feed.

        The returned structure must be JSON compatible.
        """

    @abstractmethod
    def __setstate__(self, state: Dict[str, Any]) -> None:
        """Apply previously saved state to this feed."""

    @property
    @abstractmethod
    def metadata(self) -> FeedMetadata:
        """Return the feed's metadata."""

    @abstractmethod
    def update(self) -> Awaitable[None]:
        """Read the feed from the source and dispatch any events necessary."""

    @classmethod
    def can_parse(cls, document: str, content_type: str) -> Optional[str]:
        """
        Determine if this reader class is suitable for parsing the given document as a feed.

        This method is only used for autodetection of feed type by
        :func:`~asphalt.feedreader.component.create_feed` (ie. when the feed parser has not
        been specified). Autodetection is skipped when the feed parser has been explicitly given.

        :param document: document loaded from the feed URL
        :param content_type: MIME type of the loaded document
        :return: the reason why this class cannot parse the given document, or ``None`` if it can
            parse it

        """
        return 'Autodetection not implemented for this class'


class FeedStateStore(metaclass=ABCMeta):
    """Interface for feed state stores."""

    @abstractmethod
    def start(self, ctx: Context) -> Awaitable[None]:
        """Initialize the store."""

    @abstractmethod
    def load_state(self, state_id: str) -> Awaitable[Dict[str, Any]]:
        """Load the named state from the store."""

    @abstractmethod
    def store_state(self, state_id: str, state: Dict[str, Any]) -> Awaitable[None]:
        """Add or update the indicated state in the store."""
