#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import BrandIndex, CategoryIndex
from aggregator.processes import Process

from datetime import datetime, timedelta

import traceback

def aggregate_brands(date, *brands):
    si = ShopIndex(date)
    bi = BrandIndex(date)
    try:
        si.multi()
        bi.multi()
        for brand in brands:
            aggregate_brand(bi, ci, brand, on_finish_brand)     

        si.execute()
        bi.execute()
    except:
        traceback.print_exc()

def aggregate_brand(bi, ci, brand, on_finish_brand=None):
    baseinfo = {}

    def update_with_cates(cate1, cate2):
        brandinfo = bi.getinfo(brand, cate1, cate2)
        sales = brandinfo.get('sales')
        if sales:
            bi.setindex(brand, cate1, cate2, sales)

            categoryinfo = ci.getinfo(cate1, cate2, 'mon')
            if 'sales' in categoryinfo and categoryinfo['sales']:
                bi.setinfo(brand, cate1, cate2, {'share':float(sales)/float(categoryinfo['sales'])})

        for field in ['sales', 'deals', 'delta_sales', 'items']:
            if field not in baseinfo:
                baseinfo[field] = 0
            baseinfo[field] += brandinfo.get(field, 0)

    # update info & index
    cates = bi.get_cates(brand)
    c1s = list(set([c[0] for c in cates]))
    for c1 in c1s:
        update_with_cates(c1, 'all')
    for cate1, cate2 in cates:
        update_with_cates(cate1, cate2)

    # update base
    baseinfo.update({'shops':bi.getshops(brand)})
    bi.setbase(brand, baseinfo)

    if on_finish_brand:
        on_finish_brand(brand)

class BrandAggProcess(Process):
    def __init__(self):
        super(BrandAggProcess, self).__init__('brandagg')
        self.step = 100
        self.date = (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")

    def generate_tasks(self):
        self.clear_redis()
        bi = BrandIndex(self.date)
        brands = list(bi.getbrands())
        for i in range(len(brands)/self.step):
            bs = brands[i*self.step:(i+1)*self.step]
            self.add_task('aggregator.brandagg.aggregate_brands', self.date, *bs)
        self.finish_generation()

bap = BrandAggProcess()

if __name__ == '__main__':
    bap.start()
