#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggres import ShopIndex

from datetime import datetime, timedelta
from bisect import bisect

from crawler.cates import cates

import traceback

credits = [ 4, 11, 41, 91, 151, 
            251, 501, 1001, 2001, 5001, 
            10001, 20001, 50001, 100001, 200001,
            500001, 1000001, 2000001, 5000001, 10000001, ]

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

def aggregate_items(token_start, token_end, date=datetime.utcnow()+timedelta(hours=8), on_finish_item=None, on_finish=None):
    date2 = datetime(date.year, date.month, date.day)
    d1 = (date2 - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        si = ShopIndex(d1)
        si.multi()
        with db.connection() as cur:
            cur.execute('''select id, shopid, cid, num_sold30, price from ataobao2.item where token(id)>=:start and token(id)<:end''', 
                    dict(start=int(token_start), end=int(token_end)), consistency_level='ONE')
            for row in cur:
                itemid, shopid, cid, nc, price = row
                if nc > 0:
                    try:
                        aggregate_item(si, itemid, shopid, cid, price, date, on_finish_item)
                    except:
                        traceback.print_exc()
        si.execute()
    except:
        traceback.print_exc()

    if on_finish:
        on_finish('item', d1, token_start, token_end)

def aggregate_item(si, itemid, shopid, cid, price, date, on_finish_item=None):
    date2 = datetime(date.year, date.month, date.day)
    date1 = date2 - timedelta(days=60)
    d1 = (date2 - timedelta(days=1)).strftime("%Y-%m-%d")
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

        #print('updating item {} to {}'.format(itemid, 'ataobao_'+d1))
        si.addcates(shopid, l1, l2)
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
        si.addshop(shopid)

    if on_finish_item:
        on_finish_item(itemid)

def aggregate_shops(start, end, date=datetime.utcnow()+timedelta(hours=8), on_finish_shop=None, on_finish=None):
    date2 = datetime(date.year, date.month, date.day)
    d1 = (date2 - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        si = ShopIndex(d1)
        si.multi()
        with db.connection() as cur:
            cur.execute('''select id, title, logo, rank_num from ataobao2.shop
                    where token(id)>=:start and token(id)<:end''',
                    dict(start=start, end=end), consistency_level='ONE')
            for row in cur:
                shopid, name, logo, rank_num = row
                try:
                    aggregate_shop(si, shopid, name, logo, rank_num, on_finish_shop)
                except:
                    traceback.print_exc()
        si.execute()
    except:
        traceback.print_exc()

    if on_finish:
        on_finish('shop', d1, start, end)

def aggregate_shop(si, shopid, name, logo, rank_num, on_finish_shop):
    shopinfo = si.getbase(shopid)
    if shopinfo:
        active_index = float(shopinfo['active_index_mon'])
        sales = float(shopinfo['sales_mon'])
        credit_score = bisect(credits, rank_num)
        worth = 2**credit_score + active_index/3000. + sales/30.
        update = {'name':name, 'logo':logo, 'credit_score':credit_score, 'worth':worth}
        si.setbase(shopid, update)

        def update_with_cates(cate1, cate2):
            for mod in ['mon', 'day']:
                shopinfo = si.getinfo(cate1, cate2, mod, shopid)
                for field in ['sales', 'deals', 'active_index']:
                    shopinfo[field] = float(shopinfo[field])
                score = shopinfo['active_index']/1000. + shopinfo['sales']/30.
                update = {'credit_score':credit_score, 'worth':worth, 'score':score}
                si.setinfo(cate1, cate2, mod, shopid, update) 
                shopinfo.update(update)
                for field in ['sales', 'deals', 'active_index', 'credit_score', 'worth', 'score']:
                    if shopinfo[field] > 0:
                        si.setindex(cate1, cate2, field, mod, shopid, shopinfo[field])
    
        cates = si.getcates(shopid)
        c1s = list(set([c[0] for c in cates]))
        for c1 in c1s:
            update_with_cates(c1, 'all')
        for cate1, cate2 in cates:
            update_with_cates(cate1, cate2)

    if on_finish_shop:
        on_finish_shop(shopid)

if __name__ == '__main__':
    pass
    #step = 2**64/1000
    #for start in range(-2**63, 2**63-1, step):
    #    end = start + step
    #    aggregate_items(start, end)
    #aggregate_shops(0, 1000)
