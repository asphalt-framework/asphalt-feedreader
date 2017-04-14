Using the InfluxDB client
=========================

Getting the server version
--------------------------

You can find out which version of InfluxDB you're running in the following manner::

    async def handler(ctx):
        version = await ctx.influxdb.ping()
        print('Running InfluxDB version ' + version)

Writing data points
-------------------

Each data point being written into an InfluxDB database contains the following information:
   * name of the measurement (corresponds to a table in a relational database)
   * one or more tags (corresponds to indexed, non-nullable string columns in a RDBMS)
   * zero or more fields (corresponds to nullable columns in a RDBMS)
   * a timestamp (supplied by the server if omitted)

Data points can be written one at a time (:meth:`~asphalt.influxdb.client.InfluxDBClient.write`)
or many at once (:meth:`~asphalt.influxdb.client.InfluxDBClient.write_many`). It should be noted
that the former is merely a wrapper for the latter.

To write a single data point::

    async def handler(ctx):
        await ctx.influxdb.write('cpu_load_short', dict(host=server02), dict(value=0.67))
        print('Running InfluxDB version ' + version)

To write multiple data points, you need use use the :class:`~asphalt.influxdb.client.DataPoint`
class::

    async def handler(ctx):
        await ctx.influxdb.write_many([
            DataPoint('cpu_load_short', dict(host=server02), dict(value=0.67)),
            DataPoint('cpu_load_short', dict(host=server01), dict(value=0.21))
        ])

The data points don't have to be within the same measurement.

Querying the database
---------------------

This library offers the ability to query data via both raw InfluxQL queries and a programmatic
query builder. To learn how the query builder works, see the next section.

Sending raw queries is done using :meth:`~asphalt.influxdb.client.InfluxDBClient.raw_query`::

    async def handler(ctx):
        series = await ctx.influxdb.raw_query('SHOW DATABASES')
        print([row[0] for row in series])

If you include more than one measurement in the ``FROM`` clause of a ``SELECT`` query, you will
get a list of :class:`~asphalt.influxdb.query.Series` as a result::

    async def handler(ctx):
        cpu_load, temperature = await ctx.influxdb.raw_query('SELECT * FROM cpu_load,temperature')
        print([row[0] for row in series])

It is possible to send multiple queries by delimiting them with a semicolon (``;``).
If you do that, the call will return a list of results for each query, each of which may be a
:class:`~asphalt.influxdb.query.Series` or a list thereof::

    async def handler(ctx):
        db_series, m_series = await ctx.influxdb.raw_query('SHOW DATABASES; SHOW MEASUREMENTS')
        print('Databases:')
        print([row[0] for row in db_series])
        print('Measurements:')
        print([row[0] for row in m_series])

.. warning:: Due to `this bug <https://github.com/aio-libs/yarl/issues/34>`_, multiple queries with
    the same call do not currently work.

.. note:: If you want to send a query like ``SELECT ... INTO ...``, you must call
    :meth:`~asphalt.influxdb.client.InfluxDBClient.raw_query` ``with http_verb='POST'``.
    The proper HTTP verb should be automatically detected from the query string for all other
    queries.

Using the query builder
-----------------------

The query builder allows one to dynamically build queries without having to do error prone manual
string concatenation. The query builder is considered immutable, so every one of its methods
returns a new builder with the modifications made to it, just like with `SQLAlchemy`_ ORM queries.

For example, to select ``field1`` and ``field2`` from measurements ``m1`` and ``m2``::

    async def handler(ctx):
        query = ctx.influxdb.query(['field1', 'field2'], ['m1', 'm2'])
        return await query.execute()

This will produce a query like ``SELECT "field1","field2" FROM "m1","m2"``.

More complex expressions can be given but field or tag names are not automatically quoted::

    async def handler(ctx):
        query = ctx.influxdb.query('field1 + field2', 'm1')
        return await query.execute()

The query will look like ``SELECT field1 + field2 FROM "m1"``.

Filters can be added by using :meth:`~asphalt.influxdb.query.SelectQuery.where` with positional
and/or keyword arguments::

    async def handler(ctx):
        query = ctx.influxdb.query(['field1', 'field2'], 'm1').\
            where('field1 > 3.5', 'field2 < 6.2', location='Helsinki')
        return await query.execute()

This will produce a query like
``SELECT field1,field2 FROM "m1" WHERE field1 > 3.5 AND field2 < 6.2 AND location='Helsinki'``.

To use ``OR``, you have to manually include it in one of the ``WHERE`` expressions.

Further calls to ``.where()`` will add conditions to the ``WHERE`` clause of the query.
A call to ``.where()`` with no arguments will clear the ``WHERE`` clause.

Grouping by tags works largely the same way::

    async def handler(ctx):
        query = ctx.influxdb.query(['field1', 'SUM(field2)'], 'm1').group_by('tag1')
        return await query.execute()

The SQL: ``SELECT field1,SUM(field2) FROM "m1" GROUP BY "tag1"``

.. _SQLAlchemy: http://sqlalchemy.org/
