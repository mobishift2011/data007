#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import redis
from settings import AGGRE_URIS
from shardredis import ShardRedis
from datetime import datetime, timedelta

from aggregator.models import getdb

def _getconn(date):
    conns = []
    db = getdb()
    r = db.execute('''select datestr, hosts, ready from ataobao2.agghosts
                      where datestr=:date''', dict(date=date), result=True)
    if not r.results:
        dt = datetime.strptime(date, '%Y-%m-%d')
        dates = [(dt-timedelta(days=days)).strftime('%Y-%m-%d') for days in range(14)]
        dates = ','.join(["'"+d+"'" for d in dates])
        r = db.execute('''select datestr, hosts, ready from ataobao2.agghosts where datestr in (:dates)''', 
                       dict(dates=dates), result=True)
        alluris = [ [ds, hosts, ready] for ds, hosts, ready in sorted(r.results) if ready ]
        if not alluris:
            uris = AGGRE_URIS[0]
        else:
            used_uris = json.loads(alluris[-1][1])
            for au in AGGRE_URIS:
                if set(au) != set(used_uris):
                    uris = au
                    break
            else:
                uris = used_uris

        db.execute('''insert into ataobao2.agghosts (datestr, hosts)
                      values (:date, :hosts)''',  dict(date=date, hosts=json.dumps(uris)))
    else:
        uris = json.loads(r.results[0][1])

    for uri in uris:
        host, port, dbn = re.compile('redis://(.*):(\d+)/(\d+)').search(uri).groups()
        conn = redis.Redis(host=host, port=int(port), db=int(dbn))
        conns.append(conn)

    return ShardRedis(conns=conns)

def getconn(date):
    if not hasattr(getconn, 'conn'):
        getconn.cdict = {}
    cdict = getconn.cdict

    if date not in cdict:
        cdict[date] = _getconn(date)

    return cdict[date]

if __name__ == '__main__':
    print getconn('2014-01-20')
