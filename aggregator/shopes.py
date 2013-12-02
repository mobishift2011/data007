#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex
from aggregator.processes import Process
from aggregator.esindex import index_shop, flush
from settings import ENV

from datetime import datetime, timedelta

import json
import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def es_shops(start, end, date=None):
    try:
        if date is None:
            date = defaultdate
        si = ShopIndex(date)
        with db.connection() as cur:
            cur.execute('''select id, num_products, credit_score, good_rating, title, logo, type
                    from ataobao2.shop
                    where token(id)>=:start and token(id)<:end''',
                    dict(start=start, end=end), consistency_level='ONE')
            for row in cur:
                shopid, num_products, credit_score, good_rating, title, logo, type = row
                credit_score = credit_score or 1
                try:
                    es_shop(si, date, shopid, num_products, credit_score, good_rating, title, logo, type)
                except:
                    traceback.print_exc()
        flush()
    except:
        traceback.print_exc()

def es_shop(si, date, shopid, num_products, credit_score, good_rating, title, logo, type):
    shopinfo = si.getbase(shopid)
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
    if items:
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
            self.max_workers = 1
        else:
            self.step = 2**64/10000
            self.max_workers = 100
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        count = 0
        for start in range(-2**63, 2**63, self.step):
            end = start + self.step
            if end > 2**63-1:
                end = 2**63-1
            self.add_task('aggregator.shopes.es_shops', start, end, date=self.date)
        self.finish_generation()

sep = ShopESProcess()

if __name__ == '__main__':
    sep.date = '2013-11-28'
    sep.start()
