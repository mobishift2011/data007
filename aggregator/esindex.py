#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pyes import ES
from settings import ES_HOSTS

conn = ES(ES_HOSTS)

mapping = {
    'shop': {
        'properties': {
            'title': {'type': 'string', 'index': 'analyzed'},
            'logo': {'type': 'string', 'index': 'not_analyzed'},
            'cate1': {'type': 'string', 'index': 'not_analyzed'},
            'cate2': {'type': 'string', 'index': 'not_analyzed'},
            'worth': {'type': 'float', 'index': 'not_analyzed'},
            'sales': {'type': 'float', 'index': 'not_analyzed'},
            'good_rating': {'type': 'string', 'index': 'not_analyzed'},
            'type': {'type': 'string', 'index': 'not_analyzed'},
            'credit_score': {'type': 'integer', 'index': 'not_analyzed'},
            'num_products': {'type': 'integer', 'index': 'not_analyzed'},
            'average_price': {'type': 'float', 'index': 'not_analyzed'},
            'hot_items': {'type': 'string', 'index': 'not_analyzed'}, # json string
        },
    },
    'brand': {
        'properties': {
            'title': {'type': 'string', 'index': 'analyzed'},
            'cate1': {'type': 'string', 'index': 'not_analyzed'},
            'cate2': {'type': 'string', 'index': 'not_analyzed'},
            'logo': {'type': 'string', 'index': 'not_analyzed'},
            'shops': {'type': 'integer', 'index': 'not_analyzed'},
            'items': {'type': 'integer', 'index': 'not_analyzed'},
            'deals': {'type': 'integer', 'index': 'not_analyzed'},
            'sales': {'type': 'float', 'index': 'not_analyzed'},
            'delta': {'type': 'float', 'index': 'not_analyzed'},
        },
    },
}

def index_shop(shopid, info):
    conn.index(info, 'ataobao2', 'shop', shopid, bulk=True)

def index_brand(brand, info):
    conn.index(info, 'ataobao2', 'brand', shopid, bulk=True)

def flush():
    """ flushes bulk operations """
    conn.flush_bulk(forced=True)

def refresh():
    """ refresh index so that new indexed got loaded """
    conn.indices.refresh('ataobao2')

def ensure_mapping():
    conn.ensure_index('ataobao2')
    for type in mapping:
        m = mapping[type]
        conn.indices.put_mapping(type, m, ['ataobao2'])

if __name__ == '__main__':
    ensure_mapping()
