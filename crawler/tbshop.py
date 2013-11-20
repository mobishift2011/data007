#!/usr/bin/env python
# -*- coding: utf-8 -*-
from crawler.h5 import get_shopitems

def list_shop(id, on_ids=None):
    """ listing shop by id, find all item ids, callback on ``on_ids`` 
       
    :param id: taobao shop id
    :on_ids: callback for batch ids, this is the prefered callback
    :returns: a list of item ids in this shop
    """
    ids = get_shopitems(id)
    if on_ids:
        on_ids(ids)
    return ids

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Listing Ids in Shop')
    parser.add_argument('--shopid', '-s', type=int, help='taobao shopid, e.g. 33003356', required=True)
    option = parser.parse_args()
    print('total items: {}'.format(len(list_shop(option.shopid))))

if __name__ == '__main__':
    main()
