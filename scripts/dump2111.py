#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey; monkey.patch_all()
import gevent.pool

import os
import re
import time
import pyes
import redis
import struct
import socket
from cqlutils import ConnectionPool
from datetime import datetime, timedelta


pool = gevent.pool.Pool(8)

r1 = redis.Redis()
r2 = redis.Redis(host='192.168.2.111')
db1 =  ConnectionPool(['localhost:9160'])
db2 =  ConnectionPool(['192.168.2.111:9160'])
es1 = pyes.ES('localhost:9200')
es2 = pyes.ES('192.168.2.111:9200')

schemafile = os.path.join(os.path.dirname(__file__), '..', 'schema.cql')

schemacontent = open(schemafile).read()

schemas = {}
for table, schema in re.compile(r'CREATE TABLE IF NOT EXISTS (\S+) \((.*?)\);', re.DOTALL).findall(schemacontent):
    fields = []
    for col in schema.split('\n'):
        col = col.strip()
        if col and not col.startswith('PRIMARY'):
            col = col.split(' ', 1)[0]
            fields.append(col)
    schemas['ataobao2.'+table] = fields

def sync_table(table, fields):
    f1 = ', '.join(fields)
    pieces = {
        'ataobao2.item': 100,
        'ataobao2.item_by_date': 1000,
        'ataobao2.brand_by_date': 10,
        'ataobao2.shop_by_date': 10,
    }.get(table, 1)
    start = -2**63
    step = 2**64/pieces
    print 'migrating {} {}'.format(table, f1)

    for i in range(pieces):
        start = -2**63 + step*i
        end = min(2**63-1, -2**63+step*(i+1))
        with db1.connection() as cur:
            print 'piece', i+1
            #print 'select {} from {} where token({})>=:v1 and token({})<:v2'.format(f1, table, fields[0], fields[0]), dict(v1=start, v2=end)
            if table.endswith('_by_date') and 'datestr' in fields:
                d0 = (datetime.utcnow() + timedelta(hours=8) - timedelta(days=2)).strftime('%Y-%m-%d')
                cur.execute('select {} from {} where token({})>=:v1 and token({})<:v2 and datestr>=:d0 allow filtering'.format(f1, table, fields[0], fields[0]), 
                        dict(v1=start, v2=end, d0=d0), consistency_level='ONE')
            else:
                cur.execute('select {} from {} where token({})>=:v1 and token({})<:v2'.format(f1, table, fields[0], fields[0]), 
                        dict(v1=start, v2=end), consistency_level='ONE')
            for j, row in enumerate(cur):
                if j % 1000 == 0:
                    print 'syncd {}'.format(j)
                params = {}
                fs = list(fields)
                for k,v in zip(fields, row):
                    if k == 'date':
                        if v is not None and len(v)==8:
                            v = struct.unpack('!q', v)[0]
                        else:
                            continue
                    if v is not None:
                        params[k] = v 
                fs = params.keys()
                fs1 = ', '.join(fs)
                fs2 = ', '.join([':'+f for f in fs])
                if 'id' in params or 'datestr' in params or 'name' in params:
                    if table == 'ataobao2.item_by_date' and 'date' not in params:
                        continue
                    #print 'INSERT INTO {} ({}) VALUES ({})'.format(table, fs1, fs2), params
                    pool.spawn(db2.execute, 'insert into {} ({}) values ({})'.format(table, fs1, fs2), params)
    
def sync_cassandra():
    for table, fields in sorted(schemas.items(), key=lambda x: len(x[0])):
        #if table == 'ataobao2.top10':
        if True:
            sync_table(table, fields)
    pool.join()

def sync_redis():
    r2.slaveof('no', 'one')
    ip = socket.gethostbyname(socket.gethostname())
    print "slaveof {} {}".format(ip, 6379)
    ok = r2.slaveof(ip, 6379)
    if not ok:
        print "can't do slaveof to {}:{}".format(ip, 6379)
        return 
    while True:
        time.sleep(3)
        print('check for sync')
        sync = True
        r2info = r2.info()
        for key, value in r1.info().items():
            if key.startswith('db'):
                if key not in r2info: 
                    sync = False
                    break
                if value['keys'] != r2info[key]['keys']:
                    sync = False
                    break
        if sync:
            break
    r2.slaveof('no', 'one')

def sync_elasticsearch():
    from aggregator.esindex import mapping
    es2.ensure_index('ataobao2')
    for type in mapping:
        m = mapping[type]
        es2.indices.put_mapping(type, m, ['ataobao2'])

    for type in ['shop', 'brand']:
        print 'syncing elasticsearch', type
        hits = es1.search_raw({'size':50000}, 'ataobao2', type)
        hits = hits['hits']['hits']
        for hit in hits:
            shopid = hit['_id']
            info = hit['_source']
            es2.index(info, 'ataobao2', type, shopid, bulk=True)
        es2.flush_bulk(forced=True)
        es2.refresh()

if __name__ == '__main__':
    sync_redis()
    sync_elasticsearch()
    sync_cassandra()
