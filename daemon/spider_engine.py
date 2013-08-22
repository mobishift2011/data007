#coding: utf-8

import sys
import os
import gevent, time

from twisted.python import log
from twisted.internet import reactor, defer
from twisted.web.error import Error
from twisted.internet.defer import Deferred, \
                                   DeferredList, \
                                   gatherResults, \
                                   returnValue, \
                                   inlineCallbacks
from autobahn.websocket import connectWS
from autobahn.wamp import WampClientFactory, WampClientProtocol
import pymongo
from bson.objectid import ObjectId
import client2 as client


from lxml import etree

from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.http_headers import Headers
from twisted.python import log


import pymongo
import setting
import json
from bson.json_util import *
import signal, os
import funs
import txmongo
import txredisapi

import traceback


def getPagePrxoy(url, proxy=None, contextFactory=None,
                       *args, **kwargs):
    '''
    proxy=
    {
    host:192.168.1.111,
    port:6666
    }
    '''
    
    kwargs["timeout"] = 60
    if proxy is None:
        scheme, host, port, path = client._parse(url)
        factory = client.HTTPClientFactory(url, *args, **kwargs)
        if scheme == b'https':
            from twisted.internet import ssl
            if contextFactory is None:
                contextFactory = ssl.ClientContextFactory()
            reactor.connectSSL(client.nativeString(host), port, factory, contextFactory)
        else:
            reactor.connectTCP(client.nativeString(host), port, factory)
        return factory
    else:
        factory = client.HTTPClientFactory(url, *args, **kwargs)
        reactor.connectTCP(proxy["host"], proxy["port"], factory)
        return factory
    

class SpiderEngine():
    def __init__(self, setting, spider, threads):
        self.setting = setting
        self.threads = int(threads)
        self.spider = spider
        
        signal.signal(signal.SIGINT, self.sig_handler)
        
    def sig_handler(self, signum, frame):
        print "init_spider:reload spider"
        reactor.callLater(0, self.init_spider)
        
    def load_conf(self):
        spider_conf = {}
        conn = pymongo.Connection(self.setting.CONF_MONGO_HOST, self.setting.CONF_MONGO_PORT)
        row = conn.taobao.spider.find_one({"name":self.spider})
        spider_conf = dict(row)
        open("models/get_seed_%s.py" % str(spider_conf["_id"]), "w").write(spider_conf["get_seed"].encode("utf-8"))
        
        spider_conf["navi_models"] = []
        for navi in spider_conf["navi_list"]: 
            navi_row = conn.taobao.spider_navi.find_one({"_id":navi})
            open("models/navi_%s.py" % str(navi_row["_id"]), "w").write(navi_row["python_code"].encode("utf-8"))
            spider_conf["navi_models"].append(dict(navi_row))
        redis_queue = conn.taobao.redis_queue.find({"_id":spider_conf["_id"]})
        spider_conf["redis_queue"] = list(redis_queue)
        return spider_conf
    
    
    def init_spider(self):
        self.conf = self.load_conf()
        imp_str = "from models import get_seed_%s as m" % str(self.conf["_id"])
        exec(imp_str)
        reload(m)
        self.conf["get_seed_model"] = m
        
        self.navi_list = []
        for navi in self.conf["navi_models"]:
            imp_str = "from models import navi_%s as m" % str(navi["_id"])
            exec(imp_str)
            reload(m)
            self.navi_list.append({
                                   "conf":navi,
                                   "obj" :m.SpiderBase()
                                  })
        return True


    @defer.inlineCallbacks
    def init_database(self):
        self.mongo = yield txmongo.MongoConnection(host=self.setting.DATA_MONGO_HOST, port=self.setting.DATA_MONGO_PORT)
        self.redis = yield txredisapi.Connection(host=self.setting.QUEUE_REDIS_HOST, port=self.setting.QUEUE_REDIS_PORT)
        #yield self.mongo.admin.authenticate("root", "chenfuzhi")
        defer.returnValue(True)

    
    @defer.inlineCallbacks
    def start(self):
        self.init_spider()
        yield self.init_database()
        for i in range(0, self.threads):
            reactor.callLater(0, self._run)
    
    
    @defer.inlineCallbacks
    def _run(self):
        while 1:
            try:
                log.msg("begin#####")
                
                url = yield self.conf["get_seed_model"].get_seed(self)
                
                if url is None:
                    log.msg("url is None, wait 3 second")
                    yield funs.wait(3)
                    continue
                
                log.msg("successfully###get_seed: %s" % url)
                
                
                navi_obj = None
                for n in self.navi_list:
                    ret = yield n["obj"].check_seed(url)
                    if ret is True:
                        navi_obj = n
                        break
                    
                if navi_obj is None:
                    log.msg("not navi is checked wait 3 second")
                    yield funs.wait(3)
                    continue
                
                log.msg("successfully###navi_id:%s is checked. " % navi_obj["conf"]["_id"])
                
                
                url = yield navi_obj["obj"].process_seed(url)
                agent = navi_obj["obj"].process_agent()
                headers = yield navi_obj["obj"].process_headers()
                cookies = yield navi_obj["obj"].process_cookies()
                proxyip = yield navi_obj["obj"].process_proxyip()
                
                if proxyip is not None:
                    factory = yield getPagePrxoy(url.encode("utf-8"), 
                                                 proxy=proxyip, 
                                                 headers=headers,
                                                 agent=agent,
                                                 cookies=cookies
                                                 )
                else:
                    factory = yield getPagePrxoy(url.encode("utf-8"), 
                                                 headers=headers,
                                                 agent=agent,
                                                 cookies=cookies
                                                 )
                    
                log.msg("crawl: %s" % url)
                request = {
                           "url":url,
                           "headers":headers,
                           "proxyip":proxyip,
                           }
                
                
                body = yield factory.deferred
                headers = factory.response_headers
                rets = yield navi_obj["obj"].process_response_page(request, headers, body)
                yield navi_obj["obj"].process_rets_pipeline(self, rets)
                
            except:
                traceback.print_exc()
                yield funs.wait(3)
                
                
    
if __name__ == "__main__":
#     import argparse
#     parser = argparse.ArgumentParser(description='Call Scheduler with arguments')
#     parser.add_argument('--spider', '-s', dest="spider", help='worker type, can be "full", "update", "item"', required=True)
#     parser.add_argument('--test', '-t', dest="is_test", type=bool, help='category id if worker type in "full" or "update"', default=False)
#     option = parser.parse_args()
#     print option
    import sys
    
    log.startLogging(sys.stdout)
    
    if len(sys.argv) < 3:
        print "please input: spider, threads"
    else:
        engine = SpiderEngine(setting, sys.argv[1], sys.argv[2])
        reactor.callWhenRunning(engine.start)
        reactor.run()
    
    

