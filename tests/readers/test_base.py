from typing import Tuple, Dict, Any, List

import pytest
from async_generator import aclosing
from defusedxml.ElementTree import fromstring

from asphalt.core import stream_events
from asphalt.feedreader import FeedEntry
from asphalt.feedreader.events import MetadataEvent, EntryEvent
from asphalt.feedreader.readers.base import BaseFeedReader


class DummyFeedReader(BaseFeedReader):
    async def fetch_document(self) -> str:
        return '<feed><entry id="1" title="foo"/><entry id="2" title="bar"/></feed>'

    def parse_document(self, document: str) -> Tuple[Dict[str, Any], List[FeedEntry]]:
        root = fromstring(document)
        entries = []
        for tag in root.findall('entry'):
            entries.append(FeedEntry(id=tag.attrib['id'], title=tag.attrib['title']))

        return {'title': 'feed title'}, entries


@pytest.fixture
def feed():
    return DummyFeedReader('http://localhost/blah')


def test_getstate(feed):
    feed._seen_entry_ids = {'a', 'b'}
    state = feed.__getstate__()
    state['seen_entry_ids'].sort()
    assert state == {
        'version': 1,
        'seen_entry_ids': ['a', 'b'],
        'metadata': {
            'version': 1
        }
    }


def test_setstate(feed):
    feed.__setstate__({
        'version': 1,
        'seen_entry_ids': ['a', 'b'],
        'metadata': {
            'version': 1,
            'title': 'feed title'
        }
    })
    assert feed._seen_entry_ids == {'a', 'b'}
    assert feed.metadata.title == 'feed title'


@pytest.mark.asyncio
async def test_update(event_loop, feed):
    async def catch_events():
        events = []
        async with aclosing(stream_events(
                [feed.metadata_changed, feed.entry_discovered])) as stream:
            async for event in stream:
                events.append(event)
                if len(events) == 3:
                    return events

    catch_events_task = event_loop.create_task(catch_events())
    update_task = event_loop.create_task(feed.update())

    await update_task
    events = await catch_events_task
    assert isinstance(events[0], MetadataEvent)
    assert events[0].changes == {'title': 'feed title'}
    assert feed.metadata.title == 'feed title'

    assert isinstance(events[1], EntryEvent)
    assert isinstance(events[2], EntryEvent)
    assert events[1].entry.id == '1'
    assert events[1].entry.title == 'foo'
    assert events[2].entry.id == '2'
    assert events[2].entry.title == 'bar'
