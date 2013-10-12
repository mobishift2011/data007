#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import binascii
import traceback

from msgpack import unpackb as unpack, packb as pack

from settings import QUEUE_URI

host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(QUEUE_URI).groups()
conn = redis.Redis(host=host, port=int(port), db=int(db))
    
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
    def need_update(type, *ids):
        if len(ids) == 0:
            return []
        elif len(ids) == 1:
            ids = list(ids)
	    ids.append(ids[0])
        hashkey = LC.hashkey.format(type)
        tsnow = time.mktime(time.gmtime())
        lastchecks = conn.hmget(hashkey, *ids)

        offset = 80000 if type == 'item' else 86400*7

        needs = []
        for i, lastcheck in enumerate(lastchecks): 
            # if there's no lastcheck, or lastcheck happened some time ago
            # try call on_update with id, if succeeded, update lastcheck in redis
            if lastcheck is None or unpack(lastcheck) + offset < tsnow:
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

class ShopItem(object):
    """ Shop-Item Relation Management 

    one-to-many shop-item relation hashes

        - key -> shop
        - value -> a set of item ids in the shop

    Typical Usage::

    >>> ShopItem.add_items(100, 1,2,3,4,5)
    >>> ShopItem.get_items(100)
    set([1, 2, 3, 4, 5])
    """
    basekey = 'ataobao-shop-item-set'

    @staticmethod
    def add_items(shopid, *itemids):
        setkey = '{basekey}-{shopid}'.format(basekey=ShopItem.basekey, shopid=shopid)
        if itemids:
            conn.sadd(setkey, *[pack(id) for id in itemids]) 

    @staticmethod
    def get_items(shopid):
        setkey = '{basekey}-{shopid}'.format(basekey=ShopItem.basekey, shopid=shopid)
        for m in conn.smembers(setkey):
            yield unpack(m)
