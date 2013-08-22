#coding: utf-8


from gevent import monkey; monkey.patch_all()

import sys
import os
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
from twisted.web.client import getPage

from lxml import etree

from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.http_headers import Headers
from multiprocessing import Process
from spider_base import SpiderBase
from funs import *
import setting

from twisted.web import client


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
        return factory.deferred
    else:
        factory = client.HTTPClientFactory(url, *args, **kwargs)
        reactor.connectTCP(proxy["host"], proxy["port"], factory)
        return factory.deferred



class TxSpiderEngine(SpiderBase):
    def __init__(self, setting, spider, threads):
        '''
        :param store:
        '''
        self.setting = setting
        self.spider = spider
        self.threads = threads
    
    @defer.inlineCallbacks
    def init_db(self):
        
        self.redis = None
        self.mongo_conf = None
        self.mongo = None
        
        try:
            self.mongo_conf = yield txmongo.MongoConnection(host=self.setting.CONF_MONGO_HOST, port=self.setting.CONF_MONGO_PORT)
            self.mongo = yield txmongo.MongoConnection(host=self.setting.DATA_MONGO_HOST, port=self.setting.DATA_MONGO_PORT)
            self.redis = yield txredisapi.Connection(host=self.setting.QUEUE_REDIS_HOST, port=self.setting.QUEUE_REDIS_PORT)
            yield self.mongo.admin.authenticate("root", "chenfuzhi")
            yield self.mongo_conf.admin.authenticate("root", "chenfuzhi")
            
            defer.returnValue(True)
        except Exception, e:
            import traceback
            traceback.print_exc()
            defer.returnValue(False)
            
    @defer.inlineCallbacks
    def load_conf(self):
        conn = pymongo.Connection(host=self.setting.CONF_MONGO_HOST, port=self.setting.CONF_MONGO_PORT)
        
        row = conn.taobao.spider.find_one({"name":self.spider})
        self.conf = dict(row)

        rows = conn.taobao.redis_queue.find({"_id":self.conf["_id"]}, sort=("prio", 1))
        self.queues = list(rows)
        
        
    @defer.inlineCallbacks
    def start(self):
        while 1:
            ret = yield self.init_db()
            if ret is False:
                yield wait(3)
            else:
                break
        
        for i in range(0, 100):
            reactor.callLater(0, self._run, i)
            
    @defer.inlineCallbacks
    def _run(self, worker_id):
        
        self.run_count = 0
        while 1:

            #url = yield self.get_url()
#             proxyip = yield self.get_proxyip()
#             cookie = yield self.get_cookie()
            url = "http://list.taobao.com/itemlist/default.htm?atype=b&cat=16&viewIndex=12&isnew=2&yp4p_page=0&commend=all#J_Filter"
            ret = yield getPagePrxoy(url)
            log.msg(len(ret))
            
            yield wait(0.001)
            
    @defer.inlineCallbacks
    def get_url(self):
        url = None
        while 1:
            for q in self.queues:
               url = yield self.redis.lpop(str(q["_id"]))
               if url is not None:
                   defer.returnValue(url)
            if url is None:
                yield wait(3)
                    
    @defer.inlineCallbacks
    def get_cookie(self):
        url = None
        while 1:
            for q in self.queues:
               url = yield self.redis.lpop(str(q["_id"]))
               if url is not None:
                   defer.returnValue(url)
            if url is None:
                yield wait(3)
                

    @defer.inlineCallbacks
    def get_proxyip(self):
        url = None
        while 1:
            for q in self.queues:
               url = yield self.redis.lpop(str(q["_id"]))
               if url is not None:
                   defer.returnValue(url)
            if url is None:
                yield wait(3)
                   
                
por_list = []

if __name__ == "__main__":

    from optparse import OptionParser
    
    parser = OptionParser(usage='usage: %prog [options]')
    # commands
    parser.add_option('--daemon', dest='daemon', action="store_true", help='run deamon', default=False)
    
    options, args = parser.parse_args()
    print options, args
        
    if options.daemon:
        try:
            pid = os.fork()
            if pid > 0:
                print 'PID: %d' % pid
                os._exit(0)
            log.startLogging(open('/var/log/scanipd.log', 'a'))
        except OSError, error:
            print 'Unable to fork. Error: %d (%s)' % (error.errno, error.strerror)
            os._exit(1)
    else:
        log.startLogging(sys.stdout)
        

    print sys.argv
    engine = TxSpiderEngine(setting, sys.argv[1], sys.argv[2])
    reactor.callLater(0, engine.start)
    reactor.run()
    



