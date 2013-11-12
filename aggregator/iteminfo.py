#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ItemIndex
from aggregator.processes import Process

from settings import ENV
from datetime import datetime, timedelta

from crawler.cates import cates

import traceback

def save_iteminfos(date, *itemids):
    ii = ItemIndex(date)
    for itemid in itemids:
        try:
            save_iteminfo(ii, itemid)
        except:
            traceback.print_exc()

def save_iteminfo(ii, itemid):
    r = db.execute('''select title, image, shopid, brand, price, num_sold30
                from ataobao2.item where id=:itemid''', dict(itemid=itemid), result=True)
    if r.results:
        name, image, shopid, brand, price, deals_mon = r.results[0]
        deals_day = deals_mon // 30
        sales_mon = deals_mon * price
        sales_day = deals_day * price
        ii.setinfo(itemid, {
            'name': name,
            'image': image,
            'shopid': shopid,
            'brand': brand,
            'price': price,
            'sales_day': sales_day,
            'sales_mon': sales_mon,
            'deals_day': deals_day,
            'deals_mon': deals_mon,
        })

    

class ItemInfoProcess(Process):
    def __init__(self, date=None):
        super(ItemInfoProcess, self).__init__('iteminfo')
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        ii = ItemIndex(self.date)
        allids = set()
        for cate1, cate2 in ii.getcates():
            ids1 = ii.gettopitemids(cate1, cate2, 'sales', 'mon')
            ids2 = ii.gettopitemids(cate1, cate2, 'sales', 'day')
            ids = (set(ids1) | set(ids2)) - allids
            allids.update(ids)
            if ids:
                self.add_task('aggregator.iteminfo.save_iteminfos', self.date, *ids)
        self.finish_generation()

iip = ItemInfoProcess()

if __name__ == '__main__':
    iip.date = '2013-11-11'
    iip.start()
