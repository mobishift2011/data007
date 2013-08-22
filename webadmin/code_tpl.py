#coding:utf-8

from twisted.internet import reactor, defer
import re
import json
from StringIO import StringIO
import gzip
        
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
    
    @defer.inlineCallbacks
    def process_headers(self):
        yield
        headers = {}
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.95 Safari/537.36"
        headers["Accept-Encoding"] = "gzip,deflate,sdch"
        headers["Accept-Language"] = "zh-CN,zh;q=0.8"
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        headers["Cache-Control"] = "max-age=0"
        headers["Connection"] = "keep-alive"        
        defer.returnValue(headers)
        
    
    @defer.inlineCallbacks
    def process_cookies(self):
        yield
        cookies = {}
        cookies[""] = ""
        cookies[""] = ""
        cookies[""] = ""
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
            
        body = body.decode("gbk").encode("utf-8")
        jobj = json.loads(body)
        
        total = jobj['selectedCondition']['totalNumber']
        
        if u'万' in total or int(total)>9500:
            if jobj['cat'] is None:
                for prop in jobj['propertyList']:
                    for p in prop['propertyList']:
                        url = "%s&ppath=%s" % (request["url"], p["value"])
                        rets["urls"].append(url)
            else:
                for glist in jobj['cat']['catGroupList']:
                    if not glist.has_key("catList"): continue
                    for l in glist["catList"]:
                        url = "http://list.taobao.com/itemlist/default.htm?json=on&cat=%s" % l["value"]
                        rets["urls"].append(url)
        else:
            rets["list_urls"].append(request["url"])
        print rets
        defer.returnValue(rets)

        
    @defer.inlineCallbacks
    def process_rets_pipeline(self, self_obj, rets):
        yield
        for url in rets["urls"]:
            yield self_obj.redis.lpush("list_cat", url)

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
