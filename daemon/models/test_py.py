#coding:utf-8

from twisted.internet import reactor, defer
import re
import json
from StringIO import StringIO
import gzip
from urlparse import urlparse, parse_qs
import urllib
        
class SpiderBase:
    def __init__(self):
        pass
    
    @defer.inlineCallbacks
    def check_seed(self, seed):
        yield
        if re.match(r"http://list.taobao.com/itemlist/default.htm.*", seed):
            defer.returnValue(True)
        else:
            defer.returnValue(False)

    @defer.inlineCallbacks
    def process_seed(self, seed):
        yield
        defer.returnValue(seed)
    
    def process_agent(self):
        return "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36"
        
    @defer.inlineCallbacks
    def process_headers(self):
        yield
        headers = {}
        #headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36"
        headers["Accept-Encoding"] = "gzip,deflate,sdch"
        headers["Accept-Language"] = "zh-CN,zh;q=0.8"
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers["Cache-Control"] = "max-age=0"
        headers["Connection"] = "keep-alive"
        defer.returnValue(headers)
        
    
    @defer.inlineCallbacks
    def process_cookies(self):
        yield
        cookiestr = "cna=ZdqRChJTkToCAXTn19EnUyDw; Hm_lvt_9336abc9c7952f45434aca9d356a2aa7=1376543642; _tb_token_=e6e5db373e3eb; v=0; sec=Hesper|116.231.127.77|1376991973|7604f4056ae29520f49501fdb5f07959; tg=4; _cc_=URm48syIZQ%3D%3D; t=0f155844ea4610bc166c7cff42a850a8; unb=1710623422; _nk_=chenfuzhi_test; _l_g_=Ug%3D%3D; cookie2=4882d841f55a0387ab6d468ba56cdfa9; tracknick=chenfuzhi_test; sg=t2c; lgc=chenfuzhi_test; lastgetwwmsg=MTM3Njk5MTk1Ng%3D%3D; cookie1=Vqggi1slqLatqy6JbVBZo1XGGbmbzNzTgspA%2FHPptnY%3D; uc3=nk2=AHLS8ZF5PZJ62hkAYMo%3D&id2=UoYfobmEUCgwUA%3D%3D&lg2=VT5L2FSpMGV7TQ%3D%3D; cookie17=UoYfobmEUCgwUA%3D%3D; mt=ci=0_1; uc1=lltime=1371608717&cookie14=UoLbuUmrzUEIfg%3D%3D&existShop=false&cookie16=VT5L2FSpNgq6fDudInPRgavC%2BQ%3D%3D&cookie21=VT5L2FSpccLuJBrf3T8q&tag=0&cookie15=U%2BGCWk%2F75gdr5Q%3D%3D"        
        cookies = dict(l.split('=', 1) for l in cookiestr.split('; '))
        defer.returnValue(cookies)
        
        
    @defer.inlineCallbacks
    def process_proxyip(self):
        yield
        defer.returnValue(None)


    @defer.inlineCallbacks
    def process_response_page(self, request, headers, body):
        yield
        rets = {
                "urls":[],
                "items":[],
                "list_urls":[]
                }
        if headers.has_key("content-encoding") and headers["content-encoding"] == ['gzip']:    
            buf = StringIO(body)
            f = gzip.GzipFile(fileobj=buf)
            body = f.read()
            print "read gizp"

        ups = urlparse(request["url"])
        body = body.decode("gbk").encode("utf-8")
        jobj = json.loads(body)
        
        total = jobj['selectedCondition']['totalNumber']
        
        if u'万' in total or int(total)>9500:
            if jobj['cat'] is None:
                has_explod = False
                for prop in jobj['propertyList']:
                    for p in prop['propertyList']:
                        params = parse_qs(ups.query)
                        if params.has_key("ppath"):
                            if p["value"].split(':')[0] in [x.split(':')[0] for x in params["ppath"][0].split(";")]:
                                break
                            has_explod = True
                            params["ppath"] = "%s;%s" % (params["ppath"][0], p["value"])
                        else:
                            params["ppath"] = p["value"]
                        url = "http://list.taobao.com/itemlist/default.htm?%s" %  urllib.urlencode(params, doseq=True)
                        rets["urls"].append(url)
                    if has_explod is True:
                        break
            else:
                for cat in jobj['cat']['catList']:
                    url = "http://list.taobao.com/itemlist/default.htm?json=on&cat=%s" % cat["value"]
                    rets["urls"].append(url)
                    
                for glist in jobj['cat']['catGroupList']:
                    if not glist.has_key("catList"): continue
                    for l in glist["catList"]:
                        url = "http://list.taobao.com/itemlist/default.htm?json=on&cat=%s" % l["value"]
                        rets["urls"].append(url)
        else:
            rets["count"] = int(total)
            rets["list_urls"].append(request["url"])
        print rets
        defer.returnValue(rets)


    @defer.inlineCallbacks
    def process_rets_pipeline(self, self_obj, rets):
        yield
        for url in rets["urls"]:
            yield self_obj.redis.rpush("list_cat", url)
        if rets.has_key('count'):
            yield self_obj.redis.incr("list_cat_count", rets["count"])
        for url in rets["list_urls"]:
            yield self_obj.redis.lpush("list_cat_rets", url)
            
        defer.returnValue(rets)

if __name__ == "__main__":
    
    @defer.inlineCallbacks
    def main():
        s = SpiderBase()
        ret = yield s.check_seed("http://list.taobao.com/itemlist/default.htm?json=on&cat=16")
        print "check_seed:", ret

        reactor.stop()
        
    reactor.callLater(0, main)
    reactor.run()
