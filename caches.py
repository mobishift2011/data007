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
import debouncing

conns = []
for uri in CACHE_URIS:
    host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(uri).groups()
    conn = redis.Redis(host=host, port=int(port), db=int(db))
    conns.append(conn)
conn = ShardRedis(conns=conns)

WC = ThinSet('ataobao-wrongcategory-items', 3000*10000, connection=conn)
IF = ThinSet('ataobao-infrequent-items', 15000*10000, connection=conn)


from settings import RECORD_URI

host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(RECORD_URI).groups()
conn_record = redis.Redis(host=host, port=int(port), db=int(db))

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
        elif type == 'shop':
            count = 500*10000
        elif type == 'shopinfo':
            count = 500*10000
        else:
            raise ValueError('wrong LC type: {}'.format(type))
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

        if type == 'item':
            ids = [ ids[i] for i, wc in enumerate(WC.contains(*ids)) if not wc ]
            if not ids:
                return []

        thehash = LC.gethash(type)
        tsnow = time.mktime(time.gmtime())
        if len(ids) == 1:
            lastchecks = [thehash.hget(ids[0])]
        else:
            lastchecks = thehash.hmget(*ids)

        needs = []
        for i, lastcheck in enumerate(lastchecks): 
            # if there's no lastcheck, or lastcheck happened some time ago
            # try call on_update with id, if succeeded, update lastcheck in redis
            if type == 'item':
                if lastcheck:
                    if str(lastcheck).find('.') > 0:
                        lastcheck = float(lastcheck)
                    print "get:", bin(int(lastcheck)), len(bin(int(lastcheck))) - 2
                if debouncing.can_update(lastcheck):
                    needs.append(ids[i])
            else:
                if lastcheck is None or float(lastcheck) + 86400*7 < tsnow:
                    needs.append(ids[i])
        return needs

    @staticmethod
    def update_if_needed(type, id, on_update, queue):
        """ try update item by id, update lastcheck if needed """
        hashkey = LC.hashkey.format(type)
        tsnow = time.mktime(time.gmtime())
        
        today_key = time.strftime("%Y-%m-%d", time.gmtime())
        
        if LC.need_update(type, int(id)):
            info = None
            conn_record.hincrby(today_key, '{}:crawl-sum'.format(type))
            try:
                info = on_update(id)
            except:
                conn_record.hincrby(today_key, '{}:crawl-err-except'.format(type))
                print('we do not set task_done for id {}, so we will pick them up in requeue'.format(id))
                traceback.print_exc()
            else:
                conn_record.hincrby(today_key, '{}:crawl-return'.format(type))
                
                queue.task_done(id)
                if type == "item":
                    if not info or not info.has_key('num_sold30'):
                        conn_record.hincrby(today_key, '{}:crawl-data-err'.format(type))
                        print "item err:", info
                        return
                    conn_record.hincrby(today_key, '{}:crawl-success'.format(type))
                    
                    ret_bin = LC.gethash(type).hget(id)
                    new_bin = debouncing.get_update_bin(ret_bin, info)
                    print "update:", bin(new_bin), len(bin(new_bin))
                    LC.gethash(type).hset(id, new_bin)
                else:
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
    cache = {}
    @staticmethod
    def ct():
        return int(time.mktime(time.gmtime())%86400/60+480)

    @staticmethod
    def getset(setkey):
        cache = ItemCT.cache
        if setkey not in cache:
            cache[setkey] = ThinSet(setkey, 20*10000, connection=conn)
        return cache[setkey]

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
