#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" All workers defined here

A worker typically "watches" a queue, and do jobs accordingly
"""
from gevent import monkey; monkey.patch_all()

import time
import traceback
import gevent.pool
import gevent

from aggregator import iap, sap, bap, cap, shp
from aggregator.indexes import *
from models import db


class Worker(object):
    """ General Worker """
    def __init__(self, poolsize=5):
        self.pool = gevent.pool.Pool(poolsize)

    def work(self):
        raise NotImplementedError('this method should be implemented by subclasses')

class AggregateWorker(Worker):
    """ worker for general aggregation """
    def __init__(self, poolsize=5):
        self.poolsize = poolsize
        self.processes = [iap, sap, bap, cap, shp]

    def work(self):
        def workon(iap):
            pool = gevent.pool.Pool(self.poolsize)
            
            for i in range(self.poolsize):
                pool.spawn(iap.work)

            pool.join()

        gevent.joinall([gevent.spawn(workon, p) for p in self.processes])
            

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Call Worker with arguments')
    parser.add_argument('--worker', '-w', choices=['aggregate'], help='worker type, can be "aggregate"', required=True)
    parser.add_argument('--poolsize', '-p', type=int, default=5, help='gevent pool size for worker (default: %(default)s)')
    option = parser.parse_args()
    if option.worker == "aggregate":
        AggregateWorker(option.poolsize).work()
    

if __name__ == '__main__':
    main()
