#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" A simplified and thin set/hash for redis

A "real set/hash" in redis has too much overhead (~10x)

This is a simplified version of set/hash, 
    * only integer/biginteger values supported
    * for set, only ``contains``, ``add`` and  ``delete`` is supported

By doing this simplification, we are able to take advantage of ``redis``'s 
zipentry optimization. Thus the size of set/hash can be reduced to
1/4 ~ 1/3 of the original size.

The concept comes from `this stackoverflow question 
<http://stackoverflow.com/questions/10004565/redis-10x-more-memory-usage-than-data/10008222#10008222>`_
"""
import redis
import gevent.coros

class ThinSet(object):
    def __init__(self, name, totalcount, connection=None):
        self.name = name
        self.total = totalcount
        self.modulo = totalcount//400
        self.counterkey = 'thinset_{}_count'.format(name)
        self.bucketskey = 'thinset_{}_buckets'.format(name)
        if connection is not None:
            self.conn = connection
        else:
            self.conn = redis.Redis()

    def _get_bucket(self, item):
        return 'thinset_{}_{}'.format(self.name, int(item) % self.modulo)


    def count(self):
        r = self.conn.get(self.counterkey)
        return 0 if r is None else int(r)


    def add(self, *items):
        if len(items) == 0:
            return
           
        p = self.conn.pipeline(transaction=False)

        buckets = set()
        for item in items:
            bucket = self._get_bucket(item)
            buckets.add(bucket)
            p.sadd(bucket, item)

        added = sum(p.execute())

        self.conn.incr(self.counterkey, added)
        self.conn.sadd(self.bucketskey, *list(buckets))
    

    def delete(self, *items):
        if len(items) == 0:
            return
            
        p = self.conn.pipeline(transaction=False) 

        for item in items: 
            bucket = self._get_bucket(item)
            p.srem(bucket, item)

        deleted = sum(p.execute())

        if deleted:
            self.conn.decr(self.counterkey, deleted)


    def contains(self, *items):
        """ order preserving contains, works only for shardredis """
        if not items:
            return []

        p = self.conn.pipeline(transaction=False)
    
        pointers = {}
        for i, item in enumerate(items):
            bucket = self._get_bucket(item)
            index = self.conn.ring.get_node(bucket)
            if index not in pointers:
                pointers[index] = []
            pointers[index].append(i)
            p.sismember(bucket, item)

        orders = []
        for index in range(len(self.conn.conns)):
            if index in pointers:
                orders.extend(pointers[index])
                
        values = p.execute()
        _, values = zip(*sorted(zip(orders, values)))
        return values

    def smembers(self):
        buckets = self.conn.smembers(self.bucketskey)

        p = self.conn.pipeline(transaction=False)
        for bucket in buckets:
            p.smembers(bucket)
        r = set()
        for s in p.execute():
            r.update(s)

        return r

class ThinHash(object):
    def __init__(self, name, totalcount, connection=None):
        self.name = name
        self.counterkey = 'thinhash_{}_count'.format(name)
        self.bucketskey = 'thinhash_{}_buckets'.format(name)
        self.total = totalcount
        self.modulo = totalcount//400
        if connection is not None:
            self.conn = connection
        else:
            self.conn = redis.Redis()

    def _get_bucket(self, field):
        return 'thinhash_{}_{}'.format(self.name, int(field) % self.modulo)

    def count(self):
        r = self.conn.get(self.counterkey)
        return 0 if r is None else int(r)

    def hset(self, field, value):
        bucket = self._get_bucket(field)
        p = self.conn.pipeline(transaction=False)
        p.hset(bucket, field, value) 
        p.sadd(self.bucketskey, bucket)
        r = p.execute()
        if r[0]:
            self.conn.incr(self.counterkey, r[0])

    def hdel(self, field):
        bucket = self._get_bucket(field)
        deleted = self.conn.hdel(bucket, field) 
        if deleted:
            self.conn.decr(self.counterkey, deleted)
       
    def hmset(self, *args):
        if len(args) == 0:
            return
        elif len(args) % 2 != 0:
            raise ValueError("hmset only accept even arguments")

        p = self.conn.pipeline(transaction=False)
        buckets = set()
        for i in range(len(args)/2):
            field, value = args[i*2], args[i*2+1]
            bucket = self._get_bucket(field)
            buckets.add(bucket)
            p.hset(bucket, field, value)

        added = sum(p.execute())
        self.conn.incr(self.counterkey, added)
        self.conn.sadd(self.bucketskey, *buckets)

    def hmget(self, *fields):
        """ order preserving hmget, works only for shardredis """
        if len(fields) == 0:
            return

        pointers = {}
        p = self.conn.pipeline(transaction=False)
        for i, field in enumerate(fields):
            bucket = self._get_bucket(field)
            index = self.conn.ring.get_node(bucket)
            if index not in pointers:
                pointers[index] = []
            pointers[index].append(i)
            p.hget(bucket, int(field))
        orders = []
        for index in range(len(self.conn.conns)):
            if index in pointers:
                orders.extend(pointers[index])
                
        values = p.execute()
        _, values = zip(*sorted(zip(orders, values)))
        return values

    def hgetall(self):
        buckets = self.conn.smembers(self.bucketskey)
        p = self.conn.pipeline(transaction=False)
        for bucket in buckets:
            p.hgetall(bucket)
        r = {}
        for d in p.execute():
            r.update(d)
        return r
