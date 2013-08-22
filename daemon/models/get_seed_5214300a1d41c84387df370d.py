#coding:utf-8
from twisted.internet import reactor, defer

@defer.inlineCallbacks
def get_seed(obj_self):
    seed = yield obj_self.redis.pop("list_cat_rets")
    defer.returnValue(seed)


if __name__ == "__main__":
    import txredisapi
    class d:pass
    
    @defer.inlineCallbacks
    def main():
        a = d()
        a.redis = yield txredisapi.Connection()
        seed = yield get_seed(a)
        print seed
        reactor.stop()
    
    reactor.callLater(0, main)
    reactor.run()
    
