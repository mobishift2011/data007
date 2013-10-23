#!/usr/bin/env python
# -*- coding: utf-8 -*-
from models import db
from caches import LC

from datetime import datetime, timedelta
from bisect import bisect

import redis
from cqlutils import ConnectionPool
import sys
import time


server = redis.Redis('ec2-107-22-142-71.compute-1.amazonaws.com', 6379)

DB_HOSTS = [
                'ec2-54-224-101-163.compute-1.amazonaws.com:9160',
                'ec2-23-20-136-42.compute-1.amazonaws.com:9160',
                'ec2-54-242-132-111.compute-1.amazonaws.com:9160',
                'ec2-72-44-53-84.compute-1.amazonaws.com:9160',
                'ec2-184-73-45-244.compute-1.amazonaws.com:9160',
            ]
        
        
def get_all():
    
    db = ConnectionPool(DB_HOSTS)
    per_num = 10**14
    
    #10090567193265
    
    scan_sum = 0
    begin_time = time.asctime()
    while 1:
        max_tid = server.incr("token_id", per_num)
        print max_tid, scan_sum, begin_time, time.asctime()
        with db.connection() as cur:
            cur.execute('''select id, shopid, cid, num_sold30, price from ataobao2.item where token(id)>=:start and token(id)<:end''', 
                        dict(start=max_tid - per_num, end=max_tid), consistency_level='ONE')
            if cur.rowcount:
                scan_sum += cur.rowcount
                cnt = 0
                for row in cur:
                    cnt += 1
                    itemid, shopid, cid, nc, price = row
                    if cnt%10000 == 0:
                        print "#############", row
    

def main():
    get_all()



if __name__ == '__main__':
    main()