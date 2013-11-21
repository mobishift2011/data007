#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey; monkey.patch_all()
from crawler.tbitem import get_item
import time
import gevent
import gevent.pool
pool = gevent.pool.Pool(20)

itemid = 35515810124

def warmup():
    print 'warmup'
    get_item(itemid)
    print 'warmed'

count = 0
def bench(itemid):
    global count
    get_item(itemid)
    count += 1

def printstats():
    global count
    while True:
        t0, c0 = time.time(), count
        time.sleep(1)
        print '{} items crawled in {}s'.format(count-c0, time.time()-t0)
        
def benchmark():
    gevent.spawn(printstats)
    for _ in xrange(1000):
        pool.spawn(bench, itemid) 
    pool.join()

if __name__ == '__main__':
    warmup()
    benchmark()
