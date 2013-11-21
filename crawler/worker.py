#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" All workers defined here

A worker typically "watches" a queue, and do jobs accordingly

Currently there're two workers:
    ItemWorker: update item info
    ShopWorker: update shop info
"""
from gevent import monkey; monkey.patch_all()

import time
import traceback
import gevent.pool
from functools import partial
from collections import deque

from models import db, update_item, delete_item, update_shop
from caches import LC, ItemCT, WC
from queues import poll, ai1, ai2, as1, af1, asi1
from crawler.cates import need_crawl
from crawler.tbitem import get_item
from crawler.tbshop import list_shop
from crawler.tbshopinfo import get_shop

def call_with_throttling(func, args=(), kwargs={}, threshold_per_minute=600):
    """ calling a func with throttling
    
    Throttling the function call with ``threshold_per_minute`` calls per minute. This is useful 
    in case where the func calls a remote service having their throttling policy. We must honor 
    their throttling, otherwise we will be banned shortly.

    :param func: the function to be called
    :param args: args of that function
    :param kwargs: kwargs of that function
    :param threshold_per_minute: defines how many calls can be made to the function per minute 
    """
    if not hasattr(call_with_throttling, 'logs'):
        call_with_throttling.logs = deque()
        call_with_throttling.started_at = time.time()
        call_with_throttling.count = 0
    logs = call_with_throttling.logs
    started_at = call_with_throttling.started_at
    call_with_throttling.count += 1
    count = call_with_throttling.count

    def remove_outdated():
        # remove outdated from logs
        t = time.time()
        while True:
            if logs and logs[0] < t - 60:
                logs.popleft()
            else:
                break

    def wait_for_threshold():
        while len(logs) > threshold_per_minute:
            remove_outdated()
            time.sleep(0.3)

    def smoothen_calling_interval():
        average_processing_time = (time.time() - started_at) / count
        expected_processing_time = 60. / threshold_per_minute
        if expected_processing_time > average_processing_time:
            time.sleep((len(logs)+0.8)*expected_processing_time - len(logs)*average_processing_time)
    
        
    average_processing_time = (time.time() - started_at) / count
    expected_processing_time = 60. / threshold_per_minute
    #print expected_processing_time, average_processing_time, count, time.time()-started_at

    if logs and len(logs) < threshold_per_minute:
        smoothen_calling_interval()
    else:
        wait_for_threshold()

    logs.append(time.time())

    return func(*args, **kwargs)

class Worker(object):
    """ General Worker """
    def __init__(self, poolsize=100):
        self.pool = gevent.pool.Pool(poolsize)

    def work(self):
        raise NotImplementedError('this method should be implemented by subclasses')

class ReQueueWorker(Worker):
    """ ReQueue Timeouted Jobs """
    def work(self):
        gevent.joinall([gevent.spawn(queue.background_cleaning) for queue in [ai1, ai2, as1, af1, asi1]])

class ItemWorker(Worker): 
    """ Work on Item Queues

    1. poll item ids from [ai1, ai2]
    2. check update, if yes, go on
    3. update item info, update daily summary 
    4. put shopid into queue if needed

    implement throttling
    """
    def __init__(self, poolsize=100):
        self.pool = gevent.pool.Pool(poolsize+1)
        self.banned = False
        self.pool.spawn(self.check_ban)

    def check_ban(self):
        while True:
            try:
                #self.banned = is_banned()
                pass
            except:
                traceback.print_exc()
            time.sleep(10)


    def work(self):
        def on_update(itemid):
            print('updating item id: {}'.format(itemid))
            d = call_with_throttling(get_item, args=(itemid,), threshold_per_minute=3000)
            if 'error' in d:
                if d['error'] in ['not found']:
                    try:
                        print('deleting id: {}'.format(itemid))
                        LC.delete('item', itemid)
                        ItemCT.delete(itemid)
                        delete_item(itemid)
                        ai1.task_done(itemid)
                        ai2.task_done(itemid)
                    except:
                        traceback.print_exc()
                    return d
                else:
                    raise ValueError('unknown error: {}'.format(d))

            # check if we should save this item in the first place
            # we only accept a few cates
            if 'cid' in d and not need_crawl(d['cid']):
                WC.add(d['id'])
                return d

            # for connection errors, we simply raise exception here
            # the exceptions will be captured in LC.update_if_needed
            # the task will not clean up and will be requeued by requeue worker
            if not d:
                raise ValueError('item incomplete error: {}'.format(d))
            elif d and 'shopid' in d:
                try:
                    update_item(d)
                except:
                    traceback.print_exc()
                    raise ValueError('item update failed: {}'.format(d))

                if LC.need_update('shop', d['shopid']):
                    # queue shop jobs
                    as1.put(d['shopid'])
                    
            return d
            
        while True:
            try:
                while self.banned:
                    print('banned, sleeping 60 secs')
                    time.sleep(60)
                    for attr in ['count', 'started_at', 'logs']:
                        if hasattr(call_with_throttling, attr):
                            delattr(call_with_throttling, attr)
                result = poll([ai1, ai2], timeout=10)
                if result:
                    queue, itemid = result
                    self.pool.spawn(LC.update_if_needed, 'item', int(itemid), on_update, queue)
            except:
                traceback.print_exc()

class ShopWorker(Worker):
    """ Work on Shop Queues

    1. poll item ids from [as1]
    2. check update, if yes, go on
    3. listing items in shop, update ItemCT info
    """
    def work(self):
        shopid = None

        def on_update(ids):
            ItemCT.add_items(*ids)
            ai2.put(*ids)

        def spawn_shop(shopid):
            print('updating shop-item of shop {}'.format(shopid))
            asi1.put(shopid)
            self.pool.spawn(list_shop, shopid, on_update)
            
        while True:
            try:
                result = poll([as1], timeout=10)
                if result:
                    queue, shopid = result
                    LC.update_if_needed('shop', shopid, spawn_shop, queue)
            except:
                traceback.print_exc()

class ShopInfoWorker(Worker):
    """ Work on ShopInfo Queues """
    def work(self):
        def on_update(id):
            print('updating shopinfo of shopid {}'.format(id))
            si = get_shop(id)
            if si and 'error' not in si:
                update_shop(si)

        while True:
            try:
                result = poll([asi1], timeout=10)
                if result:
                    queue, shopid = result
                    self.pool.spawn(LC.update_if_needed, 'shopinfo', int(shopid), on_update, asi1)
            except:
                traceback.print_exc()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Worker with arguments')
    parser.add_argument('--worker', '-w', choices=['item', 'shop', 'shopinfo', 'requeue'], help='worker type, can be "item", "shop", or "requeue"', required=True)
    parser.add_argument('--poolsize', '-p', type=int, default=100, help='gevent pool size for worker (default: %(default)s)')
    option = parser.parse_args()
    if option.worker == "item":
        worker = ItemWorker(option.poolsize)
        #worker.banned = is_banned()
        worker.work()
    elif option.worker == "shop":
        ShopWorker(option.poolsize).work()
    elif option.worker == "shopinfo":
        ShopInfoWorker(option.poolsize).work()
    elif option.worker == "requeue":
        ReQueueWorker().work()

def test_throttling():
    def printget():
        print time.time(), 'id' in get_item(22183623058) 
        
    import gevent.pool
    pool = gevent.pool.Pool(20)
    while True:
        pool.spawn(call_with_throttling, printget, threshold_per_minute=600) 
    pool.join()

if __name__ == '__main__':
    main()
    #test_throttling()
