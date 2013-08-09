#coding: utf-8
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

class TxSpiderEngine(SpiderBase):
    def __init__(self, store, **kw):
        '''
    kw: {
            "workers": 100,
            "row": {
                     "name":"taobao",
                     "queue_list": [
                     ],
                     "navi_list": [
                        "rule":"",
                        "code":""
                     ]
                   }
        }
        :param store:
        '''
        self.store = store
        self.setting = store.setting
        self.kw = kw
    
    def start(self):
        for i in range(0, self.threads):
            reactor.callLater(0, self._run, i)
            
    @defer.inlineCallbacks
    def _run(self, worker_id):
        
        self.run_count = 0
        while 1:
            ret = yield getPage("http://www.51job.com")
            log.msg(ret)
            yield wait(0.001)
            

    
por_list = []

if __name__ == "__main__":

    from optparse import OptionParser
    
    parser = OptionParser(usage='usage: %prog [options]')
    # commands
    parser.add_option('--daemon', dest='daemon', action="store_true", help='run deamon', default=False)
    parser.add_option('--stdout', dest='stdout', action="store_true", help='run deamon', default=False)
    
    parser.add_option('--num', dest='num', help='run workers default:10', type=int, default=1)

    options, args = parser.parse_args()
    print options, args
        
    if options.daemon:
      try:
        # Store the Fork PID
        pid = os.fork()
    
        if pid > 0:
          print 'PID: %d' % pid
          os._exit(0)
      except OSError, error:
        print 'Unable to fork. Error: %d (%s)' % (error.errno, error.strerror)
        os._exit(1)
        
    from twisted.python.logfile import DailyLogFile
    if options.stdout:
        log.startLogging(sys.stdout)
    else:
        log.startLogging(open('/var/log/scanipd.log', 'a'))

    for i in range(0, options.num):
        p = Process(target=por_start, args=(ScanEngine, 4000))
        p.start()
        por_list.append(p)



