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

from twisted.application import internet, service
import pymongo
import setting
import funs
import json
import subprocess
import urllib2

from settings import ADMIN_HOST

class SubProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, sptl, spiders, kw):
        self.sptl = sptl
        self.spiders = spiders
        self.kw = kw

    def childDataReceived(self, childFD, data):
        #self.sptl.monitor
        try:
            for pid, sid in self.sptl.monitor_ps.iteritems():
                print pid, sid
                if pid == self.pid:
                    self.sptl.publish("psmonitor", data, eligible=[sid])
        except Exception, e:
            print e
        protocol.ProcessProtocol.childDataReceived(self, childFD, data)

    def connectionMade(self):
        self.pid = self.transport.pid
        self.spiders[self.pid] = self.kw
        self.sptl.status_refresh()

    def processExited(self, reason):
        print "processExited, status %s" % (reason.value.exitCode,)
        del self.spiders[self.pid]
        
        try:
            del self.sptl.monitor_ps[self.pid]
        except:
            pass
        
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

        elif event["act"] == "restart":
            self.spider_restart(event["kw"])
        
        elif event["act"] == "status":
            self.status_refresh()

        elif event["act"] == "monitor":
            self.monitor_ps[event["pid"]] = event["sid"]
            
        elif event["act"] == "shutdown":
            os.system("init 0")
        
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

    def restart_spiders_every(self, seconds=20*60):
        """ restart spiders every ?? seconds """
        print 'restarting all spiders', self.factory.spiders
        for pid, kw in self.factory.spiders.items():
            self.spider_restart(pid, kw)
        reactor.callLater(seconds, self.restart_spiders_every, seconds)
    
    def spider_restart(self, pid, kw):
        """ restart spider process
        
        This method got called by factory every 20 minutes
        OS(EC2's VM Controller) may degrade long running process's performance
        We work around this problem by a brute force restart(Disgusting, but works)
        """
        try:
            self.spider_stop([pid])
            self.spider_start(kw)
        except Exception, e:
            print e

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
        reactor.spawnProcess(pp, 
                             sys.executable, args=args,
                             env={
                                  'PYTHONPATH':'/srv/ataobao:$PYTHONPATH',
                                  'ENV':'TEST',
                                  },
                             path='/srv/ataobao/crawler')
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

        self.monitor_ps = {}
        try:
            burl = "http://169.254.169.254/latest/meta-data"
            
            runner_info = {}
            runner_info["spider_name"] = open('/tmp/schd_name.conf').read().strip('\r\n')
            runner_info["uptime"] = subprocess.check_output(["uptime"])
            runner_info["hostname"] = urllib2.urlopen("%s/public-hostname" % burl).read()
            runner_info["instance_id"] = urllib2.urlopen("%s/instance-id" % burl).read()
            
            log.msg(json.dumps(runner_info))
            
            self.call("set_info", json.dumps(runner_info))
            
        except Exception, e:
            log.msg('set_schd_name err:%s' % e)

        else:
            if 'spider' in runner_info["spider_name"]:
                from random import randint
                self.restart_spiders_every(randint(60*5, 60*10))
            reactor.callLater(30, self.init_session)

        
    def init_session(self):
        
        if self.factory.is_first == 0:
                
            try:
                for line in open('/tmp/init_cmd.conf').readlines():
                    cmd = line.strip('\n')
                    event = {
                             'act':'start',
                             'kw':{'cmd':cmd}
                             }
                    print event
                    
                    self.process_msg('init_cmd', event)
            except Exception, e:
                log.msg('init_cmd err:%s' % e)
            self.factory.is_first = 1
            

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
        self.is_first = 0
        
    def clientConnectionFailed(self, connector, reason):
        log.msg("connect fail, wait 3 second.")
        reactor.callLater(3, connector.connect)
        
    def clientConnectionLost(self, connector, reason):
        log.msg("connect fail, wait 3 second.")
        reactor.callLater(3, connector.connect)



import os, signal


def start():
    
    
    log.startLogging(sys.stdout)
    factory = SpiderClientFactory("ws://{}:9000".format(ADMIN_HOST))
    factory.protocol = TaskClientProtocol
    connectWS(factory)
    
    def killGroup():
        for pid, kw in factory.spiders.iteritems():
            try:
                p = psutil.Process(int(pid))
                p.terminate()
            except Exception, e:
                print e
    reactor.addSystemEventTrigger('before', 'shutdown', killGroup)
    
if __name__ == "__main__":
    reactor.callWhenRunning(start)
    reactor.run()
    
    
if __name__ == "__builtin__":
    reactor.callWhenRunning(start)
    application = service.Application('spider_runner')
    
    

