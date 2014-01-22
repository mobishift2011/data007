#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import traceback
import argparse
import pymongo

from datetime import datetime, timedelta

from aggregator import iap, sap, bap, cap, shp, iip, tap, sep, bep, all_processes
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex, clear_date
from aggregator.agghosts import getconn
from aggregator.models import getdb

from settings import ENV

defaultdate = (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")

def allocate_instances(num=0):
    if ENV != 'DEV':
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
        print 'save on {}'.format(conn)
        conn.save()

def doagg(option):
    try:
        date = option.date
        instance_num = option.instance_num
        clearall(date)
        allocate_instances(instance_num)
        flow = build_flow(date)
        flow.start()
        allocate_instances(0)
        mark_ready(date)
        try:
            save_redis(date)
        except:
            pass
    except:
        traceback.print_exc()

def doagg_daily(option):
    offset = 8 
    while True:
        d = datetime.utcnow() + timedelta(hours=offset)
        try:
            if d.hour == 0 and d.minute == 0:
                print 'runing doagg for {}'.format(d)
                option.date = (d - timedelta(days=1)).strftime("%Y-%m-%d")
                doagg(option)
        except:
            traceback.print_exc()
        finally:
            to_sleep = 90 - d.second
            print 'sleeping', to_sleep, 'secs...'
            time.sleep(to_sleep)

def main():
    parser = argparse.ArgumentParser(description='Aggregation Controller')
    parser.add_argument('--date', '-d', help='the date to aggregate, must be format of YYYY-MM-DD')
    parser.add_argument('--instance-num', '-n', default=7, help='the number of instances should be used')
    parser.add_argument('--mode', '-m', default='daily', choices=['onepass', 'daily', 'clear'], help='one pass aggregation')
    option = parser.parse_args()
    if option.date:
        date = option.date
    else:
        date=(datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")
    option.date = date

    if option.mode == 'onepass':
        doagg(option)
    elif option.mode == 'clear':
        clearall(option.date)
    elif option.mode == 'daily':
        doagg_daily(option)

if __name__ == '__main__':
    main()
