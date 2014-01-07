#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
from datetime import datetime, timedelta

from models import db
from aggregator import iap, sap, bap, cap, shp, iip, tap, sep, bep, all_processes
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex, clear_date

defaultdate = (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")

def clearall(date):
    for p in all_processes:
        p.clear_redis()

    db.execute('delete from ataobao2.agghosts where datestr=:date', dict(date=date))
    clear_date(date)

    r = db.execute('select datestr, ready from ataobao2.agghosts', result=True)
    ahs = sorted(r.results) 
    try:
        last = [ x[0] for x in ahs if x[1] ][-1]
    except:
        last = date
    for d, ready in ahs:
        if d < last:
            db.execute('delete from ataobao2.agghosts where datestr=:date', dict(date=d))

    db.execute('delete from ataobao2.blacklist where type=\'shopblacknew\';')

def build_flow(date=defaultdate):
    for p in all_processes:
        p.date = date

    iap.add_child(sap)
    iap.add_child(iip)
    sap.add_child(bap)
    sap.add_child(shp)
    sap.add_child(cap)

    bap.add_child(tap)
    shp.add_child(tap)
    cap.add_child(tap)
    iip.add_child(tap)

    sap.add_child(sep)
    bap.add_child(bep)

    return iap

def mark_ready(date):
    db.execute('insert into ataobao2.agghosts (datestr, ready) values (:date, true)',
                dict(date=date))

def main():
    parser = argparse.ArgumentParser(description='Aggregation Controller')
    parser.add_argument('--date', '-d', help='the date to aggregate, must be format of YYYY-MM-DD')
    option = parser.parse_args()
    if option.date:
        date = option.date
    else:
        date=(datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")
    clearall(date)
    flow = build_flow(date)
    flow.start()
    mark_ready(date)

if __name__ == '__main__':
    main()
