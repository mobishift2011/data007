#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Cassandra Connetions Pools and Column Families 

Usage::

    >>> from models import db
    >>> db.execute('CQL QUERY')

See more details in ``ConnectionPool``'s doc

"""
from cqlutils import ConnectionPool

from settings import DB_HOSTS
from datetime import datetime

# see schema
DATABASE = 'ataobao2'
TABLES = ['item', 'shop', 'item_by_date', 'shop_by_date', 'shop_by_item', 'item_attr']

db = ConnectionPool(DB_HOSTS)

def update_item(item):
    # Item Fields:
    #   id, cid, rcid, shopid, pagetype, title, price, rating, 
    #   num_collects, num_instock, num_reviews, num_sold30, num_views 
    # Item_by_date Fields:
    #   id, date, title, price, num_collects, num_instock, num_reviews, num_sold30, num_views
    d = item
    d['date'] = datetime.utcnow()

    insert_into_item =  \
        ('''INSERT INTO ataobao2.item
                (id, cid, rcid, shopid, pagetype, title, price, rating,
                 num_collects, num_instock, num_reviews, num_sold30, num_views)
            VALUES
                (:id, :cid, :rcid, :shopid, :pagetype, :title, :price, :rating,
                 :num_collects, :num_instock, :num_reviews, :num_sold30, :num_views)''', d)

    insert_into_item_by_date = \
        ('''INSERT INTO ataobao2.item_by_date
                (id, date, title, price, num_collects, num_instock, num_reviews, num_sold30, num_views)
            VALUES
                (:id, :date, :title, :price, :num_collects, :num_instock, :num_reviews, :num_sold30, :num_views)''', d)

    # Here we use :v1, :v2, :v3 instead of :id, :date, :iid
    # because in batch mode, arguments are passed in batch, 
    # we must avoid different variables using same name
    # though we can improve ``batch`` mechanism to avoid this problem,
    # I think it may cost too much time, and may be too inefficient to do so
    insert_into_shop_by_item = \
        ('''INSERT INTO ataobao2.shop_by_item
                (id, date, iid) 
            VALUES 
                (:v1, :v2, :v3)''', dict(v1=d['shopid'], v2=d['date'], v3=d['id']))

    db.batch([
            insert_into_item,
            insert_into_item_by_date,
            insert_into_shop_by_item])

    # batch insert attributes
    insert_into_item_attr = \
        [ ('''INSERT INTO ataobao2.item_attr
                (id, attr_name, attr_value)
              VALUES
                (?, ?, ?)''', (d['id'], a[0], ':'.join(a[1:]))) for a in d['attributes'] ]

    if insert_into_item_attr:
        db.batch(insert_into_item_attr)



if __name__ == '__main__':
    from crawler.tbitem import get_item
    item = get_item(20234093898) 
    from pprint import pprint
    pprint(item)
    update_item(item)
