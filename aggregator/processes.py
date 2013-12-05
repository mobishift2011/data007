#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys
import time
import redis
import random
import traceback
import threading
from msgpack import packb as pack, unpackb as unpack

from settings import AGGRE_URIS
from shardredis import ShardRedis
from aggregator.indexes import conn

random = random.SystemRandom()

class Process(object):
    """ Distributed task processing manager

    based on redis, a process contains:
    
    - tasks:  list of (caller, args)
    - processing:  list of processing (caller, args)
    - dones:  list of done (caller, args)
    - generated: true/false, ``generate_tasks`` finish or not

    processes have ``generate_tasks`` which will propogate tasks in redis
    the tasks will be consumed by ``Worker``s

    processes may have children, each of them is a process itself,
    processes will call the children once itself is finished.
    """
    processes = 'ataobao-process-processes' # set
    tasks = 'ataobao-process-tasks-{}' # set
    processing = 'ataobao-process-processing-{}' # list
    dones = 'ataobao-process-dones-{}' # list
    generated = 'ataobao-process-generated-{}' # key
    started_at = 'ataobao-process-started_at-{}' # key
    updated_at = 'ataobao-process-updated_at-{}' # key

    def __init__(self, name, max_workers=None):
        self.name = name
        self.children = []
        self.parents = []
        self.lock = threading.Lock()
        self.gened = False
        self.max_workers = max_workers

    def clear_redis(self):
        conn.sadd(self.processes, self.name)
        conn.delete(self.tasks.format(self.name))
        conn.delete(self.processing.format(self.name))
        conn.delete(self.dones.format(self.name))
        conn.delete(self.generated.format(self.name))
        conn.delete(self.updated_at.format(self.name))
        conn.delete(self.started_at.format(self.name))

    def task_left(self):
        return conn.scard(self.tasks.format(self.name)) + conn.llen(self.processing.format(self.name))

    def task_all(self):
        return conn.scard(self.tasks.format(self.name)) +\
                    conn.llen(self.processing.format(self.name)) +\
                    conn.llen(self.dones.format(self.name))

    def progress(self):
        ta = self.task_all()
        tl = self.task_left()
        return 0
        if ta:
            return 1.*tl/ta

    def add_tasks(self, *tasktuples):
        tasks = [ pack((caller, args, kwargs)) for caller, args, kwargs in tasktuples ]
        conn.sadd(self.tasks.format(self.name), *tasks)

    def add_task(self, caller, *args, **kwargs):
        print caller, args[:5], kwargs
        conn.sadd(self.tasks.format(self.name), pack((caller, args, kwargs)))

    def finish_generation(self):
        conn.set(self.generated.format(self.name), 'true')
        conn.set(self.started_at.format(self.name), time.mktime(time.gmtime()))

    def generate_tasks(self):
        """ generate tasks using ``add_task`` and ``finish_generation`` """
        raise NotImplementedError("should implement by subclass")

    def add_child(self, child):
        self.children.append(child)
        child.parents.append(self)

    def check_zombie(self):
        updated_at = conn.get(self.updated_at.format(self.name))
        if updated_at:
            updated_at = float(updated_at)
            if (time.mktime(time.gmtime()) - updated_at) > 600:
                while True:
                    task = conn.lpop(self.processing.format(self.name))
                    if task is None:
                        break
                    conn.rpush(self.dones.format(self.name), task)

    def duration(self):
        updated_at = conn.get(self.updated_at.format(self.name))
        started_at = conn.get(self.started_at.format(self.name))
        if updated_at and started_at:
            seconds = int(float(updated_at)-float(started_at))
            if seconds < 60:
                return '{}s'.format(seconds)
            elif seconds < 3600:
                return '{}m{}s'.format(seconds/60, seconds%60)
            elif seconds < 86400:
                return '{}h{}m'.format(seconds/3600, seconds%3600/60)
            elif seconds > 86400:
                return '{}d{}h'.format(seconds/86400, seconds%86400/3600)
        else:
            return '?'

    def status(self):
        updated_at = conn.get(self.updated_at.format(self.name))
        started_at = conn.get(self.started_at.format(self.name))
        if started_at is None:
            return '?'
        elif updated_at is None:
            return 'W'
        elif self.is_finished():
            return 'F'
        else:
            return 'P'

    def is_finished(self):
        generation_complete = lambda : conn.get(self.generated.format(self.name)) == 'true' 
        processing_complete = lambda : self.task_left() == 0
        finished = generation_complete() and processing_complete()
        if not finished:
            self.check_zombie()
        return finished

    def wait_for_parents(self):
        if self.parents:
            for p in self.parents:
                while not p.is_finished():
                    print('agg {} is waiting agg {} for finish'.format(self.name, p.name))
                    time.sleep(2)

    def start(self):
        self.wait_for_parents()
        print('starting process {}'.format(self.name))

        # locking to make sure we only generate tasks once
        with self.lock:
            if not self.gened:
                self.generate_tasks()
                self.gened = True

        while True:
            time.sleep(2)
            if self.is_finished():
                if self.children:
                    tasks = []

                    for child in self.children:
                        t = threading.Thread(target=child.start)
                        t.setDaemon(True)
                        tasks.append(t)
                        t.start()

                    for t in tasks:
                        t.join()
                 
                break
        print('ended process {}'.format(self.name))

    def work(self):
        time.sleep(random.random())
        while True:
            # check status, sleep longer if not processing, break if finished
            status = self.status()
            # print self.name, status
            if status == 'F':
                break
            elif status in ['?']:
                time.sleep(random.randint(15, 30))
                continue

            try:
                if self.max_workers is not None and \
                    conn.llen(self.processing.format(self.name)) >= self.max_workers:
                    time.sleep(1)
                    continue

                result = conn.spop(self.tasks.format(self.name))
                if result is None:
                    time.sleep(3)
                    continue

                task = result
                conn.rpush(self.processing.format(self.name), task)
                caller, args, kwargs = unpack(task)
                conn.set(self.updated_at.format(self.name), time.mktime(time.gmtime()))

                print('work on {}, {}, {}'.format(caller, args[:5], kwargs))
                if '.' in caller:
                    module, method = caller.rsplit('.', 1)
                    module = __import__(module, fromlist=[method])
                    caller = getattr(module, method)
                else:
                    method = caller
                    caller = sys.modules['__builtin__'].__dict__[method]
            except:
                print("can't obtain caller, locals: {}".format(locals()))
                traceback.print_exc() 
                continue

            try:
                caller(*args, **kwargs)
            except:
                traceback.print_exc()
            finally:
                conn.lrem(self.processing.format(self.name), task, 1)
                conn.rpush(self.dones.format(self.name), task)
                conn.set(self.updated_at.format(self.name), time.mktime(time.gmtime()))


if __name__ == '__main__':
    class PrintProcess(Process):
        def __init__(self):
            super(PrintProcess, self).__init__('PrintProcess')

        def generate_tasks(self):
            for i in range(10):
                self.add_task('print', i)
            self.finish_generation()

    p = PrintProcess()
    t1 = threading.Thread(target=p.start)
    t2 = threading.Thread(target=p.work)
    t2.setDaemon(True)
    t1.start()
    t2.start()
    t1.join()
    #t2.join() 
