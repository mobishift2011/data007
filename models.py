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

from caches import IF

import json

# see schema
DATABASE = 'ataobao2'
TABLES = ['item', 'shop', 'item_by_date', 'shop_by_date', 'shop_by_item', 'item_attr']

db = ConnectionPool(DB_HOSTS)

def get_table_live(keyspace='ataobao2'):
    """ get table schemas """
    v2t = {
        'org.apache.cassandra.db.marshal.UTF8Type': 'text',
        'org.apache.cassandra.db.marshal.LongType': 'bigint',
        'org.apache.cassandra.db.marshal.Int32Type': 'int',
        'org.apache.cassandra.db.marshal.FloatType': 'float',
        'org.apache.cassandra.db.marshal.TimestampType': 'timestamp',
        'org.apache.cassandra.db.marshal.BooleanType': 'boolean',
    }
    tables = {}
    cfs = db.execute('''select columnfamily_name, column_aliases, key_aliases
                        from system.schema_columnfamilies where keyspace_name=:keyspace''',
                    dict(keyspace=keyspace), result=True).results
    for table, cols, keys in cfs:
        pk = eval(keys)
        pk.extend(eval(cols))
        cols = {}
        for cname, validator in db.execute('''select column_name, validator from system.schema_columns
                        where keyspace_name=:keyspace and columnfamily_name=:cfname allow filtering''',
                    dict(keyspace=keyspace, cfname=table), result=True).results:
            cols[cname] = v2t.get(validator, validator)
        tables[table] = {'cols':cols, 'pk':pk}
    return tables

tables = get_table_live()

def update_item(item):
    d = item
    d['date'] = datetime.utcnow()

    table = tables['item']
    keys = list(set(table['cols'].keys()) & set(d.keys()))
    #print 'missing', list(set(table['cols'].keys()) - set(d.keys()))
    arg1 = '('+', '.join(keys)+')'
    arg2 = '(:'+', :'.join(keys)+')'
    insert_into_item =  ('''INSERT INTO ataobao2.item {} VALUES {}'''.format(arg1, arg2), d)

    table = tables['item_by_date']
    keys = list(set(table['cols'].keys()) & set(d.keys()))
    #print 'missing', list(set(table['cols'].keys()) - set(d.keys()))
    arg1 = '('+', '.join(keys)+')'
    arg2 = '(:'+', :'.join(keys)+')'
    insert_into_item_by_date =  ('''INSERT INTO ataobao2.item_by_date {} VALUES {}'''.format(arg1, arg2), d)

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
    ])

    if d['num_sold30'] == 0:
        IF.add(d['id'])
    else:
        IF.delete(d['id'])

def delete_item(itemid):
    db.execute('''delete from ataobao2.item where id=:itemid''', dict(itemid=itemid))
    db.execute('''delete from ataobao2.item_by_date where id=:itemid''', dict(itemid=itemid))

def delete_shop(shopid):
    db.execute('''delete from ataobao2.shop where id=:shopid''', dict(shopid=shopid))
    db.execute('''delete from ataobao2.shop_by_date where id=:shopid''', dict(shopid=shopid))

def update_shop(shop):
    d = shop
    d['rating'] = json.dumps(d['rating'])
    if 'promise' in d:
        d['promise'] = json.dumps(d['promise'])

    table = tables['shop']
    keys = list(set(table['cols'].keys()) & set(d.keys()))
    arg1 = '('+', '.join(keys)+')'
    arg2 = '(:'+', :'.join(keys)+')'
    insert_into_shop =  '''INSERT INTO ataobao2.shop {} VALUES {}'''.format(arg1, arg2)
    db.execute(insert_into_shop, d)

if __name__ == '__main__':
    from crawler.tbitem import get_item
    from crawler.tbshopinfo import get_shop
    item = get_item(35056712044) 
    from pprint import pprint
    pprint(item)
    update_item(item)
    #shop = get_shop(63782021)
    #pprint(shop)
    #update_shop(shop)
