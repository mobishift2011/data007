#coding:utf-8

""" Given taobao's itemid, return a dict of item info
#update()

Usage::

    >>> from tbitem import get_item
    >>> get_item(24032200383)
    {
     'id': 24032200383,
     'num_collects': 2344,
     'num_instock': 37896,
     'num_reviews': 712,
     'num_sold30': 415,
     'num_views': 21147,
     'pagetype': 'taobao',
     'price': 22.0,
     'rating': 4.7,
     'sellerid': 169988019,
     'shopid': 62393798}

"""
from h5 import get_item as get_item_h5, get_cid

def get_item(itemid):
    i = get_item_h5(itemid)
    if i and 'error' not in i:
        cid = get_cid(itemid)
        if cid:
            i['cid'] = cid
    return i
    
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Get item by id')
    parser.add_argument('--id', '-i', type=int, help='taobao item id, e.g. 21825059650', required=True)
    option = parser.parse_args()
    from pprint import pprint
    pprint(get_item(option.id))

if __name__ == '__main__':
    main()
