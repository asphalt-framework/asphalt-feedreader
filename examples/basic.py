"""
This script demonstrates usage with standard (RSS or Atom) feeds.

It takes a URL as a command line argument and prints out new entries from it as they come in.

Checking is done on 5 minute intervals by default and is adjustable with the -i/--interval option.
"""

import click
from asphalt.core import CLIApplicationComponent, Context, run_application
from async_generator import aclosing


class FeedReaderApp(CLIApplicationComponent):
    def __init__(self, url: str, interval: int):
        super().__init__()
        self.url = url
        self.interval = interval

    async def start(self, ctx: Context):
        self.add_component('feedreader', url=self.url, interval=self.interval)
        await super().start(ctx)

    async def run(self, ctx: Context):
        async with aclosing(ctx.feed.entry_discovered.stream_events()) as stream:
            async for event in stream:
                print('------\npublished: {event.published}\ntitle: {event.title}\n'
                      'url: {event.link}'.format(event=event))


@click.command()
@click.option('-i', '--interval', type=click.INT, default=300)
@click.argument('url')
def stream(url, interval):
    component = FeedReaderApp(url, interval)
    run_application(component)


if __name__ == '__main__':
    stream()
