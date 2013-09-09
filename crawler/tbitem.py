""" Given taobao's itemid, return a dict of item info

Usage::

    >>> from tbitem import get_item
    >>> get_item(24032200383)
    {'cid': 50010850,
     'id': 24032200383,
     'num_collects': 2344,
     'num_instock': 37896,
     'num_reviews': 712,
     'num_sold30': 415,
     'num_views': 21147,
     'pagetype': 'taobao',
     'price': 22.0,
     'rating': 4.7,
     'rcid': 16,
     'sellerid': 169988019,
     'shopid': 62393798}

"""
import re
import json
import operator
import traceback

from session import get_session, get_blank_session
from jsctx import get_ctx, need_decode

def is_valid_item(item):
    """ test if an item dict is valid """
    if not isinstance(item, dict):
        return False

    keys = ['id', 'num_reviews', 'num_sold30', 'shopid']
    for key in keys:
        if key not in item:
            return False

    return True

def get_item(id):
    """ given itemid, return item info dict """
    s = get_session()
    try:
        r = s.get('http://item.taobao.com/item.htm?id={}'.format(id), timeout=30)
    except:
        traceback.print_exc()
        return {}
    else:
        content = r.content
        if 'error-notice-text' in content:
            return {}
        if r.url.startswith('http://item.taobao.com'):
            return get_taobao_item(id, content)
        elif r.url.startswith('http://detail.tmall.com'):
            return get_tmall_item(id, content)

def get_tmall_item(id, content):
    """ get tmall item info by id and content """
    patlist = [
        (r'<title>(.*?)</title>', lambda x: x.decode('gbk', 'ignore').split('-',1)[0], 'title'),
        (r'name="rootCatId" value="(\d+)"', int, 'rcid'),
    ]
    patdict = {
        r'TShop.Setup\(({.*?})\)': [
            ('itemDO.itemId', int, 'id'),
            ('itemDO.userId', int, 'sellerid'),
            ('itemDO.categoryId', int, 'cid'), 
            ('itemDO.quantity', int, 'num_instock'),
            ('rstShopId', int, 'shopid'),
            ('valItemInfo', 'get_price', 'price'),
            ('initApi', 'get_tmall_details', 'price,num_sold30'),
        ],
    }
    result =  parse_content(content, patlist, patdict)
    result['pagetype'] = 'tmall'
    val = get_tmall_num_reviews(id)
    if val is not None:
        result['num_reviews'] = val
    return result

def get_taobao_item(id, content):
    """ get taobao item info by id and content """
    patlist = [
        (r'<title>(.*?)</title>', lambda x: x.decode('gbk', 'ignore').split('-',1)[0], 'title'),
    ]
    patdict = [
        (r'g_config = ({.*?});', [
            ('itemId', int, 'id'),
            ('shopId', int, 'shopid'),
        ]),  
        (r'g_config.idata=({.*?})}\)', [
            ('seller.id', int, 'sellerid'),
            ('item.cid', int, 'cid'),
            ('item.rcid', int, 'rcid'),
            ('item.price', float, 'price'),
            ('item.virtQuantity', int, 'num_instock'),
        ]),
        (r"Hub.config.set\('sku',({.*?})\)", [
            ('apiItemInfo', 'get_sold30', 'num_sold30'),
            #('valItemInfo', 'get_price', 'price'),
            ('umpStockUrl', 'get_ump_price', 'price'),
        ]),
    ]
    result = parse_content(content, patlist, patdict)
    if result:
        result['pagetype'] = 'taobao'
    return result

def parse_content(content, patlist, patdict):
    """ given content as patterns, return parsed results

    :param content: html raw content
    :param patlist: a list of (``pattern``, ``callback``, ``fieldname``)s
    
                    ``pattern`` will be checked againt ``content``, the matched result 
                    will then be called in ``callback`` as parameter, the returned result
                    then assigned to the final result dict

    :param patdict: a dict of (``pattern``, ``rulelist``)s

                    we first extract ``content`` according to ``pattern``,
                    then we evaluate ``content`` using ``PyV8``,
                    then we apply each rule in rulelist to the evaluated ``Javascript Object``
        
                    each rule contains three part: ``ObjectPath``, ``callback``, ``fieldname``
                    an ``ObjectPath`` represents JavaScript Object calling path: 
                    e.g. Object.key1.key2 will be mapped to 'key1.key2'
                    then we apply ``callback`` with the extracted value,
                    and assign this value to the given ``fieldname`` of our result dict

    :returns: a result dict e.g. {'id':23413241234, 'price':112.11, ... }
    """
    ctx = get_ctx()
    result = {}
    for pat, callback, name in patlist:
        try:
            data = re.compile(pat, re.DOTALL).search(content).group(1)
                
            if isinstance(callback, str):
                callback = eval(callback)

            val = callback(data)
            if val is not None:
                result[name] = val
        except:
            print content
            traceback.print_exc()
            continue
    
    if need_decode:
        content = content.decode('gbk', 'ignore')
    for pat, patlist in patdict:
        try:
            # eval pattern using pyv8
            data = ctx.eval('d='+re.compile(pat, re.DOTALL).search(content).group(1))
            for field, callback, name in patlist:
                obj = data
                if field == 'umpStockUrl' and not getattr(obj, field, None):
                    continue 

                for f in field.split('.'):
                    obj = getattr(obj, f)

                if isinstance(callback, str):
                    callback = eval(callback)

                try:
                    val = callback(obj)
                except Exception as e:
                    # shopid does not exist
                    if name == 'shopid':
                        return {}
                    else:
                        raise e 
                if isinstance(val, dict):
                    for key in name.split(','):
                        if key in val and val[key]:
                            result[key] = val[key]
                elif val is not None:
                    result[name] = val
        except:
            traceback.print_exc()
            continue

    result.update( get_counters(result.get('id'), result.get('sellerid')) )
    return result

