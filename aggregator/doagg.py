#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse

from aggregator import iap, sap, bap, cap, shp
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex
from datetime import datetime, timedelta

def clearall(date):
    for p in [iap, sap, bap, cap, shp]:
        p.clear_redis()

    ShopIndex(date).clear()
    ItemIndex(date).clear()
    BrandIndex(date).clear()
    CategoryIndex(date).clear()

def build_flow(date=None):
    if date is None:
        date = defaultdate

    for p in [iap, sap, bap, cap, shp]:
        p.date = date

    iap.add_child(sap)
    sap.add_child(bap)
    sap.add_child(shp)
    sap.add_child(cap)

    return iap

def main():
    parser = argparse.ArgumentParser(description='Aggregation Controller')
    parser.add_argument('--date', '-d', help='the date to aggregate, must be format of YYYY-MM-DD')
    option = parser.parse_args()
    if option.date:
        date = option.date 
    else:
        date='2013-11-11'
    clearall(date)
    flow = build_flow(date)
    flow.start()

if __name__ == '__main__':
    main()
