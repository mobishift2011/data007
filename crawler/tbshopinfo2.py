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
import traceback

from session import get_session, get_blank_session

from pyquery import PyQuery


def get_shop(id_or_url):
    """ get shop info by id or url """
    if isinstance(id_or_url, str) and id_or_url.startswith('http://'):
        url = id_or_url
    else:
        url = 'http://shop{}.taobao.com'.format(id_or_url)
    s = get_session()
    print "begin...: %s" % url
    try:
        content = s.get(url, timeout=30).content
    except:
        traceback.print_exc()
        return {}

    if "error-notice" in content:
        return {"error": True}

    try:
        rateid = re.compile(r'http://rate.taobao.com/user-rate-([0-9a-f]+).htm').search(content).group(1)
    except:
        traceback.print_exc()
        return get_shop(id_or_url)
    try:
        rank = re.compile(r'http://pics.taobaocdn.com/newrank/(.*?).gif').search(content).group(1)
    except:
        if u'该店铺尚未收到评价' in content.decode('gb18030', 'ignore'):
            rank = '0'
        else:
            #traceback.print_exc()
            print "rank is tmall"
            rank = 'tmall'
        
    nick = urllib.unquote(re.compile(r'data-nick="([^"]+)"').search(content).group(1))
    
    info = {}
    info['sid'] = re.compile(r'http://shop(.*?).taobao.com').search(url).group(1)
    info['nick'] = nick
    info['rank'] = rank
    info['rateid'] = rateid
    if rank == '0':
        info['rank_num'] = 0

    if info['rank'] == "tmall":
        info['num_collects'] = 0
        info.update(get_shop_info(info['sid']))
        info.update(get_service_info(rateid, s))
        info.update(get_search_info(url, info, s))
    else:
        info.update(get_collects_info(info['sid'], s))
        info.update(get_service_info(rateid, s))
        info.update(get_search_info(url, info, s))

    for field in ['title', 'logo', 'main_cat']:
        if info[field] is None:
            info[field] = ''
        
    return info


def get_search_info(url, src_info, s):
    print "begin...get_search_info"
    
    info = {}
    try:

        search_url = "http://s.taobao.com/search?q=%s&app=shopsearch" % src_info['nick']
        content = s.get(search_url, timeout=30).content
        body = PyQuery(content.decode("gbk", "ignore"))
        ele = body.find('ul#list-container li.list-item:first-child')
        
        info['main_cat'] = PyQuery(ele).find("li.list-info p.main-cat a").text()
        
        info['logo'] = PyQuery(ele).find("li.list-img img").attr("src")
        
        info['title'] = PyQuery(ele).find('li.list-info a.shop-name.J_shop_name[trace="shop"]').text()
    except:
        traceback.print_exc()
        
    return info

#===============================================================================
# api 调用
#===============================================================================
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
    
    
def get_collects_info(sid, s):
    print "begin...get_collects_info"
    try:
        counturl = 'http://count.tbcdn.cn/counter3?callback=jsonp&keys=SCCP_2_{}'.format(sid)
        countresp = s.get(counturl, timeout=30).content
        return {'num_collects':int(re.compile(r':(\d+)').search(countresp).group(1))}
    except:
        traceback.print_exc()
        return {}

def get_service_info(rateid, s):
    print "begin...get_service_info"
    try:
        info = {}
        rateurl = 'http://rate.taobao.com/user-rate-{}.htm'.format(rateid)
        rateresp = s.get(rateurl, timeout=30).content
        # promise can be 'xiaofei', 'seven', 'fake', 'ZPBZ', 'TGFP', 'QTTH'
        # 消费保障, 七天退换, 假一罚三, 正品保障, 提供发票, 七天退换
        promise = {}
        if 'xiaobao1' not in rateresp: # it's a tmall store
            promise['ZPBZ'] = 'promise.php#ZPBZ' in rateresp
            promise['TGFP'] = 'promise.php#TGFP' in rateresp
            promise['QTTH'] = 'promise.php#QTTH' in rateresp
            promise['xiaofei'] = True
            info['promise'] = [key for key in promise if promise[key]]
        else:
            xiaobao = re.compile('class="xiaobao-box".*?</ul', re.DOTALL).search(rateresp).group()
            info['promise'] = re.compile('<span class="([^"]+)"').findall(xiaobao)
        try:
            info['charge'] = re.compile(r'class="charge".*?([0-9,.]+)').search(rateresp).group(1)
        except:
            info['charge'] = ''

        body = PyQuery(rateresp.decode("gbk", "ignore"))
        ele = body.find("div.info-block.info-block-first ul li")
        
        for e in ele:
            if u"当前主营" in PyQuery(e).text():
                info['main_sale'] = PyQuery(e).text().replace(u"当前主营：", "").strip()
            elif u"所在地区" in PyQuery(e).text():
                info['area'] = PyQuery(e).text().replace(u"所在地区：", "").strip()
            elif u"创店时间： " in PyQuery(e).text():
                info['create_shop'] = PyQuery(e).text().replace(u"创店时间： ", "").strip()                
        if 'main_sale' not in info:
            info['main_sale'] = ''
                
        ele = body.find("div.info-block ul.sep li:first-child")
        if ele:
            try:
                info["rank_num"] = int(PyQuery(ele).text().replace(u"卖家信用：", "").strip())
            except:
                info["rank_num"] = 0
        
        info['rating'] = re.compile(r'class="count">([^<]*).*?class="percent ([a-z]*)[^>]*>([^<]*)', re.DOTALL).findall(rateresp)
        info['rates'] = re.compile(r'class="small-star-no[45]".*?(\d+\.\d+)%', re.DOTALL).findall(rateresp)
        info['good_rating'] = sum(float(r) for r in info['rates'])/3
        return info
    except:
        traceback.print_exc()
        return {}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Listing Ids in Shop')
    parser.add_argument('--shopid', '-s', type=int, help='taobao shopid, e.g. 33003356', required=True)
    option = parser.parse_args()
    print('Shop Info:')
    shop = get_shop(option.shopid)
    print json.dumps(shop, indent=4)

if __name__ == '__main__':
    main()
