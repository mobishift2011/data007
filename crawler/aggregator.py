#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db, mdb
from caches import LC

from datetime import datetime, timedelta
from bisect import bisect

from crawler.cates import cates

credits = [ 4, 11, 41, 91, 151, 
            251, 501, 1001, 2001, 5001, 
            10001, 20001, 50001, 100001, 200001,
            500001, 1000001, 2000001, 5000001, 10000001, ]

def aggregate_shop(shopid, date=datetime.utcnow()+timedelta(hours=8)):
    date2 = datetime(date.year, date.month, date.day)
    date1 = date2 - timedelta(days=1)
    date0 = date2 - timedelta(days=2)
    datep = date2 - timedelta(days=3)
    date60 = date2 - timedelta(days=60)
    si = db.execute('''select id, date, iid from ataobao2.shop_by_item 
                        where id=:shopid and date>=:datep and date<:date2''',
                dict(shopid=shopid, datep=datep, date2=date2), result=True)

    # if there is no info about the provided shopid
    # we do nothing
    if not si.results:
        return 0

    itemids = set(r[2] for r in si.results)
    if len(itemids) <= 1:
        return 0

    cids = db.execute('''select id, cid from ataobao2.item where id in :ids''', dict(ids=tuple(itemids)), result=True)
    items = db.execute('''select id, date, price, num_sold30, num_collects, num_reviews, num_views from ataobao2.item_by_date
                          where id in :ids and date>=:datep and date<:date2''',
                    dict(ids=tuple(itemids), datep=datep, date2=date2), result=True)
    shop = db.execute('''select title, logo, rank_num from ataobao2.shop where id=:shopid''', 
                        dict(shopid=shopid), result=True) 


    ciddict = dict(cids.results)

    item_metrics = calculate_item_metrics(items.results)
    plans = calculate_aggregations(ciddict, item_metrics, shopid, shop)
    if plans:
        insert_plans(plans) 
        return plans['shop_base']['sales']
    else:
        return 0

def insert_plans(plans):
    for pname in plans:
        print('insert into {}: {}'.format(pname, plans[pname]))
        mdb[pname].save(plans[pname]) 

def calculate_aggregations(ciddict, item_metrics, shopid, shop):
    cids = ciddict.values()
    l1l2 = get_l1_and_l2_cids(cids)
    plans = {}
    for itemid in item_metrics:
        m = item_metrics[itemid]
        try:
            cid = ciddict[itemid]
        except:
            pnames = ['shop_base']
        else:
            pnames = ['shop_{}_mon'.format(l1l2[cid][0]), 'shop_{}_{}_mon'.format(l1l2[cid][0], l1l2[cid][1]), 'shop_base']
        for pname in pnames:
            if pname not in plans:
                plans[pname] = {
                    '_id': shopid,
                    'active_index': m['active_index'],
                    'delta_active_index': m['delta_active_index'],
                    'deals': m['deals'],
                    'delta_sales': m['delta_sales'],
                    'sales': m['price']*m['deals'],
                }
            else:
                plans[pname]['active_index'] += m['active_index']
                plans[pname]['delta_active_index'] += m['delta_active_index']
                plans[pname]['deals'] += m['deals']
                plans[pname]['delta_sales'] += m['delta_sales']
                plans[pname]['sales'] += m['price'] * m['deals']

    if plans:
        pname = 'shop_base'
        plans[pname]['worth'] = 10 * (plans[pname]['active_index']/1000. + plans[pname]['sales']/30.*0.3)
        if shop.results:
            plans[pname]['name'] = shop.results[0][0]
            plans[pname]['logo'] = shop.results[0][1]
            plans[pname]['credit_score'] = bisect(credits, shop.results[0][2])
        else:
            return {}

    for pname in plans:
        plans[pname]['score'] = plans[pname]['active_index']/1000. + plans[pname]['sales']/30.*0.3
        for field in ['worth', 'credit_score', 'active_index']:
            plans[pname][field] = plans['shop_base'][field]
    return plans
       
   
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

