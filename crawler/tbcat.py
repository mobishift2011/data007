#!/usr/bin/env python
# -*- coding: utf-8 -*-
from gevent import monkey; monkey.patch_all()
import gevent
import gevent.pool

import re
import time
import random
import traceback
from itertools import chain
from functools import partial

from session import get_session, get_blank_session

def get_count(data):
    """ get totalNumber from taobao's json return """
    if data:
        total = data['selectedCondition']['totalNumber']
        return 9500 if u'万' in total else int(total)
    else:
        return 0

def get_ids(data):
    if data and data['itemList']:
        return [ int(i['itemId']) for i in data['itemList'] ]
    else:
        return []

def get_subcats(data):
    if data['cat']:
        if data['cat']['hasGroup'] == 0:
            return [int(d['value']) for d in data['cat']['catList']]
        else:
            cids = []
            for l in data['cat']['catGroupList']:
                for d in l['catList']:
                    cids.append(int(d['value']))
            return cids
    else:
        return []
    
def get_json(cid, paths=[], page=1, sort=None):
    """ given cid and (optional) paths/page/sort, return json """
    s = get_blank_session()
    url = 'http://list.taobao.com/itemlist/default.htm?'
    params = {
        'pSize': 95,
        'json': 'on',
    }
    if cid:
        params['cat'] = cid
    if paths:
        paths = [p for p in paths if p]
        params['ppath'] = ';'.join(paths)
    if sort:
        params['sort'] = sort
    if page > 1:
        params['s'] = (page-1)*95

    try:
        data = s.get(url, params=params, timeout=30).json()
    except:
        data = None
    return data


def list_cat(cid=None, sort=None, on_ids=None, use_pool=False, max_page=10, num_paths=2):
    """ listing category by cid, find all item ids, callback on ``on_ids`` 
       
    :param cid: taobao category id, can be rootcid or leafcid or None(listing all)
    :on_ids: callback for batch ids
    :returns: a list of item ids according to keyword context
    """
    if use_pool:
        catpool = gevent.pool.Pool(100)
        pathpool = gevent.pool.Pool(100)
    else:
        catpool = None
        pathpool = None

    ids = []
    def list_paths(paths, page=1, data=None, cid=cid):
        if data is None:
            data = get_json(cid, paths, page, sort=sort)
       
        iids = get_ids(data)
        ids.extend(iids)
        if on_ids:
            try:
                print('found {} items (cid={}, ppath={} page={})'.format(len(iids), cid, ';'.join(paths), page))
                on_ids(iids)
            except:
                traceback.print_exc()
        else:
            print('found {} items (cid={}, ppath={} page={})'.format(len(iids), cid, ';'.join(paths), page))

        if page == 1:
            count = get_count(data)
            for p in range(2, min(2+count/95, max_page+1)):
                if pathpool is not None:
                    pathpool.spawn(list_paths, paths, p, cid=cid)
                else:
                    list_paths(paths, p, cid=cid)
        
    list_cat_paths(cid, pool=catpool, on_paths=list_paths, num_paths=num_paths)

    if use_pool:
        catpool.join()
        pathpool.join()
    return list(set(ids))

def list_cat_paths(cid, depth=0, paths=[], allpath=[], pool=None, num_paths=2, on_paths=None, sort=None):
    """ try filter category by paths, and list all paths have less than 9500 items
    
    :param cid: category id
    :param depth: current paths depth
    :param paths: current paths
    :param allpath: a full list of ppaths
    :param pool: gevent pool for concurrency
    :param num_paths: total paths combination used
    :on_paths: callback when an appropriate paths is decided
    """
    def should_digg(data):
        if data:
            total = data['selectedCondition']['totalNumber']
            return u'万' in total or int(total)>9500
        else:
            return False

    data = get_json(cid, paths, sort=sort)
    if depth == 0 and paths == [] and allpath == [] and data and data['cat']:
        cids = get_subcats(data)
        random.shuffle(cids)
        for scid in cids:
            list_cat_paths(scid, pool=pool, on_paths=on_paths)

    if allpath == [] and data and data['propertyList']:
        allpath = [ [p2['value'] for p2 in p1['propertyList']] for p1 in data['propertyList'] ]
        allpath = sorted(allpath, key=len, reverse=True)[:num_paths]
        paths = [''] * len(allpath)

    if depth<len(paths) and should_digg(data): 
        for ppath in chain(allpath[depth], ['']):
            paths[depth] = ppath
            if pool is not None:
                pool.spawn(list_cat_paths, cid, depth+1, list(paths), allpath, on_paths=on_paths)
            else:
                list_cat_paths(cid, depth+1, paths, allpath, on_paths=on_paths)
    else:
        if on_paths is None:
            print(paths)
        else:
            try:
                on_paths(paths, data=data, cid=cid)
            except:
                traceback.print_exc()

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Listing ids of a (leaf) category')
    parser.add_argument('--cid', '-c', type=int, help='taobao cid, e.g. 51106012', required=True)
    parser.add_argument('--pool', '-p', action='store_true', help='use gevent pool to boost execution')
    option = parser.parse_args()
    print('total items: {}'.format(len(test_list(option.cid, option.pool))))

def test_list(cid, use_pool=False):
    allids = set()
    def on_ids(ids):
        allids.update(ids)
        print('total ids: {}'.format(len(allids)))
    
    list_cat(cid, on_ids, use_pool=use_pool)

if __name__ == '__main__':
    main()
