#coding:utf-8

from twisted.application import internet, service
from twisted.internet import reactor, defer
from twisted.python import log
import setting
import txmongo
import txredisapi
import time
import sys
import socket
import struct
from txmongo import ObjectId
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.web import client
import subprocess
from twisted.internet.protocol import Protocol
import signal
import sys
from multiprocessing import Process
import os
import json



class Store(object):
    def __init__(self, setting):
        self.setting = setting
        self.mongo_remote = None
        self.redis_remote = None
    
    @defer.inlineCallbacks
    def instatll(self):
        try:

            self.mongo = yield txmongo.MongoConnection(host=self.setting.DATA_MONGO_HOST, port=self.setting.DATA_MONGO_PORT)
            self.redis = yield txredisapi.Connection(host=self.setting.QUEUE_REDIS_HOST, port=self.setting.QUEUE_REDIS_PORT)
            yield self.mongo.admin.authenticate("root", "chenfuzhi")
            
            defer.returnValue(True)
        except Exception, e:
            defer.returnValue(False)


def wait(second=1):
    d = defer.Deferred()
    reactor.callLater(second, d.callback, None)
    return d
        

                            
import urllib2
if __name__ == "__main__":
    data = {"uri":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
    print save_ip(data)
#    save_status({"data":"ddddddddddddddddddd"})
#    reactor.callWhenRunning(post_json, {"uri":"chenfuzhisssssssssssss"})
#    reactor.run()



