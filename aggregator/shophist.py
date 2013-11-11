#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import ShopIndex
from aggregator.processes import Process

from datetime import datetime, timedelta

import json
import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def save_history_shops(start, end, date=None):
    try:
        if date is None:
            date = defaultdate
        si = ShopIndex(date)
        si.multi()
        with db.connection() as cur:
            cur.execute('''select id, num_collects from ataobao2.shop
                    where token(id)>=:start and token(id)<:end''',
                    dict(start=start, end=end), consistency_level='ONE')
            for row in cur:
                shopid, num_collects = row
                try:
                    save_history_shop(si, date, shopid, num_collects)
                except:
                    traceback.print_exc()
        si.execute()
    except:
        traceback.print_exc()

def save_history_shop(si, date, shopid, num_collects):
    shopinfo = si.getbase(shopid)
    if shopinfo:
        worth = float(shopinfo.get('worth', 0))
        rank = {}
        cates = si.getcates(shopid)
        c1s = list(set([c[0] for c in cates]))
        for c1 in c1s:
            rank[c1] = si.getrank(c1, 'all', shopid)
        db.execute('''insert into ataobao2.shop_by_date (id, date, worth, rank, num_collects) values
                    (:shopid, :date, :worth, :rank, :num_collects)''', 
                    dict(worth=worth, rank=json.dumps(rank), num_collects=num_collects, shopid=shopid, date=date))

class ShopHistProcess(Process):
    def __init__(self, date=None):
        super(ShopHistProcess, self).__init__('shophist')
        self.step = 2**64/100
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        count = 0
        for start in range(-2**63, 2**63, self.step):
            end = start + self.step
            if end > 2**63-1:
                end = 2**63-1
            self.add_task('aggregator.shophist.save_history_shops', start, end, date=self.date)
        self.finish_generation()

shp = ShopHistProcess()

if __name__ == '__main__':
    shp.start()
