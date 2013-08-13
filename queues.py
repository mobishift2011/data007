#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
from msgpack import unpackb as unpack, packb as pack

from settings import QUEUE_URI

host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(QUEUE_URI).groups()
conn = redis.Redis(host=host, port=int(port), db=int(db))

##################################
# Current Set Implementation
##################################
class Queue(object):
    """ a simple queue wrapper for redis, provides Queue.Queue like methods """
    def __init__(self, key, priority=1):
        self.key = key
        self.priority = priority

    def qsize(self):
        return conn.scard(self.key)

    def put(self, *items):
        """ put item(s) into queue """
        if items:
            return conn.sadd(self.key, *[pack(item) for item in items])
        else:
            return 0

    def get(self, block=True, timeout=None):
        """ get item from queue, block if needed """
        if block:
            t = 0  
            while timeout is None or t < timeout:
                result = conn.spop(self.key)
                if result:
                    return unpack(result)
                else:
                    t += 0.05
                    time.sleep(0.05)
        else:
            result = conn.spop(self.key)
            return unpack(result) if result is not None else None

def poll(queues, timeout=None):
    """ poll item from queues (order by priority) """
    #print('polling {}'.format(queues))
    queues = sorted(queues, key=lambda x:x.priority, reverse=True)
    t = 0
    while timeout is None or t < timeout:
        for q in queues:
            result = q.get(block=False)
            if result is not None:
                return result
        t += 0.05
        time.sleep(0.05)

ai1 = Queue('ataobao-item-queue-1', 3)
ai2 = Queue('ataobao-item-queue-2', 1)
as1 = Queue('ataobao-shop-queue-1')
af1 = Queue('ataobao-fail-queue-1')
