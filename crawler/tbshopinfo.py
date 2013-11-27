#!/usr/bin/env python
# -*- coding: utf-8 -*-
from h5 import get_shop as get_shop_h5, get_misc
import json

def get_shop(shopid):
    s = get_shop_h5(shopid)
    if s:
        s.update(get_misc(shopid, sid=s['sid'], type=s['type']))
    return s

def main():
    import argparse
    from pprint import pprint
    parser = argparse.ArgumentParser(description='Get shopinfo by shopid')
    parser.add_argument('--shopid', '-s', type=int, help='taobao shopid, e.g. 33003356', required=True)
    option = parser.parse_args()
    pprint(get_shop(option.shopid)) 

if __name__ == '__main__':
    main()
