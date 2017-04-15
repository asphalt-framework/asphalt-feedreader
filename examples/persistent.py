"""
This script demonstrates the use of feeds with a persistent state store.

It takes a URL as a command line argument and prints out new entries from it as they come in.
On each update, the state is saved in the database (store.db). When you restart the script, observe
how it skips the entries it reported on the first run, and only prints out new ones.

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
        self.add_component('sqlalchemy', url='sqlite:///store.db')
        self.add_component('feedreader', url=self.url, interval=self.interval,
                           store='default', stores=dict(backend='sqlalchemy'))
        await super().start(ctx)

    async def run(self, ctx: Context):
        async with aclosing(ctx.feed.entry_discovered.stream_events()) as stream:
            async for event in stream:
                print('------\npublished: {entry.published}\ntitle: {entry.title}\n'
                      'url: {entry.link}'.format(entry=event.entry))


@click.command()
@click.option('-i', '--interval', type=click.INT, default=300)
@click.argument('url')
def stream(url, interval):
    component = FeedReaderApp(url, interval)
    run_application(component)


if __name__ == '__main__':
    stream()
