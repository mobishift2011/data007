#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import hashlib
import binascii
import traceback

from msgpack import unpackb as unpack, packb as pack

from settings import AGGRE_URIS
from shardredis import ShardRedis
from thinredis import CappedSortedSet

conns = []
for uri in AGGRE_URIS:
    host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(uri).groups()
    conn = redis.Redis(host=host, port=int(port), db=int(db))
    conns.append(conn)

conn = ShardRedis(conns=conns)


class ShopIndex(object):
    shopindex = 'shopindex_{}_{}_{}_{}_{}' # (date, cate1, cate2, field, monorday); sortedsets for indexes
    shopinfo = 'shopinfo_{}_{}_{}_{}_{}' # (date, cate1, cate2, monorday, shopid); hash for shopinfo of given shop under give cates(cate1, cate2), by given period(day/mon)
    shopcates = 'shopcates_{}_{}' # (date, shopid); set for cates(cate1,cate2) info of shop
    shopbase = 'shopbase_{}_{}' # (date, shopid); hash for shopbase info of given shop
    shophotitems = 'shophotitems_{}_{}' # (date, shopid); sortedset for (id, sales)
    shopcatescount = 'shopcatescount_{}_{}' #(date, shopid); hash(cate1 -> counts)
    shopbrandinfo = 'shopbrandinfo_{}_{}_{}' # (date, shopid, deals/sales); hash(brand -> value) => should aggregate to shopinfo/cassandra

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
                    'shophotitems_{}*'.format(date),
                    'shopcatescount_{}'.format(date),
                    'shopbrandinfo_{}*'.format(date),
                    ]
        for pattern in patterns:
            p = conn.pipeline()
            for key in conn.keys(pattern):
                p.delete(key)
            p.execute()

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
        p.hincrby(
            ShopIndex.shopcatescount.format(date, shopid),
            cate1,
            1
        )

    def incrbrand(self, shopid, field, brand, value):
        hkey = ShopIndex.shopbrandinfo.format(self.date, shopid, field)
        p = conn if self.pipeline is None else self.pipeline
        p.hincrbyfloat(hkey, brand, value)

    def addhotitems(self, shopid, itemid, sales):
        zkey = ShopIndex.shophotitems.format(self.date, shopid)
        p = conn if self.pipeline is None else self.pipeline
        # equals to p.zadd(zkey, itemid, sales), capped to 10, shared by skey
        CappedSortedSet(zkey, 10, p, skey=zkey).zadd(itemid, sales)
         
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


class ItemIndex(object):
    itemindex = 'itemindex_{}_{}_{}_{}_{}' # (date, cate1, cate2, field, monorday); sorted set for item index
    iteminfo = 'iteminfo_{}_{}' # (date, itemid); hash for item info
    itemcatescount = 'itemcatescount_{}' # (date); hash(cate1,cate2->count)
    itemcatessales = 'itemcatessales_{}' # (date); hash(cate1,cate2->sales)
        
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
        patterns = ['itemindex_{}*'.format(date),
                    'iteminfo_{}*'.format(date),
                    'itemcatescount_{}*'.format(date),
                    'itemcatessales_{}*'.format(date),
                    ]
        for pattern in patterns:
            p = conn.pipeline()
            for key in conn.keys(pattern):
                p.delete(key)
            p.execute()

    def incrcates(self, cate1, cate2, sales, deals):
        hkey1 = ItemIndex.itemcatescount.format(self.date, cate1, cate2)
        hkey2 = ItemIndex.itemcatescount.format(self.date, cate1, cate2)
        p = conn if self.pipeline is None else self.pipeline
        p.hincrby(hkey1, self.make_skey(cate1, cate2), deals) 
        p.hincrbyfloat(hkey2, self.make_skey(cate1, cate2), sales) 

    def incrindex(self, cate1, cate2, field, monorday, itemid, amount):
        zkey = ItemIndex.itemindex.format(self.date, cate1, cate2, field, monorday)
        p = conn if self.pipeline is None else self.pipeline
        CappedSortedSet(zkey, 1000, p, skey=zkey).zadd(itemid, amount, skey=self.make_skey(cate1, cate2))
    
    def setinfo(self, itemid, iteminfo):
        hkey = ItemIndex.iteminfo.format(self.date, itemid) 
        p = conn if self.pipeline is None else self.pipeline
        p.hmset(hkey, iteminfo)


