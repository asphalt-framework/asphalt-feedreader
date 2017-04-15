"""
This script demonstrates custom parsing of arbitrary HTML page as a feed.

It reads the current events page from the website of London School of Economics and Political
Science.

Checking is done on 5 minute intervals by default and is adjustable with the -i/--interval option.

You must have ``lxml`` and ``beautifulsoup4`` installed for this to work.
"""

import re
from typing import Tuple, Dict, Any, List
from urllib.parse import urlparse

import click
from asphalt.core import CLIApplicationComponent, Context, run_application
from asphalt.feedreader import FeedEntry, BaseFeedReader
from async_generator import aclosing
from dateutil.parser import parse
from lxml.html import soupparser

lse_path_re = re.compile(r'/Events/\d{4}/\d{2}/(.+?)/')


class LSEFeedReader(BaseFeedReader):
    @classmethod
    def parse_document(cls, document: str) -> Tuple[Dict[str, Any], List[FeedEntry]]:
        # Use BeautifulSoup to parse the document
        root = soupparser.fromstring(document, features='html.parser')

        # The entries we seek are all contained in a single <div> element with class="largeList"
        # and each entry is contained within an <a> element
        entries = []
        for a in root.xpath('.//div[@class="largeList"]/a'):
            kwargs = {}

            # The "title" attribute in each <a> element contains the URL, from which we also
            # extract the unique entry ID
            url = urlparse(a.attrib['title'])
            match = lse_path_re.match(url.path)
            if not match:
                continue

            kwargs['id'] = match.group(1)
            kwargs['title'] = a.findtext('.//h2').strip()
            kwargs['link'] = a.attrib['title']
            kwargs['published'] = parse(a.find('.//time').attrib['datetime'])
            kwargs['enclosure_url'] = a.find('.//img').attrib['src']
            entries.append(FeedEntry(**kwargs))

        return {}, entries


class CustomFeedReaderApp(CLIApplicationComponent):
    URL = 'http://www.lse.ac.uk/Events/Search-Events'

    def __init__(self, interval: int):
        super().__init__()
        self.interval = interval

    async def start(self, ctx: Context):
        self.add_component('feedreader', url=self.URL, reader=LSEFeedReader,
                           interval=self.interval)
        await super().start(ctx)

    async def run(self, ctx: Context):
        async with aclosing(ctx.feed.entry_discovered.stream_events()) as stream:
            async for event in stream:
                print('------\npublished: {entry.published}\ntitle: {entry.title}\n'
                      'url: {entry.link}'.format(entry=event.entry))


@click.command()
@click.option('-i', '--interval', type=click.INT, default=300)
def stream(interval):
    component = CustomFeedReaderApp(interval)
    run_application(component)


if __name__ == '__main__':
    stream()
