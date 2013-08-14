#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import traceback
from session import get_session

def list_shop(id, on_ids=None):
    """ listing shop by id, find all item ids, callback on ``on_ids`` 
       
    :param id: taobao shop id
    :on_ids: callback for batch ids, this is the prefered callback
    :returns: a list of item ids in this shop
    """
    return _list_shop(id, page=1, on_ids=on_ids)

def _list_shop(id, page=1, on_id=None, on_ids=None):
    """ listing shop by id, find all item ids, callback on ``on_ids`` 
       
    :param id: taobao shop id
    :param page: shop listing page number
    :on_ids: callback for batch ids
    :returns: a list of item ids according to keyword context
    """
    s = get_session()
    patpages = [
        re.compile(r'<span class="page-info">1/(\d+)</span>'),
        re.compile(r'<b class="ui-page-s-len">1/(\d+)</b>'),
    ]
    patids = [
        re.compile(r'<dl class="item[^"]+" data-id="(\d+)"'),
        re.compile(r'item\.htm\?id=(\d+)'),
    ]
    url = 'http://shop{}.taobao.com/search.htm?search=y&pageNum={}&orderType=hotsell_desc'.format(id, page)

    try:
        # sometimes taobao will return empty page because of high load
        # if that happens, we need to refetch the content 1 second later
        ids = []
        while True:
            content = s.get(url, timeout=30).content
            ids = set(patids[0].findall(content)) or set(patids[1].findall(content))
            ids = [ int(x) for x in ids ]
            if ids:
                break
            time.sleep(1)

        if on_ids:
            try:
                on_ids(ids)
            except:
                traceback.print_exc()
        else:
            print('shop {} found {} items on page {}'.format(id, len(ids), page))
    except:
        traceback.print_exc()    
        return []
    else:
        if page > 1:
            return ids
        else:
            # now that it is the first page
            # first, we figure out how many pages does this shop have
            # second, aggregate ids from page 2 ~ page end
            for pat in patpages:
                try:
                    pages = int(pat.search(content).group(1))
                except:
                    continue
                else:
                    break
            else:
                return ids
            for p in range(2, min(100, pages+1)):
                ids.extend( _list_shop(id, p, on_ids) )

            ids = list(set(ids))
            return ids

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Listing Ids in Shop')
    parser.add_argument('--shopid', '-s', type=int, help='taobao shopid, e.g. 33003356', required=True)
    option = parser.parse_args()
    print('total items: {}'.format(len(list_shop(option.shopid))))

if __name__ == '__main__':
    main()
