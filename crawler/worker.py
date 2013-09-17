#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" All workers defined here

A worker typically "watches" a queue, and do jobs accordingly

Currently there're two workers:
    ItemWorker: update item info
    ShopWorker: update shop info
"""
from gevent import monkey; monkey.patch_all()

import gevent.pool
from functools import partial

from models import db, update_item
from caches import LC, ItemCT, ShopItem
from queues import poll, ai1, ai2, as1, af1
from crawler.tbitem import get_item, is_valid_item
from crawler.tbshop import list_shop

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
    """
    def work(self):
        def on_update(itemid):
            print('updating item id: {}'.format(itemid))
            d = get_item(itemid)
            if 'notfound' in d or 'error' in d:
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
                    raise ValueError('item update failed: {}'.format(d))

                if LC.need_update('shop', d['shopid']):
                    # queue shop jobs
                    as1.put(d['shopid'])

        while True:
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

        def spawn_shop(shopid):
            print('updating shop-item of shop {}'.format(shopid))
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

if __name__ == '__main__':
    main()
