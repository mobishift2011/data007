#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator.models import getdb
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
    cates = list(l1l2s)
    for cate1, cate2 in cates:
        info = {}
        if cate2 != 'all':
            r = getdb().execute('select search_index from ataobao2.cate where id=:id', 
                                dict(id=cate2), result=True)
            if r and r.results:
                info['search_index'] = r.results[0][0]
            else:
                info['search_index'] = 0
        for mod in ['mon', 'day']:
            info.update({
                'shops': si.getshops(cate1, cate2),
                'brands': ci.getbrands(cate1, cate2),
            })
            info.update(ci.getinfo(cate1, cate2, mod))
            print cate1, cate2, mod, info

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
    cap.date = '2014-01-22'
    cap.start()
