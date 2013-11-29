#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from aggregator.indexes import BrandIndex
from aggregator.processes import Process
from aggregator.esindex import index_brand
from settings import ENV

from datetime import datetime, timedelta

import json
import traceback

defaultdate = (datetime.utcnow()+timedelta(hours=-16)).strftime("%Y-%m-%d")

def es_brands(brands, date=None):
    try:
        if date is None:
            date = defaultdate
        bi = BrandIndex(date)
        for brand in brands:
            try:
                es_brand(bi, date, brand)
            except:
                traceback.print_exc()
    except:
        traceback.print_exc()

def es_brand(bi, date, brand):
    pass

class BrandESProcess(Process):
    def __init__(self, date=None):
        super(BrandESProcess, self).__init__('brandes')
        if ENV == 'DEV':
            self.step = 100
        else:
            self.step = 1000
        self.date = date

    def generate_tasks(self):
        self.clear_redis()
        brands = []
        for i in range(len(brands)/self.step):
            self.add_task('aggregator.brandes.es_brands', brands[self.step*i:self.step*(i+1)], date=self.date)
        self.finish_generation()

bep = BrandESProcess()

if __name__ == '__main__':
    bep.date = '2013-11-28'
    bep.start()
