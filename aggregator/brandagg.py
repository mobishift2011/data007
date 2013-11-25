#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import BrandIndex, CategoryIndex
from aggregator.processes import Process

from settings import ENV
from datetime import datetime, timedelta

import traceback
defaultdate = (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")


def aggregate_brands(date, *brands):
    ci = CategoryIndex(date)
    bi = BrandIndex(date)
    try:
        ci.multi()
        bi.multi()
        for brand in brands:
            aggregate_brand(bi, ci, date, brand)     

        ci.execute()
        bi.execute()
    except:
        traceback.print_exc()

def aggregate_brand(bi, ci, date, brand):
    if brand == '':
        brand = '其他'
    baseinfo = {}

    def update_with_cates(cate1, cate2):
        brandinfo = bi.getinfo(brand, cate1, cate2)
        sales = float(brandinfo.get('sales', 0))
        bi.setindex(brand, cate1, cate2, sales)
        categoryinfo = ci.getinfo(cate1, cate2, 'mon')
        try:
            share = sales/float(categoryinfo['sales'])
        except:
            share = 0

        if cate2 == 'all':
            num_shops = bi.getshops(brand, cate1, cate2)
            bi.setinfo(brand, cate1, cate2, {'share':share})
            db.execute('''insert into ataobao2.brand_by_date (name, date, cate1, sales, share, num_shops)
                values (:name, :date, :cate1, :sales, :share, :num_shops)''',
                dict(name=brand.decode('utf-8'), date=date, cate1=cate1, sales=sales, share=share, num_shops=num_shops))


    # update info & index
    cates = bi.getcates(brand)
    c1s = list(set([c[0] for c in cates]))
    for c1 in c1s:
        update_with_cates(c1, 'all')
    for cate1, cate2 in cates:
        update_with_cates(cate1, cate2)


class BrandAggProcess(Process):
    def __init__(self, date=None):
        super(BrandAggProcess, self).__init__('brandagg')
        if ENV == 'DEV':
            self.step = 100
        else:
            self.step = 1000
        self.date = date or defaultdate

    def generate_tasks(self):
        self.clear_redis()
        bi = BrandIndex(self.date)
        from aggregator.brands import brands as brands1
        brands2 = set(b.decode('utf-8') for b in bi.getbrands()))
        brands = list(brands1 & brands2)
        for i in range(len(brands)/self.step):
            bs = brands[i*self.step:(i+1)*self.step]
            self.add_task('aggregator.brandagg.aggregate_brands', self.date, *bs)
        self.finish_generation()

bap = BrandAggProcess()

if __name__ == '__main__':
    bap.start()
