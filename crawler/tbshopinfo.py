#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shop Info:
    rating           [('4.6', 'lower', '2.79%'), ('4.7', 'lower', '2.15%'), ('4.6', 'lower', '3.46%')]
    rateid           20604171
    created          2004-10-21 12:19:05
    cid              14
    modified         2013-09-16 15:42:28
    rank             s_crown_2
    nick             ◎妞妞◎
    charge           1,504.88
    promise          ['xiaofei', 'seven']
    num_collects     569394
    sid              33003356
    title            ★妞妞旺铺★女装专家  T恤 雪纺 衬衫 裙子 裤子 每周一海量上新
    pic_path         /ae/98/T1mN4EXdFpXXartXjX.gif
    good_rating      92.4466666667
"""
import re
import json
import urllib
import requests

def get_shop(id_or_url):
    """ get shop info by id or url """
    if isinstance(id_or_url, str) and id_or_url.startswith('http://'):
        url = id_or_url
    else:
        url = 'http://shop{}.taobao.com'.format(id_or_url)

    try:
        content = requests.get(url).content
    except:
        return {}

    try:
        rateid = re.compile(r'http://rate.taobao.com/user-rate-([0-9a-f]+).htm').search(content).group(1)
    except:
        return get_shop(id_or_url)

    try:
        rank = re.compile(r'http://pics.taobaocdn.com/newrank/(.*?).gif').search(content).group(1)
    except:
        rank = 'tmall'

    nick = urllib.unquote(re.compile(r'data-nick="([^"]+)"').search(content).group(1))

    info = get_shop_info(nick)

    if info:
        info['rank'] = rank
        info['rateid'] = rateid
        info.update(get_collects_info(info['sid']))
        info.update(get_service_info(rateid))

    return info


def get_collects_info(sid):
    try:
        counturl = 'http://count.tbcdn.cn/counter3?callback=jsonp&keys=SCCP_2_{}'.format(sid)
        countresp = requests.get(counturl).content
        return {'num_collects':int(re.compile(r':(\d+)').search(countresp).group(1))}
    except:
        return {}

def get_service_info(rateid):
    try:
        rateurl = 'http://rate.taobao.com/user-rate-{}.htm'.format(rateid)
        rateresp = requests.get(rateurl).content

        # promise can be 'xiaofei', 'seven', 'fake', 'ZPBZ', 'TGFP', 'QTTH'
        # 消费保障, 七天退换, 假一罚三, 正品保障, 提供发票, 七天退换
        promise = {}
        if 'xiaobao1' not in rateresp: # it's a tmall store
            promise['ZPBZ'] = 'promise.php#ZPBZ' in rateresp
            promise['TGFP'] = 'promise.php#TGFP' in rateresp
            promise['QTTH'] = 'promise.php#QTTH' in rateresp
            promise['xiaofei'] = True
            promise = [key for key in promise if promise[key]]
        else:
            xiaobao = re.compile('class="xiaobao-box".*?</ul', re.DOTALL).search(rateresp).group()
            promise = re.compile('<span class="([^"]+)"').findall(xiaobao)
        try:
            charge = re.compile(r'class="charge".*?([0-9,.]+)').search(rateresp).group(1)
        except:
            charge = ''
       
        rating = re.compile(r'class="count">([^<]*).*?class="percent ([a-z]*)[^>]*>([^<]*)', re.DOTALL).findall(rateresp)
        rates = re.compile(r'class="small-star-no[45]".*?(\d+\.\d+)%', re.DOTALL).findall(rateresp)
        good_rating = sum(float(r) for r in rates)/3
        return {'promise':promise, 'charge':charge, 'good_rating':good_rating, 'rating':rating}
    except:
        return {}

def get_shop_info(nick):
    url = 'http://api.taobao.com/apitools/getResult.htm'
    data = {
        'api_source': 0,
        'app_key': '系统分配',
        'app_secret': '系统分配',
        'codeType': 'JAVA',
        'fields': 'sid,cid,title,nick,pic_path,created,modified',
        'format': 'json',
        'method': 'taobao.shop.get',
        'nick': nick,
        'restId': 2,
        'session': '',
        'sip_http_method': 'POST'
    }
    try:
        resp = requests.post(url, data=data).content.split('^|^')[1].replace('&quot;', '"')
        r = json.loads(resp)
    except:
        return {}
    if 'error_response' in r:
        return {}
    else:
        return r['shop_get_response']['shop']

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Listing Ids in Shop')
    parser.add_argument('--shopid', '-s', type=int, help='taobao shopid, e.g. 33003356', required=True)
    option = parser.parse_args()
    print('Shop Info:')
    shop = get_shop(option.shopid)
    for key, value in shop.iteritems():
        print(u'    {:16s} {}'.format(key, value))

if __name__ == '__main__':
    main()
