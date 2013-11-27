#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" taobao h5 api item info hack 

h5 api brief
============
1. signature algorithm
    e.g.
    sign = md5(
        cookies['_m_h5_tk'].split('_')[0] + '&'
        + timestr + '&'
        + appkey + '&'
        + '{"itemNumId":"ITEMID"}',
    )

2. request generation
   url = 'http://api.m.taobao.com/rest/h5ApiUpdate.do?'+options+'&sign=SIGN'

3. steps:
    a. get h5 token:
       issue normal request, token will be set to cookie

    b. issue request again, result is jsonp response


h5 api list
===========

item
----

- mtop.wdetail.getItemDetailStatic:
    * id, title, price, status, location, image, num_sold30, num_instock, num_collects, soldout
    * seller. id, location, mobile, type, nick, phone, certify, credit, evaluateInfo
    * props
    * guaranttes
    * skuProps
    
- mtop.wdetail.getItemDetailDynForH5:
    * priceUnits, delivery, trade, skus, quantity, promotion

- mtop.wdetail.getItemDetailOther:
    * jshItemInfo
        + soldCount, limitNum, jhsItemStatus, activityPrice, discount, payPostage, originalPrice, onlineStartTime, grouopId, onlineEndTime

- mtop.wdetail.getItemRates:
    * total, feedGoodCount, feedNormalCount, feedBadCount, feedAppendCount
    * rateList
        + id, auctionNumId, auctionTitle, userId, userNick, userStar, headPicUrl, annoy, rateType, feedback, feedbackDate, skuMap

shop
----

- mtop.shop.getWapShopInfo:
    * prov, phone, picUrl, isMall, rankType, rankNum, sellerId, nick, title

- com.taobao.wireless.shop.feedback.sum: v 1.0
    * badSeller, neutralSeller, goodSeller

- com.taobao.search.api.getShopItemList, v 2.0
    * itemsArray. auctionId, title, picUrl, ...
    * totalResults
    * shopId
    * shopTitle
    * pageSize (30)
    * currentPage

- com.taobao.search.api.getCatInfoInShop, v 1.0
    * cates 
        + id
        + name
        + imagePath
        + subCates. id, name, imagePath

