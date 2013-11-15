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
                if len(cidchain) == 1:
                    l1l2 = [cid, 'all']
    return l1l2

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def aggregate_items(start, end, date=None):
    try:
        if date is None:
            date = defaultdate
        date2 = datetime.strptime(date, "%Y-%m-%d")+timedelta(hours=16)
        date1 = date2 - timedelta(days=60)
        si = ShopIndex(date)
        ii = ItemIndex(date)
        bi = BrandIndex(date)
        ci = CategoryIndex(date)
        si.multi()
        ii.multi()
        bi.multi()
        ci.multi()

        iteminfos = db.execute('''select id, shopid, cid, num_sold30, price, brand, title, image 
                    from ataobao2.item where token(id)>=:start and token(id)<:end''',
                    dict(start=int(start), end=int(end)), result=True).results 
        itemts = db.execute('''select id, date, num_collects, num_reviews, num_sold30, num_views from ataobao2.item_by_date 
                    where token(id)>=:start and token(id)<:end and date>=:date1 and date<:date2 allow filtering''',
                    dict(start=int(start), end=int(end), date1=date1, date2=date2), result=True).results

        itemtsdict = {}
        for row in itemts:
            itemid, date, values = row[0], (row[1]+timedelta(hours=8)).strftime("%Y-%m-%d"), row[2:]
            if itemid not in itemtsdict:
                itemtsdict[itemid] = {}
            itemtsdict[itemid][date] = values

        for itemid, shopid, cid, nc, price, brand, name, image in iteminfos:
            if brand == '' or brand is None:
                brand = u'其他'
            if nc > 0 and itemid in itemtsdict and itemtsdict[itemid]:
                try:
                    aggregate_item(si, ii, bi, ci, itemid, itemtsdict[itemid], shopid, cid, price, brand, name, image, date)
                except:
                    traceback.print_exc()

        si.execute()
        bi.execute()
        ci.execute()
        ii.execute()
    except:
        traceback.print_exc()


def parse_iteminfo(date, itemid, items, price, cid):
    if not items:
        return

    date2 = datetime.strptime(date, "%Y-%m-%d")+timedelta(hours=16)
    date1 = date2 - timedelta(days=60)
    d1 = date
    d2 = (date2 - timedelta(days=2)).strftime("%Y-%m-%d")
    d3 = (date2 - timedelta(days=3)).strftime("%Y-%m-%d")
    d31 = (date2 - timedelta(days=31)).strftime("%Y-%m-%d")
    d32 = (date2 - timedelta(days=32)).strftime("%Y-%m-%d")
    d61 = (date2 - timedelta(days=61)).strftime("%Y-%m-%d")
    d62 = (date2 - timedelta(days=62)).strftime("%Y-%m-%d")
    if d1 not in items:
        items[d1] = items[sorted(items.keys())[-1]]
        
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

    return locals()


def aggregate_item(si, ii, bi, ci, itemid, items, shopid, cid, price, brand, name, image, date):
    info = parse_iteminfo(date, itemid, items, price, cid)
    if not info:
        return 

    for key, value in info.items():
        locals()[key] = value
        globals()[key] = value

    brand = brand.encode('utf-8')

    # inc category counters
    for mod in ['day', 'mon']:
        inc = {
            'sales': locals()['sales_'+mod],
            'deals': locals()['deals_'+mod],
            'delta_sales': locals()['delta_sales_'+mod],
            'items': 1,
        }
        ci.incrinfo(l1, l2, mod, inc)
        if l2 != 'all':
            ci.incrinfo(l1, 'all', mod, inc)
    ci.addbrand(l1, l2, brand)
    if l2 != 'all':
        ci.addbrand(l1, 'all', brand)

    # inc brand counters
    bi.addbrand(brand)
    bi.addshop(brand, l1, l2, shopid)
    bi.addcates(brand, l1, l2)
    if l2 != 'all':
        bi.addcates(brand, l1, 'all')
    bi.addhots(brand, l2, itemid, shopid, sales_mon)
    inc = {
        'items': 1,
        'deals': deals_mon,
        'sales': sales_mon,
        'delta_sales': delta_sales_mon,
    }
    bi.incrinfo(brand, l1, l2, inc)
    if l2 != 'all':
        bi.incrinfo(brand, l1, 'all', inc)

    # inc item counters
    ii.incrcates(l1, l2, sales_mon, deals_mon)
    if l2 != 'all':
        ii.incrcates(l1, 'all', sales_mon, deals_mon)
    ii.incrindex(l1, l2, 'sales', 'mon', itemid, sales_mon)
    if l2 != 'all':
        ii.incrindex(l1, 'all', 'sales', 'mon', itemid, sales_mon)
    ii.incrindex(l1, l2, 'sales', 'day', itemid, sales_day)
    if l2 != 'all':
        ii.incrindex(l1, 'all', 'sales', 'day', itemid, sales_day)

    # inc shop counters
    if l2 != 'all':
        si.addcates(shopid, l1, l2)
    si.incrbrand(shopid, 'sales', brand, sales_mon)
    si.incrbrand(shopid, 'deals', brand, deals_mon)
    si.addhotitems(shopid, itemid, sales_mon)

    cate1 = l1
    for cate2 in set(['all', l2]):
        for period in ['mon', 'day']:
            inc = {'sales':locals()['sales_'+period],
                   'deals':locals()['deals_'+period],
                   'delta_sales': locals()['delta_sales_'+period],
                   'active_index': locals()['active_index_'+period],
                   'delta_active_index': locals()['delta_active_index_'+period]}
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
    iap.date = '2013-11-11'
    iap.start()
