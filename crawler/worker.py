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

from models import item
from caches import LC, ItemCT, ShopItem
from queues import poll, ai1, ai2, as1, af1
from crawler.tbitem import get_item
from crawler.tbshop import list_shop

class Worker(object):
    """ General Worker """
    def __init__(self, poolsize=100):
        self.pool = gevent.pool.Pool(poolsize)

    def work(self):
        raise NotImplementedError('this method should be implemented by subclasses')

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
            if d:
                item.insert(str(itemid), d)

                if LC.need_update('shop', d['shopid']):
                    # queue shop jobs
                    as1.put(d['shopid'])

        while True:
            itemid = poll([ai1, ai2], timeout=10)
            if itemid:
                self.pool.spawn(LC.update_if_needed, 'item', itemid, on_update)

class ShopWorker(Worker):
    """ Work on Shop Queues

    1. poll item ids from [as1]
    2. check update, if yes, go on
    3. listing items in shop, update ItemCT and ShopItem info
    """
    def work(self):
        shopid = None

        def on_update(ids):
            print('updating shop-item of shop {}'.format(shopid))
            ShopItem.add_items(shopid, *ids)
            ItemCT.add_items(*ids)
            ai2.put(*ids)

        def spawn_shop(shopid):
            self.pool.spawn(list_shop, shopid, on_update)
            
        while True:
            shopid = poll([as1], timeout=10)
            if shopid:
                LC.update_if_needed('shop', shopid, spawn_shop)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Worker with arguments')
    parser.add_argument('--worker', '-w', choices=['item', 'shop'], help='worker type, can be "item", or "shop"', required=True)
    parser.add_argument('--poolsize', '-p', type=int, default=100, help='gevent pool size for worker (default: %(default)s)')
    option = parser.parse_args()
    {
        "item": ItemWorker(option.poolsize),
        "shop": ShopWorker(option.poolsize),
    }.get(option.worker).work()

if __name__ == '__main__':
    main()
