#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import binascii
import traceback

from msgpack import unpackb as unpack, packb as pack

from settings import CACHE_URI

host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(CACHE_URI).groups()
conn = redis.Redis(host=host, port=int(port), db=int(db))

class ShopInfo(object):
    """ some datastructures store shop info

    1. zkey, a sorted set for shopids 
    2. hkey, a hashtable saves the (num_sold30, last aggregate time)
    """
    zkey = 'ataobao-shopinfo-shopids'
    hkey = 'ataobao-shopinfo-shophash'
    @staticmethod
    def count():
        return conn.zcard(ShopInfo.zkey)
    
    @staticmethod
    def add_shop(*ids):
        args = [id for ziped in zip(ids, ids) for id in ziped]
        conn.zadd(ShopInfo.zkey, *args)

    @staticmethod
    def need_aggregate(*shopids):
        if not shopids:
            return []
        needs = []
        for i, x in enumerate(conn.hmget(ShopInfo.hkey, *shopids)):
            if not x:
                needs.append(shopids[i])
            else:
                month_sales, lastcheck = unpack(x)
                tsnow = time.mktime(time.gmtime())
                if month_sales > 0 and lastcheck < tsnow - 80000:
                    needs.append(shopids[i])
                elif lastcheck < tsnow - 800000:
                    needs.append(shopids[i])
        return needs

    @staticmethod
    def aggregate_if_needed(shopid, on_aggregate, queue):
        if ShopInfo.need_aggregate(shopid):
            try:
                month_sales = on_aggregate(shopid)
            except:
                print('we do not set task_done for id {}, so we will pick them up in requeue'.format(shopid))
                traceback.print_exc()
            else:
                lastcheck = time.mktime(time.gmtime())
                conn.hset(ShopInfo.hkey, shopid, pack([month_sales, lastcheck]))
                queue.task_done(shopid)
        else:
            queue.task_done(shopid)
         
    @staticmethod
    def get_range(start, stop):
        return [int(id) for id in conn.zrange(ShopInfo.zkey, start, stop)]

class IF(object):
    """ infrequent items 

    save ids for num_sold30 == 0, to distinguish from everyday fetchs
    ids belong to IF would trigger crawler less frequently (7days/run)
    """
    setkey = 'ataobao-infrequent-items' 
    @staticmethod
    def count():
        return conn.scard(IF.setkey) 

    @staticmethod
    def contains(*ids):
        p = conn.pipeline()
        for id in ids:
            p.sismember(IF.setkey, id)
        result = p.execute()
        return result

    @staticmethod
    def delete(*ids):
        conn.srem(IF.setkey, *ids)

    @staticmethod
    def add(*ids):
        conn.sadd(IF.setkey, *ids)
    
class LC(object):
    """ Item LastCheck Management 

    This is a huge hash table maps:
        
        - field -> item id/ shop id
        - value -> last time checked

    We can test if an item is not updated for a while and thus needs update
    
    >>> if LC.need_update('item', 12345):
    ...     print('item {} need update'.format(12345))

    if we really want to do update, we'd better call ``update_if_needed``
   
    >>> def on_update(id):
    ...     print('updating item {}'.format(id)) 
    >>>
    >>> result = queue.get()
    >>> if result:
    ...     queue, itemid = result
    ...     LC.update_if_needed('item', itemid, on_update, queue)

    This will ensure we do cleanups after we done the task
    """
    hashkey = 'ataobao-{}-lastcheck-hash'

    @staticmethod
    def count(type):
        hashkey = LC.hashkey.format(type)
        return conn.hlen(hashkey) 

    @staticmethod
    def delete(type, id):
        hashkey = LC.hashkey.format(type)
        return conn.hdel(hashkey, id)

    @staticmethod
    def need_update(type, *ids):
        if not ids:
            return []
	    ids.append(ids[0])
        hashkey = LC.hashkey.format(type)
        tsnow = time.mktime(time.gmtime())
        lastchecks = conn.hmget(hashkey, *ids)

        offset = 80000 if type == 'item' else 86400*7
        offsets = [offset] * len(ids)
        if type == 'item':
            contains = IF.contains(*ids)
            offsets = map(lambda o, c: o*7 if c else o, offsets, contains)

        needs = []
        for i, lastcheck in enumerate(lastchecks): 
            # if there's no lastcheck, or lastcheck happened some time ago
            # try call on_update with id, if succeeded, update lastcheck in redis
            if lastcheck is None or unpack(lastcheck) + offsets[i] < tsnow:
                needs.append(ids[i])

        return needs

    @staticmethod
    def update_if_needed(type, id, on_update, queue):
        """ try update item by id, update lastcheck if needed """
        hashkey = LC.hashkey.format(type)
        tsnow = time.mktime(time.gmtime())
        if LC.need_update(type, id):
            try:
                on_update(id)
            except:
                print('we do not set task_done for id {}, so we will pick them up in requeue'.format(id))
                traceback.print_exc()
            else:
                queue.task_done(id)
                conn.hset(hashkey, id, pack(tsnow))
        else:
            queue.task_done(id)

class ItemCT(object):
    """ Item CheckTime Management 
    
    this cache abstraction is used for daily item update
    We divide a day by 1400+ minutes, for each minute we create a set in redis,
    holding the items to be updated in that minute
    
    for each item we see, we calculate the minute bracket it belongs to by calling 
    ``checktime``, then added the item id into that bracket(set)

    for example, as soon as we see item 1, 2, 3, 4, and 5, we should::

    >>> ItemCT.add_items(1, 2, 3, 4, 5)

    ``item scheduler`` will use ``ItemCT.get_items`` methods to retrieve items to update
    """
    basekey = 'ataobao-item-checktime-set'

    @staticmethod
    def checktime(id):
        """ checktime, an integer indicates the minute of day the item should be checked """
        # we distribute it randomly in beteen 5th-1435th minute of day
        return binascii.crc32(id)%1430+5 if not isinstance(id, int) else id%1430+5

    @staticmethod
    def add_items(*ids):
        pipeline = conn.pipeline()
        for id in ids:
            setkey = '{basekey}-{ct}'.format(basekey=ItemCT.basekey, ct=ItemCT.checktime(id))
            pipeline.sadd(setkey, pack(id))
        pipeline.execute()

    @staticmethod
    def get_items(ct=None):
        if ct is None:
            ct = int(time.mktime(time.gmtime())%86400/60)
         
        setkey = '{basekey}-{ct}'.format(basekey=ItemCT.basekey, ct=ct)
        return [unpack(m) for m in conn.smembers(setkey)]
