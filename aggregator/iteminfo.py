#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator.models import getdb
from aggregator.indexes import ItemIndex
from aggregator.processes import Process
from aggregator.itemagg import parse_iteminfo

from settings import ENV
from datetime import datetime, timedelta

from crawler.cates import cates

import traceback

def save_iteminfos(date, *itemids):
    ii = ItemIndex(date)
    for itemid in itemids:
        try:
            save_iteminfo(date, ii, itemid)
        except:
            traceback.print_exc()

def save_iteminfo(date, ii, itemid):
    db = getdb()
    date2 = datetime.strptime(date, "%Y-%m-%d")+timedelta(hours=16)
    date1 = date2 - timedelta(days=60)
    r1 = db.execute('''select title, image, shopid, brand, price, num_sold30, cid
                from ataobao2.item where id=:itemid''',
                dict(itemid=itemid), result=True)
    r2 = db.execute('''select date, num_collects, num_reviews, num_sold30, num_views
                    from ataobao2.item_by_date
                    where id=:itemid and date>=:date1 and date<:date2''',
                    dict(itemid=itemid, date1=date1, date2=date2), result=True)

    items = {(r[0]+timedelta(hours=8)).strftime("%Y-%m-%d"): r[1:]
                for r in r2.results}

    if r1.results:
        name, image, shopid, brand, price, deals_mon, cid = r1.results[0]
        info = parse_iteminfo(date, itemid, items, price, cid)
        if info is None:
            print 'no result from parse_iteminfo', date, itemid, items, price, cid
            return

        cate1 = info['l1']
        for cate2 in set([info['l2'], 'all']):
            ii.setinfo(itemid, {
                'name': name,
                'image': image,
                'shopid': shopid,
                'brand': brand,
                'price': price,
                'sales_day': info['sales_day'],
                'sales_mon': info['sales_mon'],
                'deals_day': info['deals_day'],
                'deals_mon': info['deals_mon'],
                'delta_sales_mon': info['delta_sales_mon'],
                'delta_sales_day': info['delta_sales_day'],
            }, skey='{}_{}'.format(cate1, cate2))



class ItemInfoProcess(Process):
    def __init__(self, date=None):
        super(ItemInfoProcess, self).__init__('iteminfo')
        self.date = date
        if ENV == 'DEV':
            self.max_workers = 5
        else:
            self.max_workers = 50

    def generate_tasks(self):
        self.clear_redis()
        ii = ItemIndex(self.date)
        allids = set()
        cates = ii.getcates()
        cates.extend(list(set([(c[0], 'all') for c in cates])))
        for cate1, cate2 in cates:
            ids1 = ii.gettopitemids(cate1, cate2, 'sales', 'mon')
            ids2 = ii.gettopitemids(cate1, cate2, 'sales', 'day')
            ids = (set(ids1) | set(ids2)) - allids
            allids.update(ids)
            if ids:
                self.add_task('aggregator.iteminfo.save_iteminfos', self.date, *ids)
        self.finish_generation()

iip = ItemInfoProcess()

if __name__ == '__main__':
    #iip.date = '2013-11-14'
    #iip.start()
    ii = ItemIndex('2014-01-14')
    save_iteminfo('2014-01-14', ii, 16406397840)
