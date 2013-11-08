#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex, CategoryIndex
from aggregator.processes import Process

from datetime import datetime, timedelta

from crawler.cates import l1l2s

import traceback

def aggregate_categories(date=datetime.utcnow()+timedelta(hours=8), on_finish=None):
    date2 = datetime(date.year, date.month, date.day)
    d1 = (date2 - timedelta(days=1)).strftime("%Y-%m-%d")
    ci = CategoryIndex(d1)
    si = ShopIndex(d1)
    ci.multi()
    for cate1, cate2 in l1l2s:
        ci.setinfo(cate1, cate2, 'mon', {
                        'shops': si.getshops(cate1, cate2),
                        'brands': ci.getbrands(cate1, cate2),
                    })
        if cate2 != 'all':
            ci.setindex(cate1, cate2, 'sales', 'day', ci.getinfo(cate1, cate2, 'day').get('sales', 0))
            ci.setindex(cate1, cate2, 'sales', 'mon', ci.getinfo(cate1, cate2, 'mon').get('sales', 0))

    ci.execute()

class CateAggProcess(Process):
    def __init__(self):
        super(CateAggProcess, self).__init__('cateagg')

    def generate_tasks(self):
        pass

    def start(self):
        print('starting process cateagg')
        aggregate_categories()
        print('ended process cateagg')

    def add_child(self, child):
        raise NotImplementedError('this process can not have children')

    def work(self):
        """ we do our work directly in ``start``, no redis involved """
        pass


cap = CateAggProcess()

def save_history():
    # shop history
    # 1. save rank per cate (packed as json)
    # 2. save worth
    # 3. save num_collects
    pass

    # brand history
    # 1. sales/30
    # 2. shares
    # 3. shops
    pass

if __name__ == '__main__':
    cap.start()
