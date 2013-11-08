#!/usr/bin/env python
# -*- coding: utf-8 -*-
from aggregator import iap, sap, bap, cap

def build_flow():
    iap.add_child(sap)
    sap.add_child(bap)
    sap.add_child(cap)
    return iap

def main():
    flow = build_flow()
    flow.start()

if __name__ == '__main__':
    main()
