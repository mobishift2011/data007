#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator import iap, sap, bap, cap, shp
from datetime import datetime, timedelta

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

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
    flow = build_flow()
    flow.start()

if __name__ == '__main__':
    main()
