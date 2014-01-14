#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator.models import getdb
from aggregator.indexes import ShopIndex, CategoryIndex
from aggregator.processes import Process

from settings import ENV
from datetime import datetime, timedelta
from bisect import bisect

import traceback

credits = [ 4, 11, 41, 91, 151,
            251, 501, 1001, 2001, 5001,
            10001, 20001, 50001, 100001, 200001,
            500001, 1000001, 2000001, 5000001, 10000001, ]

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def aggregate_shops(start, end, date=None):
    try:
        db = getdb()
        if date is None:
            date = defaultdate
        si = ShopIndex(date)
        ci = CategoryIndex(date)
        si.multi()
        ci.multi()
        shopids = set()
        with db.connection() as cur:
            cur.execute('''select id, title, logo, type, credit_score, num_products, good_rating, num_collects
                    from ataobao2.shop
                    where token(id)>=:start and token(id)<:end''',
                    dict(start=start, end=end), consistency_level='ONE')

            for row in cur:
                shopid, name, logo, type, credit_score, num_products, good_rating, num_collects = row
                shopids.add(shopid)
                try:
                    aggregate_shop(si, ci, shopid, name, logo, type, credit_score, num_products, good_rating, num_collects)
                except:
                    traceback.print_exc()
        si.allshopids.add(*shopids)
        si.execute()
        ci.execute()
    except:
        traceback.print_exc()

def aggregate_shop(si, ci, shopid, name, logo, type, credit_score, num_products, good_rating, num_collects):
    shopinfo = si.getbase(shopid)
    if shopinfo:
        # create indexes
        credit_score = credit_score or 0
        active_index = float(shopinfo['active_index_mon'])
        sales = float(shopinfo['sales_mon'])
        worth = 2**credit_score + active_index/3000. + sales/30.
        update = {'name':name, 'logo':logo, 'credit_score':credit_score, 'worth':worth,
                    'type':type, 'num_products':num_products, 'good_rating':good_rating,
                    'num_collects':num_collects}
        si.setbase(shopid, update)

        def update_with_cates(cate1, cate2):
            ci.incrcredit(cate1, cate2, credit_score if type =='taobao' else 21)
            for mod in ['mon', 'day']:
                shopinfo = si.getinfo(cate1, cate2, mod, shopid)
                for field in ['sales', 'deals', 'active_index']:
                    shopinfo[field] = float(shopinfo[field])
                score = shopinfo['active_index']/1000. + shopinfo['sales']/30.
                update = {'credit_score':credit_score, 'worth':worth, 'score':score}
                si.setinfo(cate1, cate2, mod, shopid, update)
                shopinfo.update(update)
                for field in ['sales', 'deals', 'active_index', 'credit_score', 'worth', 'score']:
                    si.setindex(cate1, cate2, field, mod, shopid, shopinfo[field])

        cates = si.getcates(shopid)
        cates.extend(list(set([(c[0], 'all') for c in cates])))
        for cate1, cate2 in cates:
            update_with_cates(cate1, cate2)
            si.setbase(shopid, update, skey='{}_{}'.format(cate1, cate2))


class ShopAggProcess(Process):
    def __init__(self, date=None):
        super(ShopAggProcess, self).__init__('shopagg')
        if ENV == 'DEV':
            self.step = 2**64/100
            self.max_workers = 10
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
            self.add_task('aggregator.shopagg.aggregate_shops', start, end, date=self.date)
        self.finish_generation()

sap = ShopAggProcess()

if __name__ == '__main__':
    sap.date = '2013-11-14'
    sap.start()
