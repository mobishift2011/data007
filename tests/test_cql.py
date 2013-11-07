#!/usr/bin/env python
from gevent import monkey; monkey.patch_all()

from cqlutils import ConnectionPool

def test_connection():
    pool = ConnectionPool()
