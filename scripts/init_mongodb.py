#!/usr/bin/env python
from models import mdb
from crawler.cates import cates

l1l2 = set()
for cid in cates.keys():
    cidchain = []
    while cates[cid] != 0:                 
        cidchain.append(cid)
        cid = cates[cid]
    cidchain.append(cid)
    if len(cidchain) == 2:
        l1l2.add( (cidchain[-2], cidchain[-1]) )

print('total l1l2: {}'.format(len(l1l2)))

for l1, l2 in l1l2:
    for postfix in ['mon', 'day']:
        for tablename in ['shop_{}'.format(l1), 'shop_{}_{}'.format(l1, l2)]:
            tablename = '{}_{}'.format(tablename, postfix)
            print("ensure_index for table {}".format(tablename))
            for field in ['score', 'mon_sales', 'mon_deals', 'day_sales', 'day_deals', 'active_index', 'worth', 'credit_score']:
                mdb[tablename].ensure_index([(field, 1)])
