#coding:utf-8

from twisted.internet import reactor, defer



class SpiderBase:
    def __init__(self):
        pass
    
    @defer.inlineCallbacks
    def get_seed(self):
        pass

    @defer.inlineCallbacks
    def check_seed(self, seed):
        defer.returnValue(True)
    
    @defer.inlineCallbacks
    def request_seed(self, seed):
        pass
    
    @defer.inlineCallbacks
    def request_header(self):
        pass

    def _run(self):
        pass


if __name__ == "__main__":
    
    
    @defer.inlineCallbacks
    def main():
        s = SpiderBase()
        ret = yield s.check_seed("http://list.taobao.com/itemlist/default.htm?json=on&cat=16")
        print "check_seed:", ret

        reactor.stop()
        
    reactor.callLater(0, main)
    reactor.run()

