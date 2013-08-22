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
from multiprocessing import Process



class SpiderBase:
    def __init__(self):
        pass
    




