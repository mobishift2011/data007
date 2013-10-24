#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import binascii
import traceback

from msgpack import unpackb as unpack, packb as pack

from settings import AGGRE_URI

host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(AGGRE_URI).groups()
conn = redis.Redis(host=host, port=int(port), db=int(db))

class ShopIndex(object):
    shopindex = 'shopindex_{}_{}_{}_{}_{}' # sortedsets for indexes
    shopinfo = 'shopinfo_{}_{}_{}_{}_{}' # hash for shopinfo of given shop
    shopcates = 'shopcates_{}_{}' # set for cates(date,cate1,cate2,monorday) info of shop
    shopbase = 'shopbase_{}_{}' # hash for shopbase info of given shop
    shopids = 'shopids_{}' # sortedsets for shopids

    def __init__(self, date):
        self.date = date
        self.pipeline = None

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
        p.sadd(ShopIndex.shopcates.format(date, shopid), pack((cate1, cate2)))
         
    def incrindex(self, cate1, cate2, field, monorday, shopid, amount):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        key = ShopIndex.shopindex.format(date, cate1, cate2, field, monorday)
        p.zincrby(key, shopid, amount)

    def setindex(self, cate1, cate2, field, monorday, shopid, amount):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        zkey = ShopIndex.shopindex.format(date, cate1, cate2, field, monorday)
        p.zadd(zkey, shopid, amount)
    
    def incrinfo(self, cate1, cate2, monorday, shopid, shopinfo):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        hkey = ShopIndex.shopinfo.format(date, cate1, cate2, monorday, shopid)
        for key, value in shopinfo.items():
            p.hincrbyfloat(hkey, key, value)

    def setinfo(self, cate1, cate2, monorday, shopid, shopinfo):
        date = self.date
        p = conn if self.pipeline is None else self.pipeline
        hkey = ShopIndex.shopinfo.format(date, cate1, cate2, monorday, shopid)
        p.hmset(hkey, shopinfo)

    def getinfo(self, cate1, cate2, monorday, shopid):
        date = self.date
        hkey = ShopIndex.shopinfo.format(date, cate1, cate2, monorday, shopid)
        return conn.hgetall(hkey)

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
