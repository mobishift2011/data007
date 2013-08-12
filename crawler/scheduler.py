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

from caches import ItemCT
from queues import ai1, af1
from crawler.tbcat import list_cat, get_json

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
    def __init__(self, cid):
        self.cid = cid
        self.day = None

    def should_run(self):
        day = int(time.mktime(time.gmtime())/86400)
        if day != self.day:
            self.day = day
            return True
        else:
            return False

    def run(self):
        def on_ids(ids):
            ai1.put(*ids)
            ItemCT.add_items(*ids)

        list_cat(self.cid, on_ids=on_ids)

class UpdateScheduler(Scheduler):
    def __init__(self, cid=None):
        self.cid = cid

    def should_run(self):
        return False

    def run(self):
        pass
    
class ItemScheduler(Scheduler):
    def __init__(self):
        self.ct = None

    def should_run(self):
        ct = int(time.mktime(time.gmtime())/86400/60)
        if ct != self.ct:
            self.ct = ct
            return True
        else:
            False 
        
    def run(self):  
        for itemid in ItemCT.get_items(self.ct):
            if LC.need_update('item', itemid):
                ai1.put(itemid)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Scheduler with arguments')
    parser.add_argument('--worker', '-w', choices=['full', 'update', 'item'], help='worker type, can be "full", "update", "item"', required=True)
    parser.add_argument('--cid', '-c', type=int, help='category id if worker type in "full" or "update"')
    option = parser.parse_args()
    {
        "full": FullScheduler(option.cid),
        "update": UpdateScheduler(option.cid),
        "item": ItemScheduler(),
    }.get(option.worker).start()

if __name__ == '__main__':
    main()
