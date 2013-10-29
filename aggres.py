#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import binascii
import traceback

from msgpack import unpackb as unpack, packb as pack

from settings import AGGRE_URIS
from shardredis import ShardRedis

conns = []
for uri in AGGRE_URIS:
    host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(uri).groups()
    conn = redis.Redis(host=host, port=int(port), db=int(db))
    conns.append(conn)

conn = ShardRedis(conns=conns)


class ShopIndex(object):
    shopindex = 'shopindex_{}_{}_{}_{}_{}' # sortedsets for indexes
    shopinfo = 'shopinfo_{}_{}_{}_{}_{}' # hash for shopinfo of given shop
    shopcates = 'shopcates_{}_{}' # set for cates(date,cate1,cate2,monorday) info of shop
    shopbase = 'shopbase_{}_{}' # hash for shopbase info of given shop
    shopids = 'shopids_{}' # sortedsets for shopids

    def __init__(self, date):
        self.date = date
        self.pipeline = None

    def make_skey(self, cate1, cate2):
        return '{}_{}'.format(cate1, cate2)

    def multi(self):
        self.pipeline = conn.pipeline(transaction=False) 

    def execute(self):
        if self.pipeline:
            self.pipeline.execute()
            self.pipeline = None

    def clear(self):
        date = self.date
        patterns = ['shopindex_{}*'.format(date),
                    'shopcates_{}*'.format(date),
                    'shopinfo_{}*'.format(date),
                    'shopbase_{}*'.format(date),
                    'shopids_{}'.format(date),]
        for pattern in patterns:
            p = conn.pipeline()
            for key in conn.keys(pattern):
                p.delete(key)
            p.execute()

    def addshop(self, shopid):
        date = self.date
        zkey = ShopIndex.shopids.format(date)
        p = conn if self.pipeline is None else self.pipeline
        p.zadd(zkey, shopid, shopid) 

    def getshoprange(self, start, end):
        date = self.date
        zkey = ShopIndex.shopids.format(date)
        return conn.zrange(zkey, start, end) 

    def numshopids(self):
        date = self.date
        zkey = ShopIndex.shopids.format(date)
        return conn.zcard(zkey)

    def getcates(self, shopid):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        return [unpack(x) for x in p.smembers(ShopIndex.shopcates.format(date, shopid))]

    def addcates(self, shopid, cate1, cate2):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        p.sadd(
            ShopIndex.shopcates.format(date, shopid), 
            pack((cate1, cate2))
        )
         
    def incrindex(self, cate1, cate2, field, monorday, shopid, amount):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        key = ShopIndex.shopindex.format(date, cate1, cate2, field, monorday)
        p.zincrby(key, shopid, amount, skey=self.make_skey(cate1, cate2))

    def setindex(self, cate1, cate2, field, monorday, shopid, amount):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        zkey = ShopIndex.shopindex.format(date, cate1, cate2, field, monorday)
        p.zadd(zkey, shopid, amount, skey=self.make_skey(cate1, cate2))
    
    def incrinfo(self, cate1, cate2, monorday, shopid, shopinfo):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        hkey = ShopIndex.shopinfo.format(date, cate1, cate2, monorday, shopid)
        for key, value in shopinfo.items():
            p.hincrbyfloat(hkey, key, value, skey=self.make_skey(cate1, cate2))

    def setinfo(self, cate1, cate2, monorday, shopid, shopinfo):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        hkey = ShopIndex.shopinfo.format(date, cate1, cate2, monorday, shopid)
        p.hmset(hkey, shopinfo, skey=self.make_skey(cate1, cate2))

    def getinfo(self, cate1, cate2, monorday, shopid):
        date = self.date
        hkey = ShopIndex.shopinfo.format(date, cate1, cate2, monorday, shopid)
        return conn.hgetall(hkey, skey=self.make_skey(cate1, cate2))

    def incrbase(self, shopid, shopinfo):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        hkey = ShopIndex.shopbase.format(date, shopid)
        info = conn.hgetall(hkey)
        for key, value in shopinfo.items():
            p.hincrbyfloat(hkey, key, value)

    def setbase(self, shopid, shopinfo):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        hkey = ShopIndex.shopbase.format(date, shopid)
        conn.hmset(hkey, shopinfo)

    def getbase(self, shopid):
        date = self.date
        hkey = ShopIndex.shopbase.format(date, shopid)
        return conn.hgetall(hkey)

    def getcates(self, shopid):
        date = self.date
        skey = ShopIndex.shopcates.format(date, shopid)
        return [ unpack(x) for x in conn.smembers(skey) ]

class AggInfo(object):
    key =  'ataobao-aggregate-info-{}-{}'

    def __init__(self, date):
        self.date = date
        
    def clear(self):
        for type in ['item', 'shop']:
            key = AggInfo.key.format(self.date, type)
            conn.delete(key)
        
    def done_range(self, type, start, end):
        key = AggInfo.key.format(self.date, type)
        conn.rpush(key, pack((start, end)))

    def gaps(self, type):
        key = AggInfo.key.format(self.date, type)
        lowerbound = -2**63
        upperbound = 2**63
        lines = []
        for val in conn.lrange(key, 0, -1):
            start, end = unpack(val)
            lines.append([start, end])
        lines = sorted(lines)
        point = lowerbound
        gaps = []
        for start, end in lines:
            if start != point:
                gaps.append((point, start))
            point = end
        if point < upperbound:
            gaps.append((point, upperbound))
        return gaps

    def task_left(self, type):
        key = AggInfo.key.format(self.date, type)
        numkeys = conn.llen(key)
        if numkeys:
            start, end = unpack(conn.lindex(key, 0))
            step = end - start
            d, m = divmod(2**64, step)
            return d + int(bool(m)) - numkeys
        else:
            return 'unknown'
