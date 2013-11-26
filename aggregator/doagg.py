#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from aggregator import iap, sap, bap, cap, shp, iip, tap, all_processes
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex
from datetime import datetime, timedelta

defaultdate = (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")

def clearall(date):
    for p in all_processes:
        p.clear_redis()

    ShopIndex(date).clear()
    ItemIndex(date).clear()
    BrandIndex(date).clear()
    CategoryIndex(date).clear()

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
    
    return iap

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

if __name__ == '__main__':
    main()
