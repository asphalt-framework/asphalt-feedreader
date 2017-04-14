from datetime import datetime, timezone

from asphalt.feedreader.readers.rss import RSSFeedReader, RSSEntryEvent


def test_parse_document():
    document = """\
<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>Dummy Title</title>
    <link>https://www.example.org</link>
    <description>Channel Description</description>
    <item>
      <title>Dummy Item Title</title>
      <link>https://www.example.org/item1</link>
      <description>Dummy Item Description</description>
      <author>firstname.lastname@example.org</author>
      <comments>http://www.example.org/item1/comments</comments>
      <category>Foo</category>
      <category>Bar</category>
      <enclosure url="http://www.example.org/song1.mp3" length="1337" type="audio/mpeg" />
      <guid>1231230</guid>
      <pubDate>02 Apr 2017 08:29:30 GMT</pubDate>
    </item>
  </channel>
</rss>
"""
    metadata, events = RSSFeedReader.parse_document(document)
    assert metadata == {
        'title': 'Dummy Title',
        'link': 'https://www.example.org',
        'description': 'Channel Description'
    }

    # Check that the events were parsed right
    assert len(events) == 1
    event = RSSEntryEvent(None, '', **events[0])
    assert event.id == '1231230'
    assert event.title == 'Dummy Item Title'
    assert event.link == 'https://www.example.org/item1'
    assert event.published == datetime(2017, 4, 2, 8, 29, 30, tzinfo=timezone.utc)
    assert event.summary == 'Dummy Item Description'
    assert event.author == 'firstname.lastname@example.org'
    assert event.comments == 'http://www.example.org/item1/comments'
    assert event.categories == ('Foo', 'Bar')
    assert event.enclosure_url == 'http://www.example.org/song1.mp3'
    assert event.enclosure_length == 1337
    assert event.enclosure_type == 'audio/mpeg'
