#!/usr/bin/env python
""" Simple Pooling and Load Balancing ConnectionPool Using cql3 

Setup pooling::

>>> from cqlutils import ConnectionPool
>>> pool = ConnectionPool(hosts=['localhost:9160'])

Single execution, set result=True to fetch results::

>>> pool.execute('select * from test.test', result=True)

Argument binding is supported, too::

>>> pool.execute('insert into test.test (id, date, field, value) values (?, ?, ?, ?)',
...              (1, 0, 'testfield', 'testvalue'))

Using CQL3's own binding syntax(but with datetime handling)::

>>> pool.execute('insert into xxx (key, val) values (:key, :val)',
...              dict(key='key', val='val'))

Datetime is processed as expected::

>>> import datetime
>>> utcnow = datetime.datetime.utcnow()
>>> pool.execute('insert into test.test (id, date, field, value) values (?, ?, ?, ?)',
...              (1, utcnow, 'testfield', 'testvalue'))
>>> r = pool.execute('select * from test.test where id=1 and date=?', 
...                  (utcnow,), result=True)
>>> assert r.results[0] == (1, utcnow.replace(microsecond=0), 'testfield', 'testvalue')

Using cursor::

>>> with pool.connection() as cur:
...     # note cur does not accept dbapi2-favored argument bindings
...     cur.execute('CQL QUERY') 
...
...     # it does accept arguments like this, however, datetime is unhandled
...     cur.execute('INSERT INTO xxx (KEY, COL) VALUES (:key, :val)',
...                 dict(key='key', val='val'))
...
...     # or you can manually setup bindings for query like this
...     query, bindings = pool.setup_bindings(query, bindings)
...     cur.execute(query, bindings)

Multi-query shortcut( /w bindings)::

>>> pool.batch(['CQL QUERY1', 'CQL QUERY2'])
>>> pool.batch([('CQL QUERY1 /W BINDINGS1', bindings1), 
...             ('CQL QUERY2 /W BINDINGS2', bindings2)])

"""
import cql
import Queue
import random
import logging
from collections import namedtuple
from contextlib import contextmanager

class RowResult(tuple):
    pass

QueryResult = namedtuple('RowResult', ('columns', 'results'))

def _column_tuple_factory(colnames, values):
    return tuple(colnames), [RowResult(v) for v in values]

class ConnectionPool(object):
    """Handles pooling of database connections."""
    def __init__(self, hosts=['localhost:9160'], 
                 poolsize=10,
                 overflowsize=0,
                 maxretries=5,
                 username=None, 
                 password=None, 
                 consistency='ONE'):
        self.hosts = hosts
        self.username = username
        self.password = password
        self.poolsize = poolsize
        self.overflowsize = overflowsize
        self.maxretries = maxretries
        self.consistency = consistency
        self.queue = Queue.Queue(maxsize=self.poolsize)
        self.connection_in_use = 0

    def clear(self):
        """
        Force the connection pool to be cleared. Will close all internal
        connections.
        """
        try:
            while not self.queue.empty():
                self.queue.get().close()
        except:
            pass

    def get(self):
        """
        Returns a usable database connection. Uses the internal queue to
        determine whether to return an existing connection or to create
        a new one.
        """
        if self.queue.empty() and self.connection_in_use < self.poolsize+self.overflowsize:
            return self._create_connection()
        return self.queue.get()

    def put(self, conn):
        """
        Returns a connection to the queue freeing it up for other queries to
        use.

        :param conn: The connection to be released
        :type conn: connection
        """

        if self.queue.full():
            conn.close()
        else:
            self.queue.put(conn)

    def _create_connection(self):
        """
        Creates a new connection for the connection pool.

        should only return a valid connection that it's actually connected to
        """
        if not self.hosts:
            raise Exception("At least one host required")

        random.shuffle(self.hosts)

        for hoststr in self.hosts:
            host, port = hoststr.split(':')
            try:
                new_conn = cql.connect(
                    host,
                    int(port),
                    user=self.username,
                    password=self.password,
                    consistency_level=self.consistency
                )
                new_conn.set_cql_version('3.0.0')
                return new_conn
            except Exception as e:
                logging.exception("Could not establish connection to {}:{}".format(host, port))

        raise Exception("Could not connect to any server in cluster")

    @contextmanager
    def connection(self):
        retrycount = 0
        yielded = False
        while yielded is False and retrycount < self.maxretries:
            try:
                conn = self.get()
                cur = conn.cursor()
                yield cur
            except cql.ProgrammingError as e:
                raise e
            except Exception as e:
                conn = None
                logging.exception(e)
                retrycount += 1
            else:
                yielded = True
                retrycount = 0
            finally:
                if conn is not None:
                    cur.close()
                    self.put(conn)

        if yielded is False:
            raise Exception('Could not obtain cursor, max retry count reached: {}'.format(retrycount))

    def execute(self, query, bindings=None, result=False):
        with self.connection() as cur:
            query, bindings = self.setup_bindings(query, bindings)
            resp = cur.execute(query, bindings)

            if result is False:
                return resp

            else:
                columns = [i[0] for i in cur.description or []]
                validators = self.build_validators(i[1] for i in cur.description or [])
                map_validators = lambda validator, value: validator(value)
                results = [RowResult(map(map_validators, validators, row)) for row in cur]
                return QueryResult(columns, results)

    def batch(self, query_iterator):
        with self.connection() as cur:
            mode = 'none'
            binding_list = []
            binding_dict = {}
            query_stmt = ['BEGIN BATCH']
            for query in query_iterator:
                if isinstance(query, list) or isinstance(query, tuple):
                    query, bindings = query
                    if isinstance(bindings, dict):
                        binding_dict.update(bindings)
                        mode = 'dict'
                    else:
                        binding_list.extend(bindings)
                        mode = 'list'
                query_stmt.append(query)
            query_stmt.append('APPLY BATCH')
            query = '\n'.join(query_stmt)
            bindings = {'dict':binding_dict, 'list':binding_list, 'none':None}.get(mode)
            query, bindings = self.setup_bindings(query, bindings)
            resp = cur.execute(query, bindings)
            return resp

    def build_validators(self, columns):
        import datetime
        validators = []
        for coltype in columns:
            if coltype == 'DateType':
                validators.append(lambda x: datetime.datetime.utcfromtimestamp(x))
            else:
                validators.append(lambda x: x)
        return validators

    def setup_bindings(self, query, bindings):
        import calendar
        import datetime
        try:
            if bindings is None:
                return query, bindings
            elif isinstance(bindings, tuple) or isinstance(bindings, list):
                reps = [ ':v{}'.format(i) for i in range(len(bindings)) ]
                query = query.replace('?', '{}').format(*reps)
                bindings = {'v{}'.format(i): bindings[i] for i in range(len(bindings))}
            
            # handling datetimes
            for key in bindings:
                if isinstance(bindings[key], datetime.datetime):
                    bindings[key] = calendar.timegm(bindings[key].utctimetuple())*1000
                elif isinstance(bindings[key], unicode):
                    bindings[key] = bindings[key].encode('utf-8')
            return query, bindings
        except Exception as e:
            logging.exception(e)
            raise Exception('Binding setup failed') 
