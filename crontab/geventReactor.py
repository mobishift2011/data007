#coding:utf-8

import geventreactor; geventreactor.install()
from twisted.internet import reactor, defer
from twisted.web.http_headers import Headers
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from twisted.web.client import getPage, HTTPClientFactory, Agent, _parse, nativeString

import gevent, time
from gevent import monkey; monkey.patch_socket()
import urllib2


cnt1, cnt2 = [0] *2
__url = "http://www.51job.com"

def greencount():
    global cnt1, cnt2
    while 1:
        try:
            ret = urllib2.urlopen(__url, timeout=30).read()
            cnt1 += 1
            print "                         greencount", len(ret), cnt1
        except Exception, e:
            print "gevent", e



@defer.inlineCallbacks
def txgetpage():
    global cnt1, cnt2
    while 1:
        try:
            ret = yield getPage(__url, timeout=30)
            cnt2 += 1
            print "############################txgetpage", len(ret), cnt2
        except Exception, e:
            print "twisted", e



for i in range(0, 1):
    gevent.Greenlet.spawn(greencount)
    reactor.callWhenRunning(txgetpage)


reactor.run()