def get_counters(id, sellerid):
    """ get counters info from taobao """
    patjsonp = re.compile(r'jsonp\((.*?)\);', re.DOTALL)
    counters = {
        'ICCP_1_{}'.format(id): 'num_collects',
        'ICE_3_feedcount-{}'.format(id): 'num_reviews',
        'SM_368_sm-{}'.format(sellerid): 'rating',
        'ICVT_7_{}'.format(id): 'num_views',
    }
    url = 'http://count.tbcdn.cn/counter3?keys={}&callback=jsonp'.format(','.join(counters.keys()))
    s = get_blank_session()
    ctx = get_ctx()
    try:
        data = dict(ctx.eval('d='+patjsonp.search(s.get(url, timeout=30).content).group(1)))
        result = {}
        for key in data:
            if key in counters:
                result[counters[key]] = data[key] 
        return result
    except:
        traceback.print_exc()
        return {}

def get_sold30(url):
    patjsonp = re.compile(r'jsonp\((.*?)\);', re.DOTALL)
    s = get_blank_session()
    ctx = get_ctx()
    try:
        content = s.get(url+'&callback=jsonp', timeout=30).content
        if need_decode:
            content = content.decode('gbk', 'ignore')
        # eval pattern using pyv8
        data = ctx.eval('d='+patjsonp.search(content).group(1))
        if not getattr(data, 'quantity', None) and data.postage:
            return 0
        return data.quantity.quanity
    except:
        traceback.print_exc()
        
def get_price(d):
    try:
        return min(float(d.skuMap[key].price) for key in d.skuMap.keys())
    except:
        return None

def get_ump_price(url):
    s = get_blank_session()
    ctx = get_ctx()
    s.headers['Referer'] = 'http://item.taobao.com/item.htm'
    patpromo = re.compile(r';TB.PromoData = ({.+)', re.DOTALL)
    try:
        content = s.get(url, timeout=30).content
        if need_decode:
            content = content.decode('gbk', 'ignore')
        content = re.sub(r';TB.PointData=.*', '', content).strip()
        if content:
            data = ctx.eval('d='+patpromo.search(content).group(1))
            if data['def'].length > 0:
                if hasattr(data['def'][0], 'price'):
                    return float(data['def'][0].price)
    except:
        traceback.print_exc()

def get_tmall_details(url):
    s = get_blank_session()
    ctx = get_ctx()
    s.headers['Referer'] = 'http://item.taobao.com/item.htm'
    try:
        content = s.get(url, timeout=30).content
        if need_decode:
            content = content.decode('gbk', 'ignore')
        data = ctx.eval('d='+content)
        # price
        prices = set()
        for pikey in data.defaultModel.itemPriceResultDO.priceInfo.keys():
            prices.add(float(data.defaultModel.itemPriceResultDO.priceInfo[pikey].price))
            if data.defaultModel.itemPriceResultDO.priceInfo[pikey]['promotionList']:
                for i in range(data.defaultModel.itemPriceResultDO.priceInfo[pikey]['promotionList'].length):
                    prices.add(float(data.defaultModel.itemPriceResultDO.priceInfo[pikey]['promotionList'][i].price))
        return {
            'price': min(prices),
            'num_sold30': data.defaultModel.sellCountDO.sellCount,
        }
    except:
        traceback.print_exc()

def get_tmall_num_reviews(id):
    url = 'http://rate.tmall.com/list_dsr_info.htm?itemId={}'.format(id)
    s = get_blank_session()
    try:
        data = '{'+s.get(url, timeout=30).content.strip()+'}'
        return json.loads(data)['dsr']['rateTotal']
    except:
        traceback.print_exc()


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Get item by id')
    parser.add_argument('--id', '-i', type=int, help='taobao item id, e.g. 21825059650', required=True)
    option = parser.parse_args()
    from pprint import pprint
    print('Item {}:'.format(option.id))
    pprint(get_item(option.id))

if __name__ == '__main__':
    main()
