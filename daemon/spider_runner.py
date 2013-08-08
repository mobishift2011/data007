#coding: utf-8

import sys
import os

from twisted.python import log
from twisted.internet import reactor
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
import time
from spider_tx import TxSpiderEngine
from multiprocessing import Process
import pymongo
import setting
import funs

def por_start(**kw):
    @defer.inlineCallbacks
    def start(**kw):
        log.msg("begin install store")
        store = funs.Store(setting)
        ret = yield store.instatll()
        if ret is False:
            log.err("store install error !!!")
            reactor.stop()
        else:
            log.msg("install successfully")
        por = TxSpiderEngine(store, **kw)
        por.start()
        
    conn = pymongo.Connection(setting.CONF_MONGO_HOST, setting.CONF_MONGO_PORT)
    conn.admin.authenticate(setting.CONF_MONGO_USER, setting.CONF_MONGO_PWD)
    row = conn.taobao.spider.find_one({"name":kw["spider"]})
    queues = conn.taobao.redis_queue.find({"spider":row["_id"]})
    row = dict(row)
    row["queue_list"] = list(queues)
    kw["row"] = row
    
    reactor.callWhenRunning(start, **kw)
    reactor.run()
    
    
class TaskClientProtocol(WampClientProtocol):
    """
    Demonstrates simple Publish & Subscribe (PubSub) with Autobahn WebSockets.
    """
    def process_msg(self, topic, event):
        '''
        
        :param topic:
        :param event:
        {
            "act":"start/stop",
            "kw":{
                  "spider": "taobao",
                  "process": 1,
                  "workers": 100
                  }
        }
        '''
        log.msg("topic:%s, event: %s" % (str(topic), str(event)))
        if event["act"] == "start":
            self.spider_start(event["kw"])
        elif event["act"] == "stop":
            self.spider_stop()
        elif event["act"] == "status":
            self.spider_status()
        
        
    def spider_status(self):
        pass
    
        
    def spider_stop(self):
        for s in self.factory.spiders:
            s.terminate()
    
    def spider_start(self, kw):
        '''
        '''
        for i in range(0, kw["process"]):
            p = Process(target=por_start, kwargs=kw)
            p.start()
            self.factory.spiders.append(p)
        
    def onSessionOpen(self):
        log.msg("peerstr: %s" % self.peerstr)
        self.subscribe("spider", self.process_msg)
        log.msg("sub 'spider' channl finish")
        reactor.callLater(3, self.pub_info)

    def connectionLost(self, reason):
        WampClientProtocol.connectionLost(self, reason)
            
    def pub_info(self):
        if self.connected == 1:
            msg = {"process":len(self.factory.spiders)}
            self.publish("webadmin", msg)
            print msg
            reactor.callLater(3, self.pub_info)
      
class SpiderClientFactory(WampClientFactory):
    def __init__(self, url, debug = False, debugCodePaths = False, debugWamp = False, debugApp = False):
        WampClientFactory.__init__(self, url, debug = debug, debugCodePaths = debugCodePaths)
        self.spiders = []
        
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("connect fail, wait 3 second.")
        reactor.callLater(3, connector.connect)
        
    def clientConnectionLost(self, connector, reason):
        log.msg("connect fail, wait 3 second.")
        reactor.callLater(3, connector.connect)

if __name__ == '__main__':
    from optparse import OptionParser
    
    parser = OptionParser(usage='usage: %prog [options]')
    parser.add_option('--daemon', dest='daemon', action="store_true", help='run deamon', default=False)
    parser.add_option('--num', dest='num', help='run workers default:10', type=int, default=1)

    options, args = parser.parse_args()
    print options, args

        
    if options.daemon:
        try:
            pid = os.fork()
            if pid > 0:
                print 'PID: %d' % pid
                os._exit(0)
            log.startLogging(open('/var/log/spider.log', 'a'))
        except OSError, error:
            print 'Unable to fork. Error: %d (%s)' % (error.errno, error.strerror)
            os._exit(1)
    else:
        log.startLogging(sys.stdout)
        
    from twisted.python.logfile import DailyLogFile

    log.startLogging(sys.stdout)
    factory = SpiderClientFactory("ws://localhost:9000")
    factory.protocol = TaskClientProtocol
    connectWS(factory)
    reactor.run()