class BrandIndex(object):
    brandshop = 'brandshop_{}_{}' # (date, brandname), set for shopids, used for num_of_shops
    brandinfo = 'brandinfo_{}_{}_{}_{}' # (date, brandname, cate1, cate2); hash for brand info
                                        # num_of_items, deals, sales, delta_sales, *share*
    brandcates = 'brandcates_{}_{}' # (date, brandname); set for (cate1, cate2) pairs 
    brands = 'brands_{}' # (date); set for brandnames
    brandbase = 'brandbase_{}_{}' # (date, brandname(utf-8)); hash for brand total info
                                  # name, logo, sales, deals, num_of_items, num_of_shops, 
    brandsales = 'brandsales_{}_{}_{}' # (date, cate1, cate2); zset(brandname, sales), capped to 1000
    brandtopitems = 'brandtopitems_{}_{}_{}' # (date, brandname, cate1); zset(itemid, sales), capped to 10
    brandtopshops = 'brandtopshops_{}_{}_{}' # (date, brandname, cate1); zset(shopid, sales), capped to 10
        
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
        patterns = ['brandshop_{}*'.format(date),
                    'brandinfo_{}*'.format(date),
                    'brandcates_{}*'.format(date),
                    'brandbase_{}*'.format(date),
                    'brandsales_{}*'.format(date),
                    'brandtopitems_{}*'.format(date),
                    'brandtopshops_{}*'.format(date),
                    ]
        for pattern in patterns:
            p = conn.pipeline()
            for key in conn.keys(pattern):
                p.delete(key)
            p.execute()

    def addshop(self, brand, shopid):
        skey = BrandIndex.brandshop.format(self.date, brand)
        p = conn if self.pipeline is None else self.pipeline
        p.sadd(skey, shopid) 

    def incrinfo(self, brand, cate1, cate2, brandinfo):
        # incr brandinfo
        hkey = BrandIndex.brandinfo.format(self.date, brand, cate1, cate2)
        p = conn if self.pipeline is None else self.pipeline
        c12 = self.make_skey(cate1, cate2)
        for field, value in brandinfo.iteritems():
            p.hincrbyfloat(hkey, field, value, skey=c12)

        # add brands
        skey = BrandIndex.brands.format(self.date)
        p.sadd(skey, brand) # will be converted to utf-8 if it is unicode

        # brand sales, aka indexes
        sales = brandinfo.get('sales') 
        if sales:
            zkey = BrandIndex.brandsales.format(self.date, cate1, cate2)
            CappedSortedSet(zkey, 1000, p, skey=c12).zadd(brand, sales)

    def addcates(self, brand, cate1, cate2):
        skey = BrandIndex.brandcates.format(self.date, brand)
        p = conn if self.pipeline is None else self.pipeline
        p.sadd(skey, pack((cate1, cate2)))

    def addtops(self, brand, cate1, itemid, shopid, sales):
        p = conn if self.pipeline is None else self.pipeline
        zkey1 = BrandIndex.brandtopitems.format(self.date, brand, cate1)
        zkey2 = BrandIndex.brandtopshops.format(self.date, brand, cate1)
        CappedSortedSet(zkey1, 10, p, skey=zkey1).zadd(itemid, sales)
        CappedSortedSet(zkey2, 10, p, skey=zkey2).zadd(shopid, sales)

class CategoryIndex(object):
    categoryinfo = 'categoryinfo_{}_{}_{}_{}' # (date, cate1, cate2, monorday); hash for info
                                              # sales, deals, delta_sales, num_of_items, *search_index*

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
        patterns = ['categoryinfo_{}*'.format(date),
                    ]
        for pattern in patterns:
            p = conn.pipeline()
            for key in conn.keys(pattern):
                p.delete(key)
            p.execute()


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
