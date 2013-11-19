#coding:utf-8

""" Given taobao's itemid, return a dict of item info
#update()

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
import requests


from datetime import datetime, timedelta
from session import get_session, get_blank_session
from jsctx import get_ctx, need_decode

def is_banned():
    s = get_blank_session()
    iteminfo_url = 'http://detailskip.taobao.com/json/ifq.htm?id=26694692884&sid=860349499&sbn=882872a35964841ee57f639b99428609&q=1'
    return 'regcheckcode' in s.get(iteminfo_url).content

def is_valid_item(item):
    """ test if an item dict is valid """
    if not isinstance(item, dict):
        return False

    keys = ['id', 'num_reviews', 'num_sold30', 'shopid']
    for key in keys:
        if key not in item:
            return False

    return True

def get_item(id, prefix='http://item.taobao.com/item.htm?id={}'):
    """ given itemid, return item info dict """
    s = get_session()
    
    result = {}
    try:
        r = s.get(prefix.format(id), timeout=30)
    except:
        traceback.print_exc()
        result = {}
    else:
        content = r.content
        if 'error-notice-text' in content or 'errorDetail' in content:
            result = {'error': True, 'reason': 'not found'}
        elif 'tb-off-sale' in content:
            result = {'error': True, 'reason': 'off sale'}
        elif 'sold-out-tit' in content: 
            result = {'error': True, 'reason': 'sold out'}
        elif 'pageType:"auction"' in content:
            result = {'error': True, 'reason': 'auction'}
        elif 'status:-9' in content:
            result = {'error':True, 'reason': 'shop banned'}
            
        else:
            if 'http://s.tongcheng.taobao.com/detail.htm' in content:
                result = get_item(id, prefix='http://s.tongcheng.taobao.com/detail.htm?id={}') 
            elif r.url.startswith('http://item.taobao.com'):
                result = get_taobao_item(id, content)
            elif r.url.startswith('http://detail.tmall.com'):
                result = get_tmall_item(id, content)
            else:
                # we will ignore products in i.life.taobao.com
                return {'error':True, 'reason':'i.life.taobao.com'}
            
            result.update(get_brand_image(id))
            
    return result
    
def get_brand_image(id):
    ret = {}
    url = "http://a.m.taobao.com/da%s.htm#itemProp" % id
    response = requests.get(url)
    rec = re.compile(u'品牌：</td>\r\n<td>\r\n(.*?)\r\n</td>', re.DOTALL)
    rets = rec.findall(response.content.decode('utf-8'))
    if len(rets):
        ret['brand'] = rets[0] 
    else:
        ret['brand'] = '' 
    url = "http://a.m.taobao.com/i%s.htm" % id
    response = requests.get(url)
    retc2 = re.compile(u'<hr class="btm_line" />\r\n<div class="box">\r\n<div class="detail">.*?<p>\r\n<img alt=".*?" src="(.*?)" />\r\n</p>', re.DOTALL)
    rets = retc2.findall(response.content.decode('utf-8'))
    if len(rets):
        ret['image'] = rets[0]
    else:
        ret['image'] = ''
    return ret

def get_tmall_item(id, content):
    """ get tmall item info by id and content """
    patlist = [
        (r'<title>(.*?)</title>', lambda x: x.decode('gbk', 'ignore').split('-',1)[0], 'title'),
        (r'name="rootCatId" value="(\d+)"', int, 'rcid'),
    ]
    patdict = [
        (r'TShop.Setup\(({.*?})\)', [
            ('itemDO.itemId', int, 'id'),
            ('itemDO.userId', int, 'sellerid'),
            ('itemDO.categoryId', int, 'cid'), 
            ('itemDO.quantity', int, 'num_instock'),
            ('rstShopId', int, 'shopid'),
            ('valItemInfo', 'get_price', 'price'),
            ('initApi', 'get_tmall_details', 'price,num_sold30'),
        ]),
    ]
    result = parse_content(content, patlist, patdict)
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
            ('wholeSibUrl', 'get_sib_price', 'price'),
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
            print('parse content critical error, pat:{}'.format(pat))
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
                if field == 'wholeSibUrl' and not getattr(obj, field, None):
                    continue 

                for f in field.split('.'):
                    obj = getattr(obj, f)

                if isinstance(callback, str):
                    callback = eval(callback)

                try:
                    val = callback(obj)
                except Exception as e:
                    # shopid does not exist
                    # it must be a second hand product
                    # we should ignore it
                    if name == 'shopid':
                        return {'error':True, 'reason':'second hand'}
                    else:
                        raise e 
                if isinstance(val, dict):
                    for key in name.split(','):
                        if key in val and val[key] is not None:
                            result[key] = val[key]
                elif val is not None:
                    result[name] = val
        except:
            traceback.print_exc()
            continue

    result.update( get_counters(result.get('id'), result.get('sellerid')) )
    if 'num_sold30' not in result:
        return {}
    result['attributes'] = get_attributes(content)

    #try:
    #    url = re.compile(r'detail:params="([^,]+)').search(content).group(1)
    #    result['num_soldld'] = get_num_soldld(url, result['num_sold30'])
    #except:
    #    pass
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
        if not getattr(data, 'quantity', None):
            return 0
        return data.quantity.quanity
    except:
        traceback.print_exc()
        
def get_price(d):
    try:
        return min(float(d.skuMap[key].price) for key in d.skuMap.keys())
    except:
        return None

def get_sib_price(url):
    s = get_blank_session()
    ctx = get_ctx()
    s.headers['Referer'] = 'http://item.taobao.com/item.htm'
    patpromo = re.compile(r'PromoData=({.+]\s*})\s*;', re.DOTALL)
    try:
        content = s.get(url, timeout=30).content
        if need_decode:
            content = content.decode('gbk', 'ignore')

        if content and 'PromoData' in content:
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
        try:
            return {
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
        print('review for id {} failed'.format(id))
        traceback.print_exc()

def get_attributes(content):
    try:
        # never mind, a digusting encode/decode hell
        if need_decode is False:
            content = content.decode('gbk', 'ignore')
        al = re.compile(r'<ul class="attributes-list">(.*?)</ul>', re.DOTALL).search(content).group(1)
    except:
        return []
    else:
        return [ x.replace('&nbsp;', '').replace(u'\uff1a', ':').split(':') 
                for x in re.compile(r'>([^<]*)</li', re.DOTALL).findall(al) ] 

def get_buyhistory(content):
    """ get buy history, first page only, not used """
    url = re.compile(r'detail:params="(.*?),showBuyerList').search(content).group(1)
    url += '&callback=jsonp'
    patjsonp = re.compile(r'jsonp\((.*?)\);?', re.DOTALL)
    s = get_blank_session()
    ctx = get_ctx()
    try:
        content = s.get(url+'&callback=jsonp', timeout=30).content
        if need_decode:
            content = content.decode('gbk', 'ignore')
        # eval pattern using pyv8
        data = ctx.eval('d='+patjsonp.search(content).group(1))
        return re.compile('<em class="tb-rmb-num">(\d+)</em>.*?<td class="tb-amount">(\d+)</td>.*?<td class="tb-time">([^>]+)</td>', re.DOTALL).findall(data.html)
    except:
        traceback.print_exc()

def get_num_soldld(url):
    if url.endswith('&'):
        url = url[:-1]
    url += '&callback=jsonp'
    s = get_blank_session()
    headers = {'Referer': 'http://detail.tmall.com', 'User-Agent': 'Mozilla 5.0/Abracadabra'}
    try:
        last_day = (datetime.utcnow() - timedelta(hours=16)).date().strftime('%Y-%m-%d')
        def get_ld(page=1, total=0):
            theurl = url.replace('bid_page=1', 'bid_page='+str(page))
            #theurl = theurl.replace('bid_page', 'bidPage').replace('item_id', 'itemId').replace('seller_num_id', 'sellerNumId')
            content = s.get(theurl, headers=headers).content
            bl = re.compile(r'tb-amount\\">(\d+).*?tb-time\\">([^ ]+)', re.DOTALL).findall(content)
            bl.extend(re.compile(r'<td>(\d+)</td> <td>(\d+-\d+-\d+) ', re.DOTALL).findall(content))
            if bl == []:
                end = True
            else:
                end = False
                for amount, date in bl:
                    if date == last_day:
                        total += int(amount)
                    if date < last_day:
                        end = True
            if end:
                return total 
            else:
                return get_ld(page+1, total)
        return get_ld()
    except:
        traceback.print_exc()

def get_item_new(itemid):
    from h5 import get_item
    return get_item(itemid)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Get item by id')
    parser.add_argument('--id', '-i', type=int, help='taobao item id, e.g. 21825059650', required=True)
    option = parser.parse_args()
    from pprint import pprint
    print('Item {}:'.format(option.id))
    pprint(get_item_new(option.id))

if __name__ == '__main__':
    main()
