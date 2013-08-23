#coding: utf-8

import sys
import os

from twisted.python import log
from twisted.internet import reactor, defer, protocol, error
from twisted.web.error import Error
from twisted.internet.defer import Deferred, \
                                   DeferredList, \
                                   gatherResults, \
                                   returnValue, \
                                   inlineCallbacks
from autobahn.websocket import connectWS
from autobahn.wamp import WampClientFactory, WampClientProtocol
import pymongo
import psutil
from bson.objectid import ObjectId
from twisted.web.client import getPage

from lxml import etree

from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web.http_headers import Headers
import time
from spider_tx import TxSpiderEngine
from multiprocessing import Process

from twisted.internet.error import ReactorAlreadyRunning


import pymongo
import setting
import funs


class SubProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, sptl, spiders, kw):
        self.sptl = sptl
        self.spiders = spiders
        self.kw = kw

    def connectionMade(self):
        self.pid = self.transport.pid
        self.spiders[self.pid] = self.kw
        self.sptl.status_refresh()
        
    def processExited(self, reason):
        print "processExited, status %s" % (reason.value.exitCode,)
        del self.spiders[self.pid]
        self.sptl.status_refresh()
    
    
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
        if not event.has_key("act"): return
        
        if event["act"] == "start":
            self.spider_start(event["kw"])
            
        elif event["act"] == "stop":
            self.spider_stop(event["pid_list"])

        elif event["act"] == "status":
            self.status_refresh()
        
    def status_refresh(self):
        ret_msg = {
                   "sid": self.session_id,
                   "msg_type":"status_change"
                   }
        por_list = []
        for pid, kw in self.factory.spiders.iteritems():
            info = {
                    "pid":pid,
                    'cmd':kw["cmd"]
                    #"threads": kw["threads"],
                    #"spider": kw["spider"],
                    }
            por_list.append(info)
        ret_msg["por_list"] = por_list
        self.publish("webadmin", ret_msg)
    
    def spider_stop(self, pid_list):
        for pid in pid_list:
            try:
                p = psutil.Process(int(pid))
                p.terminate()
            except Exception, e:
                print e
            
            
    def spider_start(self, kw):
        '''
        '''
        pp = SubProcessProtocol(self, self.factory.spiders, kw)
        args = [sys.executable] + kw['cmd'].split(' ')
        reactor.spawnProcess(pp, sys.executable, args=args)
#         for i in range(0, kw["process"]):
#             pp = SubProcessProtocol(self, self.factory.spiders, kw)
#             args = [sys.executable, "spider_tx.py", kw["spider"], str(kw["threads"])]
#             args = [sys.executable, "crawler/worker.py", "-w", "shop", "-p", "10"]
#             args = [sys.executable, "crawler/tbcat.py", "-c", "16"]
#             print args
#             reactor.spawnProcess(pp, sys.executable, args=args)
            
    def onSessionOpen(self):
        log.msg("peerstr: %s" % self.peerstr)
        self.subscribe("spider", self.process_msg)
        log.msg("sub 'spider' channl finish")

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
        self.spiders = {}
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("connect fail, wait 3 second.")
        reactor.callLater(3, connector.connect)
        
    def clientConnectionLost(self, connector, reason):
        log.msg("connect fail, wait 3 second.")
        reactor.callLater(3, connector.connect)



def spider_runner_daemon():
    pass


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
    
    import os, signal
    
    def killGroup():
        for pid, kw in factory.spiders.iteritems():
            try:
                p = psutil.Process(int(pid))
                p.terminate()
            except Exception, e:
                print e

    reactor.addSystemEventTrigger('before', 'shutdown', killGroup)
    reactor.run(1)
