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
import re
import traceback
from session import get_session, get_blank_session
from h5 import get_item as get_item_h5, get_cid

def get_item(itemid):
    i = get_item_h5(itemid)
    if i and 'error' not in i:
        cid = get_cid(itemid)
        if cid:
            i['cid'] = cid
    return i

def get_buyhistory(itemid):
    """ get buy history, first page only
    
    :param itemid: itemid for item
    :returns: list of (price/sold, sold/price, date) tuple
    """
    s = get_session()
    content = s.get('http://item.taobao.com/item.htm?id={}'.format(itemid)).content
    url = re.compile(r'detail:params="(.*?),showBuyerList').search(content).group(1)
    url += '&callback=jsonp'
    patjsonp = re.compile(r'jsonp\((.*?)\);?', re.DOTALL)
    s = get_blank_session()
    s.headers['Referer'] = 'http://detail.tmall.com/item.htm'
    try:
        content = s.get(url+'&callback=jsonp', timeout=30).content
        content = content.replace('\\"', '"')
        if content == 'jsonp({"status":1111,"wait":5})':
            print 'baned, sleeping for 5 mins'
            time.sleep(5*60)
            return get_buyhistory(itemid)
        ret1 = re.compile('<em class="tb-rmb-num">([^<]+)</em>.*?<td class="tb-amount">(\d+)</td>.*?<td class="tb-time">([^>]+)</td>', re.DOTALL).findall(content)
        ret2 = re.compile('<em>(\d+)</em>.*?<td>(\d+)</td>.*?<td>([^<]+)</td>', re.DOTALL).findall(content)
        ret1.extend(ret2)
        return ret1
    except:
        print '!!!', itemid
        traceback.print_exc()

def get_lastbuy(itemid):
    history = get_buyhistory(itemid)
    return max([h[-1] for h in history])

def get_offset(itemid):
    now = datetime.now()
    try:
        lb = datetime.strptime(get_lastbuy(itemid), '%Y-%m-%d %H:%M:%S')
    except:
        traceback.print_exc()
        return None
    return min(15, (now - lb).days)
    
def main():
    import argparse
    parser = argparse.ArgumentParser(description='Get item by id')
    parser.add_argument('--id', '-i', type=int, help='taobao item id, e.g. 21825059650', required=True)
    option = parser.parse_args()
    from pprint import pprint
    pprint(get_item(option.id))

if __name__ == '__main__':
    main()
