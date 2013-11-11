#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex, CategoryIndex
from aggregator.processes import Process

from datetime import datetime, timedelta

from crawler.cates import l1l2s

import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def aggregate_categories(date=None):
    if date is None:
        date = defaultdate
    ci = CategoryIndex(date)
    si = ShopIndex(date)
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
    def __init__(self, date=None):
        super(CateAggProcess, self).__init__('cateagg')
        self.date = date

    def generate_tasks(self):
        pass

    def start(self):
        print('starting process cateagg')
        aggregate_categories(self.date)
        print('ended process cateagg')

    def add_child(self, child):
        raise NotImplementedError('this process can not have children')

    def work(self):
        """ we do our work directly in ``start``, no redis involved """
        pass


cap = CateAggProcess()

if __name__ == '__main__':
    cap.start()
