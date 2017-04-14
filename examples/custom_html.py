"""
This script demonstrates custom parsing of arbitrary HTML page as a feed.

It reads the current events page from the website of London School of Economics and Political
Science.

Checking is done on 5 minute intervals by default and is adjustable with the -i/--interval option.

"""

import re
from typing import Tuple, Dict, Any, List
from urllib.parse import urlparse

import click
from asphalt.core import CLIApplicationComponent, Context, run_application
from async_generator import aclosing
from dateutil.parser import parse
from lxml.html import soupparser

from asphalt.feedreader.readers.base import BaseFeedReader

lse_path_re = re.compile(r'/Events/\d{4}/\d{2}/(.+?)/')


class LSEFeedReader(BaseFeedReader):
    @classmethod
    def parse_document(cls, document: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        # Use BeautifulSoup to parse the document
        root = soupparser.fromstring(document, features='html.parser')

        entries = []
        for a in root.xpath('.//div[@class="largeList"]/a'):
            entry = {}
            url = urlparse(a.attrib['title'])
            match = lse_path_re.match(url.path)
            if not match:
                continue

            entry['id'] = match.group(1)
            entry['title'] = a.findtext('.//h2').strip()
            entry['link'] = a.attrib['title']
            entry['published'] = parse(a.find('.//time').attrib['datetime'])
            entry['enclosure_url'] = a.find('.//img').attrib['src']
            entries.append(entry)

        return {}, entries


class CustomFeedReaderApp(CLIApplicationComponent):
    URL = 'http://www.lse.ac.uk/Events/Search-Events'

    def __init__(self, interval: int):
        super().__init__()
        self.interval = interval

    async def start(self, ctx: Context):
        self.add_component('feedreader', url=self.URL, kind=LSEFeedReader, interval=self.interval)
        await super().start(ctx)

    async def run(self, ctx: Context):
        async with aclosing(ctx.feed.entry_discovered.stream_events()) as stream:
            async for event in stream:
                print('------\npublished: {event.published}\ntitle: {event.title}\n'
                      'url: {event.link}'.format(event=event))


@click.command()
@click.option('-i', '--interval', type=click.INT, default=300)
def stream(interval):
    component = CustomFeedReaderApp(interval)
    run_application(component)


if __name__ == '__main__':
    stream()
