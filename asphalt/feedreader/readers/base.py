import asyncio
import logging
from abc import abstractmethod
from contextlib import suppress
from datetime import timedelta
from typing import Union, Dict, Any, List, Set, Tuple  # noqa

from aiohttp import ClientSession
from asphalt.core import Context
from multidict import CIMultiDict
from typeguard import check_argument_types

from asphalt.feedreader.api import FeedStateStore, FeedReader
from asphalt.feedreader.metadata import FeedMetadata

logger = logging.getLogger(__name__)


class BaseFeedReader(FeedReader):
    """
    Base class for news syndication feeds.

    :ivar FeedMetadata metadata: latest metadata extracted from the feed

    :param url: source URL for the feed
    """

    metadata_cls = FeedMetadata
    state_attributes = tuple(locals().keys())

    def __init__(self, url: str, store: Union[str, FeedStateStore] = None, state_id: str = None,
                 client_session: Union[str, ClientSession] = None, http_method: str = 'GET',
                 http_headers: Dict[str, Any] = None, interval: Union[int, timedelta, None] = 300):
        assert check_argument_types()
        self.url = url
        self.store = store
        self.state_id = state_id
        self.session = client_session
        self.http_method = http_method.upper()
        self.http_headers = CIMultiDict(http_headers or {})
        self.interval = interval.total_seconds() if isinstance(interval, timedelta) else interval
        self._metadata = self.metadata_cls()
        self._seen_entry_ids = set()  # type: Set[str]

        if self.store and not self.state_id:
            raise ValueError('state store provided provided but no state_id was given')

    def __getstate__(self) -> Dict[str, Any]:
        return {
            'version': 1,
            'seen_entry_ids': list(self._seen_entry_ids),
            'metadata': self._metadata.__getstate__()
        }

    def __setstate__(self, state: Dict[str, Any]) -> None:
        version = state.get('version')
        if version != 1:
            raise ValueError('cannot handle {} state version {}'.
                             format(self.__class__.__name__, version))

        for key, value in state.items():
            if key == 'seen_entry_ids':
                self._seen_entry_ids = set(value)
            elif key == 'metadata':
                metadata = self.metadata_cls()
                metadata.__setstate__(value)
                self._metadata = metadata

    @property
    def metadata(self):
        return self._metadata

    async def start(self, ctx: Context) -> None:
        if isinstance(self.store, str):
            self.store = await ctx.request_resource(FeedStateStore, self.store)

        if isinstance(self.session, str):
            self.session = await ctx.request_resource(ClientSession, self.session)
        elif self.session is None:
            self.session = ClientSession()
            ctx.add_teardown_callback(self.session.close)

        if self.store is not None:
            state = await self.store.load_state(self.name)
            self.__setstate__(state)

        if self.interval:
            loop_task = ctx.loop.create_task(self.loop_update())
            ctx.add_teardown_callback(loop_task.cancel)

    async def loop_update(self):
        with suppress(asyncio.CancelledError):
            while True:
                try:
                    await self.update()
                except asyncio.CancelledError:
                    return
                except Exception:
                    logger.exception('Error updating feed at (url=%s)', self.url)

                await asyncio.sleep(self.interval)

    async def update(self):
        document = await self.fetch_document()
        entry_ids = set()
        metadata, event_kwargs_list = self.parse_document(document)

        # Dispatch a metadata_changed event if metadata values have changed
        changes = {key: value for key, value in metadata.items()
                   if hasattr(self.metadata, key) and getattr(self.metadata, key) != value}
        if changes:
            self.metadata_changed.dispatch(changes)

        for event_kwargs in event_kwargs_list:
            if event_kwargs['id'] not in self._seen_entry_ids:
                self.entry_discovered.dispatch(**event_kwargs)
                entry_ids.add(event_kwargs['id'])

        new_ids = self._seen_entry_ids - entry_ids
        obsolete_ids = entry_ids - self._seen_entry_ids
        if (new_ids or obsolete_ids) and self.store is not None:
            state = self.__getstate__()
            await self.store.store_state(self.state_id, state)

    async def fetch_document(self) -> str:
        async with self.session.get(self.url, headers=self.http_headers) as resp:
            resp.raise_for_status()
            return await resp.text()

    @abstractmethod
    def parse_document(self, document: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Parse the downloaded document.

        :param document: the downloaded document content
        :return: a two-tuple of (feed metadata, list of constructor arguments for the feed's entry
            event class, one item for each event)
        """
