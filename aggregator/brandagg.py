#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import BrandIndex, CategoryIndex
from aggregator.processes import Process
from crawler.cates import l1l2s, topcids

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

        num_shops = bi.getshops(brand, cate1, cate2) or 0
        bi.setinfo(brand, cate1, cate2, {'share':share, 'shops': num_shops})

        if cate2 == 'all':
            db.execute('''insert into ataobao2.brand_by_date (name, datestr, cate1, sales, share, num_shops)
                values (:name, :datestr, :cate1, :sales, :share, :num_shops)''',
                dict(name=brand.decode('utf-8'), datestr=date, cate1=cate1, sales=sales, share=share, num_shops=num_shops))


    # update info & index
    cates = bi.getcates(brand)
    for cate1, cate2 in cates:
        update_with_cates(cate1, cate2)

class BrandAggProcess(Process):
    def __init__(self, date=None):
        super(BrandAggProcess, self).__init__('brandagg')
        if ENV == 'DEV':
            self.step = 100
            self.max_workers = 10
        else:
            self.step = 1000
            self.max_workers = 100
        self.date = date or defaultdate

    def generate_tasks(self):
        self.clear_redis()
        bi = BrandIndex(self.date)
        ci = CategoryIndex(self.date)
        #from aggregator.brands import brands as brands1
        brands2 = set(b.decode('utf-8') for b in bi.getbrands())
        #brands = list(brands1 & brands2)
        allbrands = set()
        for cate1, cate2 in l1l2s:
            brands1 = ci.getbrandnames(cate1, cate2)
            brands = list(brands1 - allbrands)
            allbrands.update(brands1)
            for i in range(1+len(brands)/self.step):
                bs = brands[i*self.step:(i+1)*self.step]
                self.add_task('aggregator.brandagg.aggregate_brands', self.date, *bs)
        self.finish_generation()

bap = BrandAggProcess()

if __name__ == '__main__':
    bap.date = '2013-12-18'
    bap.start()
