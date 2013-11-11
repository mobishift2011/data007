#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex
from aggregator.processes import Process

from settings import ENV
from datetime import datetime, timedelta

from crawler.cates import cates

import traceback

def get_l1_and_l2_cids(cids): 
    l1l2 = {}
    for cid in cids:
        if cid in cates:
            cidchain = []
            while cates[cid] != 0:
                cidchain.append(cid)
                cid = cates[cid]
            cidchain.append(cid)
            try:
                l1l2[ cidchain[0] ] = (cidchain[-1], cidchain[-2])
            except:
                pass
    return l1l2

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def aggregate_items(start, end, date=None):
    try:
        if date is None:
            date = defaultdate
        si = ShopIndex(date)
        ii = ItemIndex(date)
        bi = BrandIndex(date)
        ci = CategoryIndex(date)
        si.multi()
        ii.multi()
        bi.multi()
        ci.multi()
        with db.connection() as cur:
            cur.execute('''select id, shopid, cid, num_sold30, price, brand, title, image 
                    from ataobao2.item where token(id)>=:start and token(id)<:end''', 
                    dict(start=int(start), end=int(end)), consistency_level='ONE')
            for row in cur:
                itemid, shopid, cid, nc, price, brand, name, image = row
                if nc > 0:
                    try:
                        aggregate_item(si, ii, bi, ci, itemid, shopid, cid, price, brand, name, image, date)
                    except:
                        traceback.print_exc()
        si.execute()
        bi.execute()
        ci.execute()
        ii.execute()
    except:
        traceback.print_exc()

def aggregate_item(si, ii, bi, ci, itemid, shopid, cid, price, brand, name, image, date):
    brand = brand.encode('utf-8')
    date2 = datetime.strptime(date, "%Y-%m-%d")
    date1 = date2 - timedelta(days=60)
    d1 = date
    d2 = (date2 - timedelta(days=2)).strftime("%Y-%m-%d")
    d3 = (date2 - timedelta(days=3)).strftime("%Y-%m-%d")
    d31 = (date2 - timedelta(days=31)).strftime("%Y-%m-%d")
    d32 = (date2 - timedelta(days=32)).strftime("%Y-%m-%d")
    d61 = (date2 - timedelta(days=61)).strftime("%Y-%m-%d")
    d62 = (date2 - timedelta(days=62)).strftime("%Y-%m-%d")
    items = db.execute('''select date, num_collects, num_reviews, num_sold30, num_views from ataobao2.item_by_date 
                    where id=:itemid and date>=:date1 and date<:date2''',
                    dict(itemid=itemid, date1=date1, date2=date2), result=True).results
    items = {i[0].strftime("%Y-%m-%d"):i[1:] for i in items}
    if d1 in items and items[d1][2]>0:
        try:
            l1, l2 = get_l1_and_l2_cids([cid])[cid]
        except:
            return

        i1 = items[d1]
        i2 = items.get(d2, i1)
        i3 = items.get(d3, i2)
        i31 = items.get(d31, i1)
        i32 = items.get(d32, i2)
        i61 = items.get(d61, i31)
        i62 = items.get(d62, i32)
        active_index_day = max(0, (i1[1]-i2[1])*50 + (i1[0]-i2[0])*10 + (i1[3]-i2[3]))
        delta_active_index_day = active_index_day - max(0, (i2[1]-i3[1])*50 - (i2[0]-i3[0])*10 - (i2[3]-i3[3]))
        active_index_mon = max(0, (i1[1]-i31[1])*50 + (i1[0]-i31[0])*10 + (i1[3]-i31[3]))
        delta_active_index_mon = active_index_mon - max(0, (i31[1]-i61[1])*50 - (i31[0]-i61[0])*10 - (i31[3]-i61[3]))
        deals_mon = i1[2]
        if d31 in items:
            deals_day = i1[2] - (i2[2] - i31[2])
        else:
            deals_day = i1[2]//30
        if d32 in items:
            deals_day1 = i2[2] - (i3[2] - i32[2])
        else:
            deals_day1 = i2[2]//30
        price = price
        sales_mon = deals_mon * price
        sales_day = deals_day * price
        delta_sales_mon = deals_mon * price - i2[2] * price 
        delta_sales_day = deals_day * price - deals_day1 * price

        # inc category counters
        for mod in ['day', 'mon']:
            inc = {
                'sales': locals()['sales_'+mod],
                'deals': locals()['deals_'+mod],
                'delta_sales': locals()['delta_sales_'+mod],
                'items': 1,
            }
            ci.incrinfo(l1, l2, mod, inc)
            ci.incrinfo(l1, 'all', mod, inc)
        ci.addbrand(l1, l2, brand)
        ci.addbrand(l1, 'all', brand)

        # inc brand counters
        bi.addbrand(brand)
        bi.addshop(brand, l1, l2, shopid)
        bi.addcates(brand, l1, l2)
        bi.addhots(brand, l1, itemid, shopid, sales_mon)
        inc = {
            'items': 1,
            'deals': deals_mon,
            'sales': sales_mon,
            'delta_sales': delta_sales_mon,
        }
        bi.incrinfo(brand, l1, l2, inc)
        bi.incrinfo(brand, l1, 'all', inc)

        # inc item counters
        ii.incrcates(l1, l2, sales_mon, deals_mon)
        ii.incrindex(l1, l2, 'sales', 'mon', itemid, sales_mon)
        ii.incrindex(l1, 'all', 'sales', 'mon', itemid, sales_mon)
        ii.incrindex(l1, l2, 'sales', 'day', itemid, sales_day)
        ii.incrindex(l1, 'all', 'sales', 'day', itemid, sales_day)
        ii.setinfo(itemid, {
            'name': name,
            'image': image,
            'shopid': shopid,
            'brand': brand,
            'price': price,
            'sales_day': sales_day,
            'sales_mon': sales_mon,
            'deals_day': deals_day,
            'deals_mon': deals_mon,
        })

        # inc shop counters
        si.addcates(shopid, l1, l2)
        si.incrbrand(shopid, 'sales', brand, sales_mon)
        si.incrbrand(shopid, 'deals', brand, deals_mon)
        si.addhotitems(shopid, itemid, sales_mon)

        cate1 = l1
        for cate2 in  ['all', l2]:
            for period in ['mon', 'day']:
                inc = {'sales':locals()['sales_'+period],
                       'deals':locals()['deals_'+period],
                       'delta_sales': locals()['delta_sales_'+period],
                       'active_index': locals()['active_index_'+period],
                       'delta_active_index': locals()['delta_active_index_'+period]}
                # we do index creation later
                #for field in ['sales', 'deals', 'active_index']:
                #    #si.incrindex( cate1, cate2, field, period, shopid, inc[field])
                si.incrinfo(cate1, cate2, period, shopid, inc)
        inc = {'sales_mon': sales_mon,
               'sales_day': sales_day,
               'deals_mon': deals_mon,
               'deals_day': deals_day,
               'active_index_mon': active_index_mon,
               'active_index_day': active_index_day}
        si.incrbase(shopid, inc)


class ItemAggProcess(Process):
    def __init__(self, date=None):
        super(ItemAggProcess, self).__init__('itemagg')
        if ENV == 'DEV':
            self.step = 2**64/100
        else:
            self.step = 2**64/100000
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        count = 0
        for start in range(-2**63, 2**63, self.step):
            end = start + self.step
            if end > 2**63-1:
                end = 2**63-1
            self.add_task('aggregator.itemagg.aggregate_items', start, end, date=self.date)
        self.finish_generation()

iap = ItemAggProcess()

if __name__ == '__main__':
    iap.start()
