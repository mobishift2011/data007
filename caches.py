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
        #ids = [ ids[i] for i, wc in enumerate(WC.contains(*ids)) if not wc ]
        
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
            
            if type == 'item':
                #cfz
                if lastcheck is None:
                    needs.append(ids[i])
                else:
                    
                    if str(lastcheck).find('.') > 0:
                        lastcheck = int(float(lastcheck))
                        lastcheck = lastcheck << 28 
                    else:
                        lastcheck = int(lastcheck)
                        
                    offset = 0
                    if len(str(lastcheck)) == 10:# 兼容原来的
                        lastcheck = lastcheck
                    else:
                        offset = lastcheck & 0xf
                        lastcheck = lastcheck >> 28
                    
                    #print lastcheck, offset, "=========="
                    
                    if offset == 0:
                        offset = offsets[i]
                    else:
                        offset = offset * 86400
                    
                    #needs.append(ids[i])
                    if lastcheck + offset < int(tsnow):
                        needs.append(ids[i])
            else:
                if lastcheck is None or float(lastcheck) + offsets[i] < tsnow:
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
                    
                    src = LC.gethash(type).hmget(*[id])
                    if src[0]:
                        '''
                                                                                    共用59位
                            31(ts), 24(num_sold30), 4(offset)
                        '''
                        
                        if str(src[0]).find('.') > 0:
                            src = int(float(src[0]))
                            src = src << 28 
                        else:
                            src = int(src[0])
                        
                        info['num_sold30'] += 5
                        #print "src", bin(src)
                            
                        num_sold30 = (src >> 4) & 0xffffff
                        offset = src & 0xf
                        ts = src >> 28
                        
                        sold0, sold1 = map(int, [num_sold30, info['num_sold30']])
                        
                        if sold0 == sold1:
                            if offset == 0:
                                offset = 1
                            elif offset == 1:
                                offset = 2
                            elif offset == 2:
                                offset = 4
                            elif offset == 4:
                                offset = 8
                            elif offset == 8:
                                offset = 15
                        else:
                            offset = 0
                        new_deb = (int(tsnow) << 28) + (sold1 << 4) + offset
                        print "update"
                    else:
                        new_deb = (int(tsnow) << 28) + (int(info['num_sold30']) << 4 )
                        print "new"
                        
                    print "save:", bin(new_deb)
                    LC.gethash(type).hset(id, new_deb)
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
