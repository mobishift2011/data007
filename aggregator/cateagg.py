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
    for cate1, cate2 in l1l2s:
        for mod in ['mon', 'day']:
            info = {
                        'shops': si.getshops(cate1, cate2),
                        'brands': ci.getbrands(cate1, cate2),
                    }
            info.update(ci.getinfo(cate1, cate2, mod))
            ci.setinfo(cate1, cate2, mod, info)
            ci.setindex(cate1, cate2, 'sales', mod, ci.getinfo(cate1, cate2, mod).get('sales', 0))
    for cate1 in topcids:
        for mod in ['mon', 'day']:
            info = {
                'shops': si.getshops(cate1, 'all'),
                'brands': ci.getbrands(cate1, 'all'),
            }
            info.update(ci.getinfo(cate1, 'all', mod))
            ci.setinfo(cate1, 'all', mod, info)

    ci.execute()

class CateAggProcess(Process):
    def __init__(self, date=None):
        super(CateAggProcess, self).__init__('cateagg')
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        self.add_task('aggregator.cateagg.aggregate_categories', self.date)
        self.finish_generation()

    #def start(self):
    #    print('starting process cateagg')
    #    #aggregate_categories(self.date)
    #    print('ended process cateagg')

    def add_child(self, child):
        raise NotImplementedError('this process can not have children')

    #def work(self):
    #    """ we do our work directly in ``start``, no redis involved """
    #    pass


cap = CateAggProcess()

if __name__ == '__main__':
    cap.date = '2013-11-14'
    cap.start()
