#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator import iap, sap, bap, cap, shp
from aggregator.indexes import ShopIndex, ItemIndex, BrandIndex, CategoryIndex
from datetime import datetime, timedelta

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def clearall(date=None):
    if date is None:
        date = defaultdate

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
    date = (datetime.utcnow()+timedelta(hours=8)).strftime("%Y-%m-%d")
    flow = build_flow(date)
    flow.start()

if __name__ == '__main__':
    clearall(date='2013-11-11')
    main()
