from abc import ABCMeta, abstractmethod
from asphalt.core import Context, Signal
from typing import Awaitable, Dict, Any

from asphalt.feedreader.events import EntryEvent, MetadataEvent
from asphalt.feedreader.metadata import FeedMetadata


class FeedReader(metaclass=ABCMeta):
    entry_discovered = Signal(EntryEvent)
    metadata_changed = Signal(MetadataEvent)

    @abstractmethod
    def start(self, ctx: Context) -> Awaitable:
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
    def update(self) -> Awaitable:
        """Read the feed from the source and dispatch any events necessary."""

    @classmethod
    def can_parse(cls, document: str, content_type: str) -> bool:
        """
        Return ``True`` if this parser can parse this document, ``False`` otherwise.

        This method is only used for autodetection of feed type (ie. when the feed parser has not
        been specified). Autodetection is skipped when the feed parser has been explicitly given.

        :param document: document loaded from the feed URL
        :param content_type: MIME type of the loaded document

        """
        return False


class FeedStateStore(metaclass=ABCMeta):
    @abstractmethod
    def start(self, ctx: Context) -> Awaitable:
        """Initialize the store."""

    @abstractmethod
    def load_state(self, state_id: str) -> Awaitable[Dict[str, Any]]:
        """Load the named state from the store."""

    @abstractmethod
    def store_state(self, state_id: str, state: Dict[str, Any]) -> Awaitable:
        """Add or update the indicated state in the store."""
