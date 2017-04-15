Using feed readers
==================

Feed readers are used by listening to their ``entry_discovered`` and ``metadata_changed`` signals.
To continuously print new entries as they come in, just stream events from the signal::

    async def print_events(ctx):
        async with aclosing(ctx.feed.entry_discovered.stream_events()) as stream:
            async for event in stream:
                print('New event: {entry.title}'.format(entry=event.entry))

Or, if you prefer callbacks::

    def new_entry_found(event):
        print('New event: {entry.title}'.format(entry=event.entry))

    ctx.feed.entry_discovered.connect(new_entry_found)

.. note:: Each feed reader class may have its own set of entry attributes beyond the ones in
    :class:`~asphalt.feedreader.events.EntryEvent`. See the API documentation for each individual
    feed reader class.

Creating new feeds on the fly
-----------------------------

If you need to create news feeds dynamically during the run time of your application, you can do
so using the :func:`~asphalt.feedreader.create_feed` function.