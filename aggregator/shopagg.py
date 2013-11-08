#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex, CategoryIndex
from aggregator.processes import Process

from datetime import datetime, timedelta
from bisect import bisect

import traceback

credits = [ 4, 11, 41, 91, 151, 
            251, 501, 1001, 2001, 5001, 
            10001, 20001, 50001, 100001, 200001,
            500001, 1000001, 2000001, 5000001, 10000001, ]

def aggregate_shops(start, end, date=datetime.utcnow()+timedelta(hours=8), on_finish_shop=None, on_finish=None):
    date2 = datetime(date.year, date.month, date.day)
    d1 = (date2 - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        si = ShopIndex(d1)
        ci = CategoryIndex(d1)
        si.multi()
        ci.multi()
        with db.connection() as cur:
            cur.execute('''select id, title, logo, rank, rank_num from ataobao2.shop
                    where token(id)>=:start and token(id)<:end''',
                    dict(start=start, end=end), consistency_level='ONE')
            for row in cur:
                shopid, name, logo, rank, rank_num = row
                try:
                    aggregate_shop(si, ci, shopid, name, logo, rank, rank_num, on_finish_shop)
                except:
                    traceback.print_exc()
        si.execute()
        ci.execute()
    except:
        traceback.print_exc()

    if on_finish:
        on_finish('shop', d1, start, end)

def aggregate_shop(si, ci, shopid, name, logo, rank, rank_num, on_finish_shop):
    shopinfo = si.getbase(shopid)
    if shopinfo:
        # create indexes
        active_index = float(shopinfo['active_index_mon'])
        sales = float(shopinfo['sales_mon'])
        credit_score = bisect(credits, rank_num)
        worth = 2**credit_score + active_index/3000. + sales/30.
        update = {'name':name, 'logo':logo, 'credit_score':credit_score, 'worth':worth}
        update['type'] = 'tmall' if rank == 'tmall' else 'taobao'
        si.setbase(shopid, update)

        def update_with_cates(cate1, cate2):
            ci.incrcredit(cate1, cate2, credit_score)
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
        c1s = list(set([c[0] for c in cates]))
        for c1 in c1s:
            update_with_cates(c1, 'all')
        for cate1, cate2 in cates:
            update_with_cates(cate1, cate2)

    if on_finish_shop:
        on_finish_shop(shopid)

class ShopAggProcess(Process):
    def __init__(self):
        super(ShopAggProcess, self).__init__('shopagg')
        self.step = 2**64/100

    def generate_tasks(self):
        self.clear_redis()
        count = 0
        for start in range(-2**63, 2**63, self.step):
            end = start + self.step
            if end > 2**63-1:
                end = 2**63-1
            self.add_task('aggregator.shopagg.aggregate_shops', start, end)
        self.finish_generation()

sap = ShopAggProcess()

if __name__ == '__main__':
    sap.start()
