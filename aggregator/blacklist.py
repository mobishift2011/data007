#!/usr/bin/env python
""" Blacklist Item from our Aggregation Process """
from models import db

bl_shopids = [row[0] for row in db.execute('select id from ataobao2.blacklist', result=True).results ]

thresholds = {
}

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

def in_blacklist(shopid, price, cid, num_sold30, num_reviews, credit_score):
    if shopid in bl_shopids:
        return True

    l1l2 = get_l1_and_l2(cid)
    if price >= thresholds.get(l1l2, 50000):
        return True

    if num_sold30*price >= 1000000 and credit_score <= 10:
        return True

    if num_sold30*price >= 100000:
        if num_reviews == 0 and num_sold30>=3000:
            return True
        if num_reviews>0 and num_sold30/num_reviews >= 50:
            return True

    return False 
     
