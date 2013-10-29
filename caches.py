#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import binascii
import traceback

from thinredis import ThinSet, ThinHash 
from shardredis import ShardRedis
from settings import CACHE_URIS

conns = []
for uri in CACHE_URIS:
    host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(uri).groups()
    conn = redis.Redis(host=host, port=int(port), db=int(db))
    conns.append(conn)
conn = ShardRedis(conns=conns)

WC = ThinSet('ataobao-wrongcategory-items', 3000*10000, connection=conn)
IF = ThinSet('ataobao-infrequent-items', 15000*10000, connection=conn)

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
    def gethash(type):
        hashkey = LC.hashkey.format(type)
        if type == 'item':
            count = 2*10000*10000
        else:
            count = 500*10000
        return ThinHash(hashkey, count, connection=conn)

    @staticmethod
    def count(type):
        return LC.gethash(type).count()

    @staticmethod
    def delete(type, id):
        return LC.gethash(type).hdel(id)

    @staticmethod
    def need_update(type, *ids):
        if not ids:
            return []
        ids = list(set(ids))
        ids = [ ids[i] for i, wc in enumerate(WC.contains(*ids)) if not wc ]

        if not ids:
            return []

        thehash = LC.gethash(type)
        tsnow = time.mktime(time.gmtime())
        lastchecks = thehash.hmget(*ids)

        offset = 80000 if type == 'item' else 86400*7
        offsets = [offset] * len(ids)
        if type == 'item':
            contains = IF.contains(*ids)
            offsets = map(lambda o, c: o*7 if c else o, offsets, contains)

        needs = []
        for i, lastcheck in enumerate(lastchecks): 
            # if there's no lastcheck, or lastcheck happened some time ago
            # try call on_update with id, if succeeded, update lastcheck in redis
            if lastcheck is None or float(lastcheck) + offsets[i] < tsnow:
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
                LC.gethash(type).hset(id, tsnow)
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
    def ct():
        return int(time.mktime(time.gmtime())%86400/60+480)

    @staticmethod
    def getset(setkey):
        return ThinSet(setkey, 20*10000, connection=conn)

    @staticmethod
    def checktime(id):
        """ checktime, an integer indicates the minute of day the item should be checked """
        # we distribute it randomly in beteen 5th-1435th minute of day
        return binascii.crc32(id)%1430+5 if not isinstance(id, int) else id%1430+5

    @staticmethod
    def add_items(*ids):
        for id in ids:
            setkey = '{basekey}-{ct}'.format(basekey=ItemCT.basekey, ct=ItemCT.checktime(id))
            ItemCT.getset(setkey).add(id)

    @staticmethod
    def delete(*ids):
        for id in ids:
            setkey = '{basekey}-{ct}'.format(basekey=ItemCT.basekey, ct=ItemCT.checktime(id))
            ItemCT.getset(setkey).delete(id)

    @staticmethod
    def get_items(ct=None):
        if ct is None:
            ct = ItemCT.ct()
         
        setkey = '{basekey}-{ct}'.format(basekey=ItemCT.basekey, ct=ct)
        return ItemCT.getset(setkey).smembers()
