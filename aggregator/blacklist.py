#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Blacklist Item from our Aggregation Process """
from models import db

bl_shopblackids = set()
bl_shopwhiteids = set()
bl_thresholds = {}

def load_bls():
    global bl_shopblackids
    global bl_shopwhiteids
    global bl_thresholds
    bls = set([row for row in db.execute('select type, args, value from ataobao2.blacklist', result=True).results ])
    bl_shopblackids = set(int(row[1]) for row in bls if row[0] == 'shopblack')
    bl_thresholds = {row[1]:float(row[2]) for row in bls if row[0] == 'cateprice'}
    bl_shopwhiteids = set(int(row[1]) for row in bls if row[0] == 'shopwhite')

load_bls()

def get_l1_and_l2(cid):
    from crawler.cates import cates
    if cid in cates:
        cidchain = []
        while cates[cid] != 0:
            cidchain.append(cid)
            cid = cates[cid]
        cidchain.append(cid)
        try:
            return cidchain[-1], cidchain[-2]
        except:
            if len(cidchain) == 1:
                    return cid, 'all'

def in_blacklist(shopid, price, cid, num_sold30, num_reviews, credit_score, title, type, use_blacklist=True, itemid=None):
    global bl_shopblackids
    global bl_shopwhiteids
    global bl_thresholds
    ib = False
    new = True
    if type == 'tmall':
        ib = False

    elif int(shopid) in bl_shopwhiteids:
        ib = False

    elif use_blacklist and int(shopid) in bl_shopblackids:
        ib = True
        new = False

    else:
        l1l2 = get_l1_and_l2(cid) or 'all_all'
        tprice = bl_thresholds.get('{}_{}'.format(l1l2[0], l1l2[1]), 500000)
        if price >= min(max(tprice, 1000), 500000):
            ib = True

        elif num_sold30*price >= 5000000 and num_sold30 > 1000 and credit_score <= 8:
            ib = True

        elif num_sold30*price >= 500000:
            if num_reviews == 0 and num_sold30 >= 5000:
                ib = True
            elif num_reviews == 0 and num_sold30*price >= 2000000:
                ib = True
            elif num_reviews > 0 and num_sold30/num_reviews >= 100 and num_sold30*price>=1000000:
                for kw in [u'预定', u'预订', u'定金', u'订金']:
                    if kw in title:
                        ib = False
                        break
                else:
                    ib = True

    if ib and new:
        db.execute('insert into ataobao2.blacklist (type, args, value) values (:type, :args, :value)',
                    dict(type='shopblack', args=str(shopid), value=str(itemid)))
        db.execute('insert into ataobao2.blacklist (type, args, value) values (:type, :args, :value)',
                    dict(type='shopblacknew', args=str(shopid), value=str(itemid)))
        bl_shopblackids.add(int(shopid))

    return ib
