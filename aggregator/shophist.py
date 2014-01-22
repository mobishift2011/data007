#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator.models import getdb
from aggregator.indexes import ShopIndex
from aggregator.processes import Process
from settings import ENV

from datetime import datetime, timedelta
from operator import itemgetter

import json
import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def save_history_shops(shopids, date=None):
    try:
        if date is None:
            date = defaultdate
        si = ShopIndex(date)
        si.multi()
        for shopid in shopids:
            try:
                save_history_shop(si, date, shopid)
            except:
                traceback.print_exc()
        si.execute()
    except:
        traceback.print_exc()

def save_history_shop(si, date, shopid):
    db = getdb()
    shopinfo = si.getbase(shopid)
    if shopinfo:
        num_collects = int(shopinfo.get('num_collects', 0))
        worth = float(shopinfo.get('worth', 0))
        sales = 0
        catetrend = {}
        cates = si.getcates(shopid)
        c1s = list(set([c[0] for c in cates]))
        for c1 in c1s:
            catetrend[c1] = {'rank': si.getrank(c1, 'all', shopid, 'day')}
            info = si.getinfo(c1, 'all', 'day', shopid)
            if info:
                catetrend[c1]['sales'] = float(info.get('sales', 0))
                sales += catetrend[c1]['sales']
                catetrend[c1]['deals'] = int(info.get('deals', 0))
        brandshare = {}

        for mod in ['mon', 'day']:
            brandshare[mod] = {}
            info = si.getbrandinfo(shopid, 'sales', mod)
            dealsinfo = si.getbrandinfo(shopid, 'deals', mod)
            binfo = [(brand, float(value), int(dealsinfo.get(brand, 0)) )
                        for brand, value in info.iteritems() if float(value)>0]
            total_sales = sum(sales for brand, sales, deals in binfo)
            if total_sales == 0:
                top10 = []
            else:
                tops = sorted(binfo, key=itemgetter(1), reverse=True)
                other_sales = sum(sales for brand, sales, deals in tops[9:])
                other_deals = sum(deals for brand, sales, deals in tops[9:])
                tops = [(brand.decode('utf-8'), '{:4.2f}%'.format(sales*100/total_sales), sales, deals)
                                for brand, sales, deals in tops[:9] ]
                if other_sales > 0:
                    tops.append((u'其他', '{:4.2f}%'.format(other_sales*100/total_sales), other_sales, other_deals))
                top10 = tops

            brandshare[mod] = top10

        cateshare = {}
        for mod in ['mon', 'day']:
            cinfo = []
            total_sales = 0
            for cate1, cate2 in cates:
                info = si.getinfo(cate1, cate2, mod, shopid)
                if info and float(info.get('sales', 0)) > 0:
                    total_sales += float(info.get('sales', 0))
                    cinfo.append((cate2, float(info.get('sales', 0)), int(info.get('deals', 0))))
            if total_sales == 0:
                top10 = []
            else:
                tops = sorted(cinfo, key=itemgetter(1), reverse=True)
                other_sales = sum(sales for cate2, sales, deals in tops[9:])
                other_deals = sum(deals for cate2, sales, deals in tops[9:])
                tops = [(cate2, '{:4.2f}%'.format(sales*100/total_sales), sales, deals)
                            for cate2, sales, deals in tops[:9]]
                if other_sales > 0:
                    tops.append((u'其他', '{:4.2f}'.format(other_sales*100/total_sales), other_sales, other_deals))
                top10 = tops
            cateshare[mod] = top10

        db.execute('''insert into ataobao2.shop_by_date 
                    (id, datestr, worth, sales, num_collects, catetrend, brandshare, cateshare) values
                    (:shopid, :datestr, :worth, :sales, :num_collects, :catetrend, :brandshare, :cateshare)''',
                    dict(worth=worth, num_collects=num_collects, shopid=shopid, datestr=date, sales=total_sales,
                        catetrend=json.dumps(catetrend), brandshare=json.dumps(brandshare), cateshare=json.dumps(cateshare)))

class ShopHistProcess(Process):
    def __init__(self, date=None):
        super(ShopHistProcess, self).__init__('shophist')
        if ENV == 'DEV':
            self.max_workers = 10
        else:
            self.max_workers = 50
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        ts = ShopIndex(self.date).allshopids
        for bucket in ts.conn.smembers(ts.bucketskey):
            shopids = ts.conn.smembers(bucket)
            shopids = [int(id) for id in shopids]
            self.add_task('aggregator.shophist.save_history_shops', shopids, date=self.date)
        self.finish_generation()

shp = ShopHistProcess()

if __name__ == '__main__':
    shp.date = '2014-01-16'
    #shp.start()
    save_history_shops([57301243], '2014-01-16')
