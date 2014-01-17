#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator.models import getdb
from aggregator.indexes import ShopIndex
from aggregator.processes import Process
from aggregator.esindex import index_shop, flush
from settings import ENV

from datetime import datetime, timedelta

import json
import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def es_shops(shopids, date=None):
    try:
        if date is None:
            date = defaultdate
        si = ShopIndex(date)
        for shopid in shopids:
            try:
                es_shop(si, date, shopid)
            except:
                traceback.print_exc()
        flush()
    except:
        traceback.print_exc()

def es_shop(si, date, shopid):
    db = getdb()
    shopinfo = si.getbase(shopid)
    num_products = int(shopinfo.get('num_products', 0))
    credit_score = int(shopinfo.get('credit_score', 0)) or 1
    good_rating = shopinfo.get('good_rating', '')
    title = shopinfo.get('name', '')
    logo = shopinfo.get('logo', '')
    type = shopinfo.get('type', '')
    worth = float(shopinfo.get('worth', 0))
    cates = si.getcates(shopid)
    sales = 0
    deals = 0
    c1s = list(set([str(c[0]) for c in cates]))
    c2s = list(set([str(c[1]) for c in cates]))
    for c1 in c1s:
        info = si.getinfo(c1, 'all', 'mon', shopid)
        if info:
            sales += float(info.get('sales', 0))
            deals += int(info.get('deals', 0))

    items = si.gethotitems(shopid) or []
    hot_items = []
    if items and sales >= 10000 and credit_score >= 5:
        items = [int(id) for id in items]
        if len(items) == 1:
            r = db.execute('select id, image, num_sold30 from ataobao2.item where id=:id', dict(id=items[0]), result=True)
        else:
            r = db.execute('select id, image, num_sold30 from ataobao2.item where id in :ids', dict(ids=tuple(items[:4])), result=True)
        for row in r.results:
            itemid, image, num_sold30 = row
            hot_items.append({'itemid':itemid, 'deals':num_sold30, 'image':image})

    info = {
        'title': title,
        'logo': logo,
        'cate1': c1s,
        'cate2': c2s,
        'worth': worth,
        'sales': sales,
        'good_rating': good_rating,
        'type': type,
        'credit_score': credit_score,
        'num_products': num_products,
        'average_price': sales/deals if deals !=0 else 0,
        'hot_items': json.dumps(hot_items),
    }

    index_shop(int(shopid), info)

class ShopESProcess(Process):
    def __init__(self, date=None):
        super(ShopESProcess, self).__init__('shopes')
        if ENV == 'DEV':
            self.step = 2**64/5
            self.max_workers = 5
        else:
            self.step = 2**64/10000
            self.max_workers = 50
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        ts = ShopIndex(self.date).allshopids
        for bucket in ts.conn.smembers(ts.bucketskey):
            shopids = ts.conn.smembers(bucket)
            shopids = [int(id) for id in shopids]
            self.add_task('aggregator.shopes.es_shops', shopids, date=self.date)
        self.finish_generation()

sep = ShopESProcess()

if __name__ == '__main__':
    sep.date = '2013-12-18'
    sep.start()