"""
import re
import time
import json
import urllib
import base64
import hashlib
import requests
import traceback
import threading
from requests.cookies import cookiejar_from_dict

lock = threading.Lock()

bsession = requests.Session()
session = requests.Session()
session.headers = {
    'Referer': 'http://h5.m.taobao.com/awp/core/detail.htm',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5)',
}

vs = {
    "mtop.shop.getWapShopInfo": 1.0,
    "com.taobao.search.api.getCatInfoInShop": 1.0,
    "com.taobao.search.api.getShopItemList": 2.0,
    "com.taobao.wireless.shop.feedback.sum": 1.0,
    "mtop.wdetail.getItemDesc": 3.0,
    "mtop.wdetail.getItemDetailDynForH5": 4.0,
    "mtop.wdetail.getItemDetailStatic": 4.0,
    "mtop.wdetail.getItemDetailOther": 4.0,
    "mtop.wdetail.getItemRates": 2.0,
}

class NetworkError(Exception):
    pass

class NotFoundError(Exception):
    pass

def retry(times, func, *args, **kwargs):
    count = times
    while count >= 0:
        try:
            r = func(*args, **kwargs)
        except Exception as e:
            count -= 1
            continue
        else:
            return r
    raise e

def get_misc(shopid, sid=None, type='taobao'):
    """ get shop charge/main_sale info """
    try:
        r = {}
        if sid is None or type is None:
            j = get_json("mtop.shop.getWapShopInfo", {"shopId":shopid})
            if not j:
                return r
            sid = j['data']['sellerId']
            type = 'tmall' if j['data'].get('isMall', 'false') == 'true' else 'taobao'
        url = 'http://rate.taobao.com/user-rate-{}.htm'.format(sid)

        rates = retry(3, session.get, url, timeout=30).text

        try:
            r['charge'] = re.compile(r'class="charge".*?([0-9,.]+)').search(rates).group(1)
        except:
            r['charge'] = ''

        try:
            r['main_sale'] = re.compile(ur'当前主营[^>]+>([^<]+)<').findall(rates)[-1].replace('&nbsp;','').replace('\r\n', '').replace(' ', '')
        except:
            traceback.print_exc()
            r['main_sale'] = ''

        # this can be achieved by 
        # ==== client side ajax ====
        # $.ajax({
        #          url:'http://rate.taobao.com/ShopService4C.htm?userNumId=1688836098', 
        #          dataType:'jsonp', 
        #          success: function(data) { console.log(data); }
        # })
        # 
        # ==== python code ====
        # url = 'http://rate.taobao.com/ShopService4C.htm?userNumId={}'.format(sid)
        # try:
        #     s30 = requests.get(url, timeout=30).json()
        # except:
        #     traceback.print_exc()
        # else:
        #     r.update(s30)

        # promises
        promise = []
        if type == 'taobao':
            for cname in ["xiaofei", "seven", "fake", "thirty", "lightning", "safe", "xb-three"]:
                token = 'class="{}"'.format(cname)
                if token in rates:
                    promise.append(cname) 
        r['promise'] = promise

        return r
    except:
        traceback.print_exc()
        return {}
    

def get_interacts(itemid, sid=None, type=None):
    """ these information can be fetched in client side

    treat this as an example implementation
    """
    if sid is None or type is None:
        try:
            d = get_json("mtop.wdetail.getItemDetailStatic", {"itemNumId":itemid})
            sid = d['data']['seller']['userNumId']
            type = 'tmall' if d['data']['seller']['type'] == 'B' else 'taobao'
        except:
            pass
    try:
        i = {}
        if type is None or type == 'taobao':
            #taobao
            if sid:
                url = 'http://orate.alicdn.com/detailCommon.htm?auctionNumId={}&userNumId={}'.format(itemid, sid)
            else:
                url = 'http://orate.alicdn.com/detailCommon.htm?auctionNumId={}'.format(itemid)
                
            text = retry(3, requests.get, url, timeout=30, headers={'User-Agent':'Mozilla/4.0'}).text

            summary = json.loads(text.strip()[1:-1])['data']
            if sid:
                i['num_rates'] = summary['correspondCount']
                i['rate'] = summary['correspond']
            impress = summary['impress']
            impress = [ {'title':x['title'], 'value':x['count']*x['value']} for x in impress ]
            if sid:
                i['good'] = summary['count']['good']
                i['normal'] = summary['count']['normal']
                i['bad'] = summary['count']['bad']
            else:
                i['good'] = sum(x['value'] for x in impress if x['value']>0)
                i['normal'] = 0
                i['bad'] = -sum(x['value'] for x in impress if x['value']<=0)
            i['impress'] = impress
        else:
            #tmall
            rateurl = 'http://dsr.rate.tmall.com/list_dsr_info.htm?itemId={}&callback=jsonp'.format(itemid)
            tagurl = 'http://rate.tmall.com/listTagClouds.htm?itemId={}'.format(itemid)
            try:
                rates = retry(3, requests.get, rateurl, timeout=30, headers={'User-Agent':'Mozilla/4.0'}).text
                tags = retry(3, requests.get, tagurl, timeout=30, headers={'User-Agent':'Mozilla/4.0'}).text
            except:
                pass
            dsr = json.loads(rates[6:-1])['dsr']
            i['rate'] = str(dsr["gradeAvg"])
            i['num_rates'] = dsr["rateTotal"]
            tc = json.loads('{'+tags+'}')['tags']['tagClouds']
            impress = [ {'title':x['tag'].strip(), 'value':x['count']*int(2*(int(x['posi'])-0.5))}
                            for x in tc ]
            i['impress'] = impress
            i['good'] = sum(x['value'] for x in impress if x['value']>0)
            i['normal'] = 0
            i['bad'] = -sum(x['value'] for x in impress if x['value']<=0)
        return i 
    except NotFoundError:
        return {'good':0,'normal':0,'bad':0,'impress':[]}
    except:
        traceback.print_exc()
        return {} if 'i' not in locals() else i
    

def get_cid(itemid):
    """ use m.taobao.com, fetch cid info """
    url = 'http://a.m.tmall.com/i{}.htm'.format(itemid)
    count = 3
    r = retry(3, bsession.get, url, timeout=30, stream=True, headers={'User-Agent': 'Mozilla/4.0'})
    i = retry(3, r.iter_content, chunk_size=4000)
    try:
        html = retry(3, i.next)
    except:
        print '!! get cid failed, retries={}'.format(3)
        html = ''

    cids = re.compile(r'cat=(\d+)').findall(html)
    return int(cids[-1]) if cids else 0

def setup_token():
    """ token will expire after an hour, 
        
    so let's do it when we have 
        1. first init
        2. request return "令牌过期"
    """
    with lock:
        url = get_request_url("mtop.wdetail.getItemDetailStatic", 20006742565)
        retry(3, session.get, url, timeout=30)

def get_request_url(api, data):
    apiurl = 'http://api.m.taobao.com/rest/h5ApiUpdate.do'
    t = int(time.time())*1000
    h5tk = session.cookies.get('_m_h5_tk', '')
    tk = h5tk.split('_')[0]
    appkey = "12574478" 
    data = json.dumps(data, separators=(',', ':')) 
    tohash = tk+'&'+str(t)+'&'+appkey+'&'+data
    sign = hashlib.md5(tohash).hexdigest()
    options = {
        "callback": "jsonp",
        "type": "jsonp",
        "api": api,
        "v": vs.get(api, 1.0),
        "data": urllib.quote(data),
        "ttid": urllib.quote("2013@taobao_h5_1.0.0"),
        "appkey": appkey,
        "t": int(t),
        "sign": sign,
    } 
    url = apiurl + '?callback={callback}&type={type}&api={api}&v={v}&data={data}&ttid={ttid}&appKey={appkey}&t={t}&sign={sign}'.format(**options)
    return url

def get_json(api, data):
    if session.cookies.get('_m_h5_tk', '') == '':
        setup_token()
    url = get_request_url(api, data)

    text = retry(3, session.get, url, timeout=30).text

    if u'令牌过期' in text or u'令牌为空' in text:
        setup_token() 
        return get_json(api, data)
    elif u'宝贝不存在' in text or u'ID错误' in text or u'没有查询到记录' in text or u'类目不存在' in text:
        raise NotFoundError("Shop/Item Not Found")
    elif u'网络系统异常' in text:
        raise NotFoundError("Taobao Api Error")
    else:
        resp = json.loads(text.strip()[6:-1])
        if not resp['ret'][0].startswith('SUCCESS'):
            raise ValueError('Unknown API Failure: {}'.format(text.encode('utf-8')))
        else:
            return resp

def get_shopitems(shopid):
    ids = []
    def extend(itemlist):
        for item in itemlist['data']['itemsArray']:
            if int(item['sold']) == 0:
                return False
            ids.append(int(item['auctionId']))
        return True
                
    itemlist = get_json(api="com.taobao.search.api.getShopItemList", 
                        data={"shopId":shopid, "sort":"hotsell", "pageSize":30}) 
    if itemlist:
        total = int(itemlist['data']['totalResults'])
        if total>0:
            if extend(itemlist) and total > 30:
                for page in range(2, min(101, (total-1)/30+2)):
                    itemlist = get_json(api="com.taobao.search.api.getShopItemList",
                                data={"shopId":shopid, "sort":"hotsell", "pageSize":30, "currentPage":page})
                    if not extend(itemlist):
                        break
    return ids

def get_mobile(shopid):
    itemlist = get_json(api="com.taobao.search.api.getShopItemList", 
                        data={"shopId":shopid, "sort":"hotsell", "pageSize":10}) 
    if itemlist is None or \
        itemlist['data']['totalResults'] == 0 or \
        'itemsArray' not in itemlist['data']:
        return ''
    else:
        itemid = itemlist['data']['itemsArray'][0]['auctionId']
        try:
            itemdetail = get_json(api="mtop.wdetail.getItemDetailStatic", data={"itemNumId":itemid})
        except NotFoundError:
            return ''
        except:
            return ''
        if itemdetail is None:
            return ''
        seller = itemdetail['data']['seller']
    return seller.get('mobile', '')

def get_shop(shopid):
    try:
        j = get_json("mtop.shop.getWapShopInfo", {"shopId":shopid})
        d = j['data'] 

        def fix_logo(url):
            if url == '':
                return url
            else:
                if '80x80' not in url:
                    return url[:-4] + '_80x80' + url[-4:]
                else:
                    return url
        s = {
            'id': int(shopid),
            'sid': int(d.get('sellerId', 0)),
            'logo': fix_logo(d.get('picUrl', '')),
            'type': 'tmall' if d.get('isMall', 'false') =='true' else 'taobao',
            'nick': d.get('nick', ''),
            'title': d.get('title', ''), 
            'prov': d.get('prov', ''),
            'city': d.get('city', ''),
            'credit_score': int(d.get('rateSum', 0)),
            'num_collects': int(d.get('collectorCount', 0)),
            'num_products': int(d.get('productCount', 0)),
            'good_rating': d.get('shopDSRScore', {}).get('sellerGoodPercent', ''),
            'rating': d.get('shopDSRScore', {}),
            'created_at': d.get('starts', ''),

            'mobile': get_mobile(shopid), 

            # unimplemented
            # see get_misc
            # charge
            # promise
            # main_sale

            # for compability only
            'rank_num': 0,
            'rank': '', 
            'rates': '',
            'rateid': '',
        }
        return s
    except:
        traceback.print_exc()
        return {}

def get_item(itemid):
    result = {}
    try:
        j = get_json("mtop.wdetail.getItemDetailStatic", {"itemNumId":itemid})
        p = get_json("mtop.wdetail.getItemDetailDynForH5", {"itemNumId":itemid})
        i = j['data']['item'] 
        s = j['data']['seller']

        def get_brand():
            for prop in j['data'].get('props', []):
                if prop['propId'] == '20000':
                    return prop['values'][0]['name']
            return ''

        def get_price():
            if 'priceUnits' in p['data']:
                pu = p['data']['priceUnits'][0]
                price = float(pu['price'].split('-')[0])
                promo = pu['name']
                return {'price': price, 'promo': promo}
            else:
                o = get_json('mtop.wdetail.getItemDetailOther', {"itemNumId": itemid})
                if 'jhsItemInfo' in o['data']:
                    price = int(o['data']['jhsItemInfo']['activityPrice'])/100. 
                    promo = u'聚划算'
                    return {'price': price, 'promo': promo}
                else:
                    #raise ValueError('price cannot be found!')
                    return {'price': int(i.get('price', 0))/100., 'promo': ''}

        def get_counters():
            if s.get('type', 'C') == 'C':
                # taobao shop counters
                counters = {
                    'ICE_3_feedcount-{}'.format(itemid): 'num_reviews',
                    'ICVT_7_{}'.format(itemid): 'num_views',
                }
                url = 'http://count.tbcdn.cn/counter3?keys={}&callback=jsonp'.format(','.join(counters.keys()))
                r = retry(3, session.get, url, timeout=30)

                d = json.loads(r.text[6:-2])
                result = {}
                for key, value in counters.items():
                    if key in d:
                        result[value] = d[key] 
                return result
            else:
                # tmall shop counters
                url = 'http://dsr.rate.tmall.com/list_dsr_info.htm?itemId={}&callback=jsonp'.format(itemid)
                data = retry(3, session.get, url, timeout=30).content.strip()[6:-1]
                return {'num_reviews':json.loads(data)['dsr']['rateTotal'], 'num_views':0}

        def get_image():
            image = i.get('picsPath', [''])
            if not image:
                return ''
            else:
                return image[0]

        result.update({
            'id': itemid,
            'type': {'B':'tmall', 'C':'taobao'}.get(s.get('type', 'B'), 'taobao'),
            'brand': get_brand(),
            'image': get_image(),
            'shopid': int(s.get('shopId', 0)),
            'title': i.get('title', ''),
            'oprice': int(i.get('price', 0))/100.,
            'num_instock': int(p['data'].get('quantity', 0)),
            'num_collects': int(i.get('favcount', 0)),
            'num_sold30': int(i.get('totalSoldQuantity', 0)),
            'delivery_type': int(i.get('delivery', {}).get('deliveryFeeType', 1)),

            # unimplemented
            # cid, see get_cid
            # interacts, see get_interacts

            # for compability
            'rating': 0,
            'pagetype': '',
            'rcid': 0,
        })
        result.update(get_price())
        result.update(get_counters())
        return result
    except NotFoundError:
        return {'error': 'not found'}
    except:
        traceback.print_exc()
        return {}

def test_ban():
    t0 = time.time()
    for i in range(10000):
        j = get_json("mtop.wdetail.getItemDetailDynForH5", 19725558910)
        print i, 1.*(time.time()-t0)/(i+1), j['ret'][0].startswith('SUCCESS') == True

def main():
    import argparse
    from pprint import pprint
    parser = argparse.ArgumentParser(description='Get Info from h5 api/mobiles/others')
    parser.add_argument('--method', '-m', choices=['item', 'shop', 'cid', 'interacts', 'misc', 'shopitems', 'mobile'], type=str, help='method to call')
    parser.add_argument('--id', '-i', type=int, help='taobao item/shop id, e.g. 35515810124/61775664', required=True)
    option = parser.parse_args()
    pprint(globals()['get_'+option.method](option.id))

if __name__ == '__main__':
    main()
