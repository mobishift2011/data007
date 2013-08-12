#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import redis
from msgpack import unpackb as unpack, packb as pack

from settings import QUEUE_URI

host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(QUEUE_URI).groups()
conn = redis.Redis(host=host, port=int(port), db=int(db))

class Queue(object):
    """ a simple queue wrapper for redis, provides Queue.Queue like methods """
    def __init__(self, key, priority=1):
        self.key = key
        self.priority = priority

    def qsize(self):
        return conn.llen(self.key)

    def put(self, *items):
        """ put item(s) into queue """
        return conn.rpush(self.key, *[pack(item) for item in items])

    def get(self, block=True, timeout=None):
        """ get item from queue, block if needed """
        if block:
            result = conn.blpop(self.key, timeout)
            return unpack(result[1]) if result is not None else None
        else:
            result = conn.lpop(self.key)
            return unpack(result) if result is not None else None

def poll(queues, timeout=None):
    """ poll item from queues (order by priority) """
    queues = sorted(queues, key=lambda x:x.priority, reverse=True)
    result = conn.blpop([q.key for q in queues], timeout=timeout)
    return unpack(result[1]) if result is not None else None

ai1 = Queue('queue-ataobao-item-1', 3)
ai2 = Queue('queue-ataobao-item-2', 1)
as1 = Queue('queue-ataobao-shop-1', 1)
