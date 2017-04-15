from datetime import datetime, timezone, timedelta
from typing import cast

import pytest

from asphalt.feedreader.readers.atom import AtomFeedReader, Person, AtomEntry


@pytest.mark.parametrize('document, content_type, error', [
    ('<feed></feed>', 'text/html',
     "Incompatible content type (got 'text/html', needs to be either 'application/atom+xml' "
     "or 'text/xml')"),
    ('brdytgrdt', 'text/xml', 'Error parsing the document as XML: syntax error: line 1, column 0'),
    ('<foo></foo>', 'text/xml', ('Incompatible root tag (got <foo>, needs to be <feed> in the '
                                 'http://www.w3.org/2005/Atom namespace)')),
    ('<feed xmlns="http://www.w3.org/2005/Atom"></feed>', 'application/atom+xml', None)
], ids=['content_type', 'xml_error', 'root_tag', 'all_ok'])
def test_can_parse(document, content_type, error):
    assert AtomFeedReader.can_parse(document, content_type) == error


def test_parse_document():
    document = """\
<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
 <title type="text">dive into mark</title>
 <subtitle type="html">
   A &lt;em&gt;lot&lt;/em&gt; of effort
   went into making this effortless
 </subtitle>
 <updated>2005-07-31T12:29:29Z</updated>
 <id>tag:example.org,2003:3</id>
 <link rel="alternate" type="text/html"
  hreflang="en" href="http://example.org/"/>
 <link rel="self" type="application/atom+xml"
  href="http://example.org/feed.atom"/>
 <rights>Copyright (c) 2003, Mark Pilgrim</rights>
 <generator uri="http://www.example.com/" version="1.0">
   Example Toolkit
 </generator>
 <entry>
   <title>Dummy Entry Title</title>
   <link rel="alternate" type="text/html"
    href="http://example.org/2005/04/02/atom"/>
   <link rel="enclosure" type="audio/mpeg" length="1337"
    href="http://example.org/audio/ph34r_my_podcast.mp3"/>
   <id>tag:example.org,2003:3.2397</id>
   <updated>2005-07-31T12:29:29Z</updated>
   <published>2003-12-13T08:29:29-04:00</published>
   <author>
     <name>Mark Pilgrim</name>
     <uri>http://example.org/</uri>
     <email>f8dy@example.com</email>
   </author>
   <contributor>
     <name>Sam Ruby</name>
   </contributor>
   <contributor>
     <name>Joe Gregorio</name>
   </contributor>
   <content type="xhtml" xml:lang="en"
    xml:base="http://diveintomark.org/">
     <div xmlns="http://www.w3.org/1999/xhtml">
       <p><i>[Update: The Atom draft is finished.]</i></p>
     </div>
   </content>
 </entry>
</feed>
"""
    metadata, events = AtomFeedReader.parse_document(document)
    assert metadata == {
        'title': 'dive into mark',
        'description': 'A <em>lot</em> of effort\n   went into making this effortless',
        'updated': datetime(2005, 7, 31, 12, 29, 29, tzinfo=timezone.utc),
        'id': 'tag:example.org,2003:3',
        'link': 'http://example.org/',
        'copyright': 'Copyright (c) 2003, Mark Pilgrim',
        'generator': 'Example Toolkit'
    }

    assert len(events) == 1
    event = cast(AtomEntry, events[0])
    assert event.id == 'tag:example.org,2003:3.2397'
    assert event.title == 'Dummy Entry Title'
    assert event.link == 'http://example.org/2005/04/02/atom'
    assert event.published == datetime(2003, 12, 13, 8, 29, 29,
                                       tzinfo=timezone(-timedelta(hours=4)))
    assert event.updated == datetime(2005, 7, 31, 12, 29, 29, tzinfo=timezone.utc)
    assert event.authors == (Person(name='Mark Pilgrim', uri='http://example.org/',
                                    email='f8dy@example.com'),)
    assert event.contributors == (Person('Sam Ruby'), Person('Joe Gregorio'))
    assert event.enclosure_url == 'http://example.org/audio/ph34r_my_podcast.mp3'
    assert event.enclosure_length == 1337
    assert event.enclosure_type == 'audio/mpeg'
    assert event.content_type == 'xhtml'
