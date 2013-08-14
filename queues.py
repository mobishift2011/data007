#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import threading
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
        self.hashkey = '{key}-timehash'.format(key=key)
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
                    result = unpack(result)
                    break
                else:
                    t += 0.05
                    time.sleep(0.05)
        else:
            result = conn.spop(self.key)
            result =  unpack(result) if result is not None else None

        if result:
            self.task_start(result)
        return result

    def task_start(self, result):
        """ save start time in redis hash """
        conn.hsetnx(self.hashkey, pack(result), pack(time.mktime(time.gmtime())))

    def task_done(self, result):
        """ clear start time in redis hash, indicating the task done """
        conn.hdel(self.hashkey, pack(result))

    def clean_task(self):
        """ check task hash for unfinished long running tasks, requeue them """
        timeout = 90 if 'item' in self.key else 1800
        items = []
        for field, value in conn.hgetall(self.hashkey).iteritems():
            start_time = unpack(value)
            if time.mktime(time.gmtime()) - start_time > timeout:
                items.append(field)

        # we call sadd directly because we don't want to unpack then pack fields
        if items:
            print('requeuing {} to {}'.format([unpack(item) for item in items], self.key))
            pipeline = conn.pipeline()
            pipeline.hdel(self.hashkey, *items)
            pipeline.sadd(self.key, *items)
            pipeline.execute()

    def background_cleaning(self):
        while True:
            self.clean_task()
            time.sleep(60)
        
def poll(queues, timeout=None):
    """ poll item from queues (order by priority) """
    #print('polling {}'.format(queues))
    queues = sorted(queues, key=lambda x:x.priority, reverse=True)
    t = 0
    while timeout is None or t < timeout:
        for q in queues:
            result = q.get(block=False)
            if result is not None:
                return q, result
        t += 0.05
        time.sleep(0.05)

ai1 = Queue('ataobao-item-queue-1', 3)
ai2 = Queue('ataobao-item-queue-2', 1)
as1 = Queue('ataobao-shop-queue-1')
af1 = Queue('ataobao-fail-queue-1')
