#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex
from aggregator.processes import Process

from datetime import datetime, timedelta
from collections import Counter

from crawler.cates import l1l2s, topcids

import json
import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def top10_brands(date=None):
    if date is None:
        date = defaultdate
    bi = BrandIndex(date)
    top10 = Counter()
    branddeals = Counter()
    for cate1 in topcids:
        for brand, sales in bi.getindex(cate1, 'all'):
            info = bi.getinfo(brand, cate1, 'all')
            branddeals[brand] += int(info.get('deals', 0))
            top10[brand] += float(sales)
    top10 = top10.most_common(10)
    top10brand = []
    for brand, sales in top10:
        deals = branddeals[brand]
        brand = brand.decode('utf-8')
        top10brand.append((brand, deals, sales))
    db.execute('''insert into ataobao2.top10 (datestr, field, value) values
                    (:datestr, :field, :value)''', dict(datestr=date, field='brand', value=json.dumps(top10brand)))
        

def top10_categories(date=None):
    if date is None:
        date = defaultdate
    ci = CategoryIndex(date)
    top10 = Counter()
    catedeals = Counter()
    for cate1 in topcids:
        info = ci.getinfo(cate1, 'all', 'mon')
        top10[cate1] = float(info.get('sales', 0))    
        catedeals[cate1] = int(info.get('deals', 0))    
    top10cate = []
    for cate, sales in top10.most_common(10):
        deals = catedeals[cate]
        top10cate.append((int(cate), deals, sales))
    db.execute('''insert into ataobao2.top10 (datestr, field, value) values
                    (:datestr, :field, :value)''', dict(datestr=date, field='category', value=json.dumps(top10cate)))

def top10_shops(date=None):
    if date is None:
        date = defaultdate
    si = ShopIndex(date)
    top10 = Counter()
    shopdeals = Counter()
    for cate1 in topcids:
        for shopid, sales in si.getindex(cate1, 'all', 'sales', 'mon'):
            top10[shopid] += sales 
            shopdeals[shopid] = int(si.getbase(shopid).get('deals_mon', 0))
    top10shop = []
    for shopid, sales in top10.most_common(10):
        deals = shopdeals[shopid]
        top10shop.append((int(shopid), deals, sales))
    db.execute('''insert into ataobao2.top10 (datestr, field, value) values
                    (:datestr, :field, :value)''', dict(datestr=date, field='shop', value=json.dumps(top10shop)))

def top10_items(date=None):
    if date is None:
        date = defaultdate
    ii = ItemIndex(date)
    top10 = Counter()
    itemdeals = Counter()
    for cate1 in topcids:
        for itemid, sales in ii.getindex(cate1, 'all', 'sales', 'mon'):
            top10[itemid] = sales
            itemdeals[itemid] = int(ii.getinfo(itemid, cate1).get('deals_mon', 0))
    top10item = []
    for itemid, sales in top10.most_common(10):
        deals = itemdeals[itemid]
        top10item.append((int(itemid), deals, sales))
    db.execute('''insert into ataobao2.top10 (datestr, field, value) values
                    (:datestr, :field, :value)''', dict(datestr=date, field='item', value=json.dumps(top10item)))

class Top10AggProcess(Process):
    def __init__(self, date=None):
        super(Top10AggProcess, self).__init__('top10agg')
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        for method in ['top10_brands', 'top10_categories', 'top10_shops', 'top10_items']:
            method = 'aggregator.top10agg.' + method
            self.add_task(method, self.date) 
        self.finish_generation()

    def add_child(self, child):
        raise NotImplementedError('this process can not have children')

tap = Top10AggProcess()

if __name__ == '__main__':
    tap.date = '2013-11-25'
    tap.start()
