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
import gevent.pool

import time
import traceback

from caches import ItemCT, LC
from queues import ai1, ai2, af1
from crawler.tbcat import list_cat, get_json, get_ids
from crawler.cates import fecids

class Scheduler(object):
    def start(self):
        while True:
            print('looping')
            if self.should_run():
                try:
                    self.run()
                except:
                    traceback.print_exc()
            time.sleep(1)

    def should_run(self):
        return False

class AllScheduler(Scheduler):
    """ listing all category """
    def __init__(self):
        self.week = None
        self.pool = gevent.pool.Pool(100)

    def should_run(self):
        week = int(time.mktime(time.gmtime())/86400/7)
        if week != self.week:
            self.week = week
            return True
        else:
            return False

    def run(self):
        def on_ids(ids):
            ai2.put(*ids)
            ItemCT.add_items(*ids)
        
        for cid in fecids:
            self.pool.spawn(list_cat, cid, on_ids=on_ids, use_pool=False)
        self.pool.join()

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
        self.hour = None

    def should_run(self):
        hour = int(time.mktime(time.gmtime())/3600)
        if hour != self.hour:
            self.hour = hour
            return True
        else:
            return False

    def run(self):
        def update_latest_ids(cid):
            data = get_json(cid, page=1, sort='_oldstart')
            nids = get_ids(data)
            if nids:
                print 'found {} ids in category {}'.format(len(nids), cid)
                ai2.put(*list(nids))

        pool = gevent.pool.Pool(10)
        for cid in fecids:
            pool.spawn(update_latest_ids, cid)
        pool.join()


class ItemScheduler(Scheduler):
    def __init__(self):
        self.ct = None

    def should_run(self):
        ct = int(time.mktime(time.gmtime())%86400/60+480)
        if ct >= 1435:
            ct -= 1430
        if ct != self.ct:
            self.ct = ct
            return True
        else:
            return False 
        
    def run(self):  
        ids = ItemCT.get_items(self.ct)
        if ids:
            print('ct = {}'.format(self.ct))
            print('scheduled {} items for lastcheck'.format(len(ids)))
            ids = LC.need_update('item', *ids)
            ai1.put(*ids)
            print('putting {} items in queue'.format(len(ids)))

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Scheduler with arguments')
    parser.add_argument('--worker', '-w', choices=['full', 'all', 'update', 'item'], help='worker type, can be "full", "update", "item"', required=True)
    parser.add_argument('--cid', '-c', type=int, help='category id if worker type in "full" or "update"')
    parser.add_argument('--pool', '-p', action='store_true', help='use gevent pool')
    option = parser.parse_args()
    if option.worker == "full":
        FullScheduler(option.cid, option.pool).start()
    elif option.worker == "all":
        AllScheduler().start()
    elif option.worker == "update":
        UpdateScheduler().start()
    elif option.worker == "item":
        ItemScheduler().start()

if __name__ == '__main__':
    main()
