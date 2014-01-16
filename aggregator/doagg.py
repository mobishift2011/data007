#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import pymongo

from datetime import datetime, timedelta

from aggregator import iap, sap, bap, cap, shp, iip, tap, sep, bep, all_processes
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex, clear_date
from aggregator.agghosts import getconn
from aggregator.models import getdb

defaultdate = (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")

def allocate_instances(num=0):
    db = pymongo.MongoClient().taobao
    db.e_c2__schd.update({'name':'taobao_aggregate'}, {'$set':{'instance_num':num}})

def clearall(date):
    db = getdb('db1')
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
    db = getdb('db1')
    db.execute('insert into ataobao2.agghosts (datestr, ready) values (:date, true)',
                dict(date=date))

def save_redis(date):
    for conn in getconn(date).conns:
        print 'bgsave on {}'.format(conn)
        conn.bgsave()

def main():
    parser = argparse.ArgumentParser(description='Aggregation Controller')
    parser.add_argument('--date', '-d', help='the date to aggregate, must be format of YYYY-MM-DD')
    parser.add_argument('--instance-num', '-n', default=0, help='the number of instances should be used')
    option = parser.parse_args()
    if option.date:
        date = option.date
    else:
        date=(datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")
    clearall(date)
    allocate_instances(option.instance_num)
    flow = build_flow(date)
    flow.start()
    allocate_instances(0)
    mark_ready(date)
    try:
        save_redis(date)
    except:
        pass

if __name__ == '__main__':
    main()
