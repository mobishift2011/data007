#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import redis
import random
from msgpack import packb as pack
    
from thinredis import ThinSet, ThinHash
from shardredis import ShardRedis

conn = redis.Redis()
conn = ShardRedis([
            redis.Redis(db=1),
            redis.Redis(db=2),
            redis.Redis(db=3),
            redis.Redis(db=4),
            #redis.Redis(port=6401),
            #redis.Redis(port=6402),
            #redis.Redis(port=6403),
            #redis.Redis(port=6404),
        ])

def randid(binary=False):
    id = random.randint(2**34, 2**35)
    if binary:
        return pack(id)
    else:
        return id

def randts(binary=True):
    if binary:
        return pack(time.mktime(time.gmtime()))
    else:
        return time.mktime(time.gmtime())

def check_setsize(binary=False, count=10000):
    setkey = 'testset'
    conn.flushall()
    p = conn.pipeline()
    for _ in xrange(0, count):
        p.sadd(setkey, randid(binary=binary))
    p.execute()
    print('it takes {} for {} {} sets'.format(conn.info()['used_memory_human'], conn.scard(setkey), 'binary' if binary else 'integer'))
    
def check_hashsize(binary=False, count=10000):
    hashkey = 'testhash' 
    conn.flushall()
    p = conn.pipeline()
    for _ in xrange(0, count):
        p.hset(hashkey, randid(binary=binary), randts())
    p.execute()
    print('it takes {} for {} {} hashs'.format(conn.info()['used_memory_human'], conn.hlen(hashkey), 'binary' if binary else 'integer'))

def check_thinsetsize(count=10000):
    thinsetkey = 'testthinset'
    conn.flushall()
    s = ThinSet(thinsetkey, count, connection=conn)
    s.add(*[randid() for _ in xrange(0, count)])
    print('it takes {} for {} thinsets'.format(conn.info()['used_memory_human'], s.count()))

def check_thinhashsize(count=10000):
    thinhashkey = 'testthinhash'
    conn.flushall()
    h = ThinHash(thinhashkey, count, connection=conn)
    args = []
    for _ in xrange(count):
        args.append(randid())
        args.append(randts())
    h.hmset(*args)
    print('it takes {} for {} thinhashs'.format(conn.info()['used_memory_human'], h.count()))
    

if __name__ == '__main__':
    import time
    t1 = time.time()
    check_thinsetsize(100000)
    t2 = time.time()
    check_setsize(False, 100000)
    t3 = time.time()
    print t2-t1, t3-t2
    check_thinhashsize(100000)
    t4 = time.time()
    check_hashsize(False, 100000)
    t5 = time.time()
    print t4-t3, t5-t4

    exit(0)
    for binary in [False, True]:
        check_setsize(binary, 100000)
        check_hashsize(binary, 100000)
