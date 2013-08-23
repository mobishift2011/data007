#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Defines all schedulers

A scheduler will regularly spawn jobs which typically 
filter some data from database/cache, list items/shops
in taobao, then put items/shops into queues

There're three Schedulers:

    FullScheduler: list a category
    UpdateScheduler: list a category on only new items
    ItemScheduler: list items based on caches.ItemCT rules
"""
from gevent import monkey; monkey.patch_all()

import time

from caches import ItemCT, LC
from queues import ai1, ai2, af1
from crawler.tbcat import list_cat, get_json, get_ids

class Scheduler(object):
    def start(self):
        while True:
            print('looping')
            if self.should_run():
                self.run()
            time.sleep(1)

    def should_run(self):
        return False

class FullScheduler(Scheduler):
    """ listing category id """
    def __init__(self, cid, use_pool=False):
        self.cid = cid
        self.day = None
        self.use_pool = use_pool

    def should_run(self):
        day = int(time.mktime(time.gmtime())/86400)
        if day != self.day:
            self.day = day
            return True
        else:
            return False

    def run(self):
        def on_ids(ids):
            ai2.put(*ids)
            ItemCT.add_items(*ids)

        list_cat(self.cid, on_ids=on_ids, use_pool=self.use_pool)

class UpdateScheduler(Scheduler):
    def __init__(self, cid=None):
        self.cid = cid
        self.itemid = None

    def should_run(self):
        return True

    def run(self):
        latest_itemid = None
        page = 1
        while page < 10:
            print('fetching page {}'.format(page))
            data = get_json(self.cid, page=page, sort='_oldstart')
            ids = get_ids(data)
            if ids:
                if page == 1:
                    latest_itemid = ids[0]
                    print('last id {}'.format(latest_itemid))
                print('found {} items'.format(len(ids)))
                for id in ids:
                    if id == self.itemid:
                        page = 9999
                        break
                    elif LC.need_update('item', id):
                        print('put {}'.format(id))
                        ai2.put(id)
                page += 1
            else:
                time.sleep(5)
        self.itemid = latest_itemid
    
class ItemScheduler(Scheduler):
    def __init__(self):
        self.ct = None

    def should_run(self):
        ct = int(time.mktime(time.gmtime())%86400/60)
        if ct != self.ct:
            self.ct = ct
            return True
        else:
            False 
        
    def run(self):  
        for itemid in ItemCT.get_items(self.ct):
            if LC.need_update('item', itemid):
                print('putting {}'.format(itemid))
                ai1.put(itemid)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Scheduler with arguments')
    parser.add_argument('--worker', '-w', choices=['full', 'update', 'item'], help='worker type, can be "full", "update", "item"', required=True)
    parser.add_argument('--cid', '-c', type=int, help='category id if worker type in "full" or "update"')
    parser.add_argument('--pool', '-p', action='store_true', help='use gevent pool')
    option = parser.parse_args()
    {
        "full": FullScheduler(option.cid, option.pool),
        "update": UpdateScheduler(option.cid),
        "item": ItemScheduler(),
    }.get(option.worker).start()

if __name__ == '__main__':
    main()