def calculate_item_metrics(items):
    itemdate = {}
    ids = set()
    metrics = {}
    for id, date, price, num_sold30, num_collects, num_reviews, num_views in items:
        date = date.strftime("%Y-%m-%d")
        if date not in itemdate:
            itemdate[date] = {}
        itemdate[date][id] = (price, num_sold30, num_collects, num_reviews, num_views)
        ids.add(id)

    dates = sorted(itemdate.keys())

    try:
        d1, d2, d3 = dates
    except:
        return {}

    # fixing data
    for id in ids:
        if id in itemdate[d1]:
            if id not in itemdate[d2]:
                itemdate[d2][id] = itemdate[d1][id] 
            if id not in itemdate[d3]:
                itemdate[d3][id] = itemdate[d1][id] 
        if id in itemdate[d2]:
            if id not in itemdate[d3]:
                itemdate[d3][id] = itemdate[d2][id]
            if id not in itemdate[d1]:
                itemdate[d1][id] = itemdate[d2][id]
        if id in itemdate[d3]:
            if id not in itemdate[d1]:
                itemdate[d1][id] = itemdate[d3][id]
            if id not in itemdate[d2]:
                itemdate[d2][id] = itemdate[d3][id]

    # do calc
    for id in ids: 
        data1, data2, data3 = itemdate[d1][id], itemdate[d2][id], itemdate[d3][id]
        active_index = (data3[2] - data2[2])*50 + (data3[3] - data2[3])*10 + (data3[4] - data2[4])
        delta_active_index = active_index - ((data2[2] - data1[2])*50 + (data2[3] - data1[3])*10 + (data2[4] - data1[4]))
        deals = data3[1]
        delta_sales = data3[0]*data3[1] - data2[0]*data2[1]
        metrics[id] = dict(active_index=active_index, delta_active_index=delta_active_index, deals=deals, delta_sales=delta_sales, price=price)
    return metrics

def aggregate_items(token_start, token_end, date=datetime.utcnow()+timedelta(hours=8)):
    with db.connection() as cur:
        cur.execute('''select id, shopid, cid, num_sold30, price from ataobao2.item where token(id)>=:start and token(id)<:end''', 
                    dict(start=token_start, end=token_end), consistency_level='ONE')
        for row in cur:
            itemid, shopid, cid, nc, price = row
            if nc > 0:
                aggregate_item(itemid, shopid, cid, price, date)

def aggregate_item(itemid, shopid, cid, price, date):
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
    if d1 in items:
        l1, l2 = get_l1_and_l2_cids([cid])[cid]
        i1 = items[d1]
        i2 = items.get(d2, i1)
        i3 = items.get(d3, i2)
        i31 = items.get(d31, i1)
        i32 = items.get(d32, i2)
        i61 = items.get(d61, i31)
        i62 = items.get(d62, i32)
        active_index_day = (i1[1]-i2[1])*50 + (i1[0]-i2[0])*10 + (i1[3]-i2[3])
        delta_active_index_day = active_index_day - (i2[1]-i3[1])*50 - (i2[0]-i3[0])*10 - (i2[3]-i3[3])
        active_index_mon = (i1[1]-i31[1])*50 + (i1[0]-i31[0])*10 + (i1[3]-i31[3])
        delta_active_index_mon = active_index_mon - (i31[1]-i61[1])*50 - (i31[0]-i61[0])*10 - (i31[3]-i61[3])
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

        for cate in [str(l1), str(l1) + '_' + str(l2)]:
            for period in ['_mon', '_day']:
                inc = {'sales':locals()['sales'+period],
                       'deals':locals()['deals'+period],
                       'delta_sales': locals()['delta_sales'+period],
                       'active_index': locals()['active_index'+period],
                       'delta_active_index': locals()['delta_active_index'+period]}
                mdb['shop_'+cate+period].update({'_id':shopid}, {'$inc':inc})

if __name__ == '__main__':
    #print aggregate_shop(102603268)
    aggregate_items(0, 2**46)
