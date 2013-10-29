#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import time
import redis
import threading

from settings import QUEUE_URI

host, port, db = re.compile('redis://(.*):(\d+)/(\d+)').search(QUEUE_URI).groups()
conn = redis.Redis(host=host, port=int(port), db=int(db))

class Queue(object):
    """ an unordered queue wrapper for redis, provides Queue.Queue like methods

    Usage::

    >>> q = Queue('queue-name', priority=1)
    >>> q.put(1, 2, 3)
    >>> q.get(block=False)
    2

    >>> # do something with item id 2

    when an item is poped, we also updated poping timestamp in a ``hash``
    upon task finish, we should call ``task_done`` to remove that timestamp

    >>> q.task_done(2)

    if a task isn't finished normally, ``task_done`` will not be executed, 
    thus we can findout items spent too much time in that hash, and have 
    them requeued in the queue

    see ``Queue.clean_tasks`` method for details
    """
    def __init__(self, key, priority=1, timeout=90):
        self.key = key
        self.hashkey = '{key}-timehash'.format(key=key)
        self.priority = priority
        self.timeout = timeout

    def clear(self):
        return conn.delete(self.key)

    def qsize(self):
        return conn.scard(self.key)

    def put(self, *items):
        """ put item(s) into queue """
        if items:
            return conn.sadd(self.key, *items)
        else:
            return 0

    def get(self, block=True, timeout=None):
        """ get item from queue, block if needed """
        if block:
            t = 0  
            while timeout is None or t < timeout:
                result = conn.spop(self.key)
                if not result:
                    t += 0.05
                    time.sleep(0.05)
        else:
            result = conn.spop(self.key)

        if result:
            self.task_start(result)
        return result

    def task_start(self, result):
        """ save start time in redis hash """
        conn.hsetnx(self.hashkey, result, time.mktime(time.gmtime()))

    def task_done(self, result):
        """ clear start time in redis hash, indicating the task done """
        conn.hdel(self.hashkey, result)

    def clean_task(self):
        """ check task hash for unfinished long running tasks, requeue them """
        timeout = self.timeout
        if timeout is None:
            conn.delete(self.hashkey)
            return

        items = []
        for field, value in conn.hgetall(self.hashkey).iteritems():
            start_time = float(value)
            if time.mktime(time.gmtime()) - start_time > timeout:
                items.append(field)

        items, items_tail = items[:50000], items[50000:]
        while items:
            try:
                print('requeuing {} items(e.g. ... {}) to {}'.format(len(items), items[-10:], self.key))
                pipeline = conn.pipeline()
                pipeline.hdel(self.hashkey, *items)
                pipeline.sadd(self.key, *items)
                pipeline.execute()
                items, items_tail = items_tail[:50000], items_tail[50000:]
            except:
                pass

    def background_cleaning(self):
        while True:
            self.clean_task()
            time.sleep(60)
        
def poll(queues, timeout=None):
    """ poll item from queues (order by priority) 
    
    :param queues: instances of queues, can not be empty
    :param timeout: how much time should be used to wait for results, `None` means not limited
    :returns: a tuple of (queue, result), the respective queue and result
    """
    #print('polling {}'.format(queues))
    queues = sorted(queues, key=lambda x:x.priority, reverse=True)
    t = 0
    while timeout is None or t < timeout:
        for q in queues:
            result = q.get(block=False)
            if result is not None:
                return q, result
        t += 0.5
        time.sleep(0.5)

ai1 = Queue('ataobao-item-queue-1', 3, timeout=90)
ai2 = Queue('ataobao-item-queue-2', 1, timeout=90)
as1 = Queue('ataobao-shop-queue-1', timeout=1800)
af1 = Queue('ataobao-fail-queue-1', timeout=1800)
asi1 = Queue('ataobao-shopinfo-queue-1', timeout=90)
aa1 = Queue('ataobao-aggregate-1', timeout=None) # item aggregation
aa2 = Queue('ataobao-aggregate-2', timeout=None) # shop aggregation
