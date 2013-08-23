from gevent import monkey; monkey.patch_all()
import  time
import gevent

def f():
    time.sleep(1)
    return 'haha'

def callback(greenlet):
    print greenlet.value

gevent.spawn(f).link(callback)

gevent.sleep(10)

