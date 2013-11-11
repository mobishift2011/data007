#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import sys
import time
import redis
import traceback
import threading
from msgpack import packb as pack, unpackb as unpack


from settings import AGGRE_URIS
from shardredis import ShardRedis
from aggregator.indexes import conn

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
    processes = 'ataobao-process-processes'
    tasks = 'ataobao-process-tasks-{}'
    processing = 'ataobao-process-processing-{}'
    dones = 'ataobao-process-dones-{}'
    generated = 'ataobao-process-generated-{}'

    def __init__(self, name):
        self.name = name
        self.children = []

    def clear_redis(self):
        conn.sadd(self.processes, self.name)
        conn.delete(self.tasks.format(self.name))
        conn.delete(self.processing.format(self.name))
        conn.delete(self.dones.format(self.name))
        conn.delete(self.generated.format(self.name))

    def task_left(self):
        return conn.llen(self.tasks.format(self.name))

    def add_task(self, caller, *args, **kwargs):
        print caller, args[:5], kwargs
        conn.rpush(self.tasks.format(self.name), pack((caller, args, kwargs))) 

    def finish_generation(self):
        conn.set(self.generated.format(self.name), 'true')

    def generate_tasks(self):
        """ generate tasks using ``add_task`` and ``finish_generation`` """
        raise NotImplementedError("should implement by subclass")

    def add_child(self, child):
        self.children.append(child)

    def is_finished(self):
        generation_complete = lambda : conn.get(self.generated.format(self.name)) == 'true' 
        processing_complete = lambda : conn.llen(self.tasks.format(self.name)) + conn.llen(self.processing.format(self.name)) == 0
        return generation_complete() and processing_complete()

    def start(self):
        print('starting process {}'.format(self.name))
        self.generate_tasks()

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
        while True:
            try:
                result = conn.blpop(self.tasks.format(self.name), 10)
                if result is None:
                    continue
                _, task = result
                conn.rpush(self.processing.format(self.name), task)
                caller, args, kwargs = unpack(task)
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
