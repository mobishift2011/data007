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

from models import db, update_item, update_shop
from caches import LC, ItemCT, ShopItem
from queues import poll, ai1, ai2, as1, af1
from crawler.tbitem import get_item, is_valid_item, is_banned
from crawler.tbshop import list_shop
from crawler.tbshopinfo2 import get_shop

def call_with_throttling(func, args=(), kwargs={}, threshold_per_minute=60):
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
    logs = call_with_throttling.logs

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
        average_processing_time = (time.time() - logs[0]) / len(logs)
        expected_processing_time = 60. / threshold_per_minute
        if expected_processing_time > average_processing_time:
            time.sleep((len(logs)+0.8)*expected_processing_time - len(logs)*average_processing_time)
    
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
        gevent.joinall([gevent.spawn(queue.background_cleaning) for queue in [ai1, ai2, as1, af1]])

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
            time.sleep(10)
            try:
                self.banned = is_banned()
            except:
                traceback.print_exc()

    def work(self):
        def on_update(itemid):
            print('updating item id: {}'.format(itemid))
            d = call_with_throttling(get_item, args=(itemid,), threshold_per_minute=600)
            #d = get_item(itemid)
            if 'notfound' in d or 'error' in d:
                LC.delete('item', itemid)
                return

            # for connection errors, we simply raise exception here
            # the exceptions will be captured in LC.update_if_needed
            # the task will not clean up and will be requeued by requeue worker
            if d == {} or 'num_instock' not in d or 'num_sold30' not in d:
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

        while True:
            if self.banned:
                print('banned, sleeping 60 secs')
                time.sleep(60)
            result = poll([ai1, ai2], timeout=10)
            if result:
                queue, itemid = result
                self.pool.spawn(LC.update_if_needed, 'item', itemid, on_update, queue)

class ShopWorker(Worker):
    """ Work on Shop Queues

    1. poll item ids from [as1]
    2. check update, if yes, go on
    3. listing items in shop, update ItemCT and ShopItem info
    """
    def work(self):
        shopid = None

        def on_update(ids):
            ShopItem.add_items(shopid, *ids)
            ItemCT.add_items(*ids)
            ai2.put(*ids)

        def update_shopinfo(id):
            try:
                si = get_shop(id)
                update_shop(si)
            except Exception as e:
                traceback.print_exc()

        def spawn_shop(shopid):
            print('updating shop-item of shop {}'.format(shopid))
            self.pool.spawn(update_shopinfo, shopid)
            self.pool.spawn(list_shop, shopid, on_update)
            
        while True:
            result = poll([as1], timeout=10)
            if result:
                queue, shopid = result
                LC.update_if_needed('shop', shopid, spawn_shop, queue)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Worker with arguments')
    parser.add_argument('--worker', '-w', choices=['item', 'shop', 'requeue'], help='worker type, can be "item", "shop", or "requeue"', required=True)
    parser.add_argument('--poolsize', '-p', type=int, default=100, help='gevent pool size for worker (default: %(default)s)')
    option = parser.parse_args()
    {
        "item": ItemWorker(option.poolsize),
        "shop": ShopWorker(option.poolsize),
        "requeue": ReQueueWorker(),
    }.get(option.worker).work()


def test_throttling():
    def printget():
        print time.time(), get_item(22183623058) 
        
    import gevent.pool
    pool = gevent.pool.Pool(20)
    while True:
        pool.spawn(call_with_throttling, printget, threshold_per_minute=600) 
    pool.join()


if __name__ == '__main__':
    main()
