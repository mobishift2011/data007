#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex, CategoryIndex
from aggregator.processes import Process

from datetime import datetime, timedelta

from crawler.cates import l1l2s, topcids

import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def aggregate_categories(date=None):
    if date is None:
        date = defaultdate
    ci = CategoryIndex(date)
    si = ShopIndex(date)
    ci.multi()
    l1l2s.extend([[c, 'all'] for c in topcids])
    for cate1, cate2 in l1l2s:
        for mod in ['mon', 'day']:
            info = {
                'shops': si.getshops(cate1, cate2),
                'brands': ci.getbrands(cate1, cate2),
            }
            info.update(ci.getinfo(cate1, cate2, mod))
            for field in ['deals', 'items', 'sales', 'delta_sales']:
                if field not in info:
                    info[field] = 0
            ci.setinfo(cate1, cate2, mod, info)
            ci.setindex(cate1, cate2, 'sales', mod, info.get('sales', 0))

    ci.execute()

class CateAggProcess(Process):
    def __init__(self, date=None):
        super(CateAggProcess, self).__init__('cateagg')
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        self.add_task('aggregator.cateagg.aggregate_categories', self.date)
        self.finish_generation()

cap = CateAggProcess()

if __name__ == '__main__':
    cap.date = '2013-11-27'
    cap.start()
