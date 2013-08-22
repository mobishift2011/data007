#coding:utf-8
from twisted.internet import reactor, defer

@defer.inlineCallbacks
def get_seed(obj_self):
    seed = yield obj_self.redis.pop("list_cat")
    defer.returnValue(seed)


if __name__ == "__main__":
    import os
    os.chroot("../")
    from spider_engine import SpiderEngine
    import setting
    
    engine = SpiderEngine(setting, 'taobao', 1)
    reactor.callLater(0, engine.test_get_seed)
    reactor.run()
