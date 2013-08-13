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
    """ Item LastCheck Management """
    hashkey = 'ataobao-{}-lastcheck-hash'

    @staticmethod
    def need_update(type, id):
        hashkey = LC.hashkey.format(type)
        tsnow = time.mktime(time.gmtime())
        lastcheck = conn.hget(hashkey, id)

        offset = 43200 if type == 'item' else 86400

        # if there's no lastcheck, or lastcheck happened an hour ago
        # try call on_update with id, if succeeded, update lastcheck in redis
        if lastcheck is None or unpack(lastcheck) + offset < tsnow:
            return True
        else:
            return False

    @staticmethod
    def update_if_needed(type, id, on_update):
        """ try update item by id, update lastcheck if needed """
        hashkey = LC.hashkey.format(type)
        tsnow = time.mktime(time.gmtime())
        if LC.need_update(type, id):
            try:
                conn.hset(hashkey, id, pack(tsnow))
                on_update(id)
            except:
                traceback.print_exc()

class ItemCT(object):
    """ Item CheckTime Management """
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
    def get_items(self, ct=None):
        if ct is None:
            ct = int(time.mktime(time.gmtime())/86400/60)
         
        setkey = '{basekey}-{ct}'.format(basekey=ItemCT.basekey, ct=ct)
        for m in conn.smembers(setkey):
            yield unpack(m)

class ShopItem(object):
    """ Shop-Item Relation Management """
    basekey = 'ataobao-shop-item-set'

    @staticmethod
    def add_items(shopid, *itemids):
        setkey = '{basekey}-{shopid}'.format(basekey=ShopItem.basekey, shopid=shopid)
        conn.sadd(setkey, *[pack(id) for id in itemids]) 

    @staticmethod
    def get_items(shopid):
        setkey = '{basekey}-{shopid}'.format(basekey=ShopItem.basekey, shopid=shopid)
        for m in conn.smembers(setkey):
            yield unpack(m)
