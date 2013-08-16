#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Cassandra Connetions Pools and Column Families 

Usage::

    >>> from models import pool, item, shop
    >>> item.insert(12345: {'id':12345, 'num_reviews':34})

"""
from pycassa.pool import ConnectionPool
from pycassa.columnfamily import ColumnFamily
from pycassa.system_manager import SystemManager, LONG_TYPE, INT_TYPE, ASCII_TYPE, FLOAT_TYPE, UTF8_TYPE, BYTES_TYPE
from pycassa.cassandra.ttypes import InvalidRequestException, NotFoundException

from settings import DB_HOSTS

DATABASE = 'ataobao'
TABLE_ITEM = 'item'
TABLE_SHOP = 'shop'

SCHEMA = {
    # rowkey = id / id+'-'+YYYYMMDD
    'item': {
        'id': LONG_TYPE,
        'rcid': INT_TYPE,
        'cid': INT_TYPE,
        'sellerid': LONG_TYPE,
        'shopid': LONG_TYPE,
        'pagetype': ASCII_TYPE,
        'title': UTF8_TYPE,
        'rating': FLOAT_TYPE,
        'price': FLOAT_TYPE,
        'num_reviews': INT_TYPE,
        'num_collects': INT_TYPE,
        'num_instock': INT_TYPE,
        'num_reviews': INT_TYPE,
        'num_sold30': INT_TYPE,
        'num_views': INT_TYPE,
    },
    'shop': {
        'id': LONG_TYPE,
    }
}

def get_or_create_cp():
    try:
        pool = ConnectionPool(DATABASE, DB_HOSTS)
    except InvalidRequestException as e:
        if 'does not exist' in e.why:
            for host in DB_HOSTS:  
                sys = SystemManager(host)
                sys.create_keyspace(DATABASE, strategy_options={"replication_factor": "1"})
            pool = ConnectionPool(DATABASE, DB_HOSTS)
        else:
            raise e
    return pool

def get_or_create_cf(pool, name):
    try:
        cf = ColumnFamily(pool, name)
    except NotFoundException as e:
        for host in DB_HOSTS:  
            sys = SystemManager(host)
            sys.create_column_family(DATABASE, name, comparator_type=UTF8_TYPE)
        cf = ColumnFamily(pool, name)

    for host in DB_HOSTS:  
        sys = SystemManager(host)
        for column, value_type in SCHEMA.get(name, {}).iteritems():
            sys.alter_column(DATABASE, name, column, value_type)
    return cf

pool = get_or_create_cp()
item = get_or_create_cf(pool, TABLE_ITEM)
shop = get_or_create_cf(pool, TABLE_SHOP)
