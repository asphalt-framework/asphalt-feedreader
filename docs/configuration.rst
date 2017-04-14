Configuration
-------------

.. highlight:: yaml

The typical InfluxDB configuration using a single database at ``localhost`` on the default port
would look like this::

    components:
      influxdb:
        db: mydb

The above configuration creates an :class:`asphalt.influxdb.client.InfluxDBClient` instance in the
context, available as ``ctx.influxdb`` (resource name: ``default``).

If you wanted to connect to ``influx.example.org`` on port 8886, you would do::

    components:
      influxdb:
        base_urls: http://influx.example.org:8886
        db: mydb

To connect to an InfluxEnterprise cluster, list all the nodes under ``base_urls``::

    components:
      influxdb:
        base_urls:
          - http://influx1.example.org:8086
          - http://influx2.example.org:8086
          - http://influx3.example.org:8086
        db: mydb

To connect to two unrelated InfluxDB servers, you could use a configuration like::

    components:
      influxdb:
        clients:
          influx1:
            base_urls: http://influx.example.org:8886
            db: mydb
          influx2:
            context_attr: influxalter
            base_urls: https://influxalter.example.org/influxdb
            db: anotherdb
            username: testuser
            password: testpass

This configuration creates two :class:`asphalt.influxdb.client.InfluxDBClient` resources,
``influx1`` and ``influx2`` (``ctx.influx1`` and ``ctx.influxalter``) respectively.

.. note:: See the documentation of the :class:`asphalt.influxdb.client.InfluxDBClient` class for
    a comprehensive listing of all connection options.
