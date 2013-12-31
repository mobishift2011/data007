#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import json
import redis
from models import db
from settings import AGGRE_URIS
from shardredis import ShardRedis

def _getconn(date):
    conns = []
    r = db.execute('''select datestr, hosts from ataobao2.agghosts
                      where datestr=:date''', dict(date=date), result=True)
    if not r.results:
        r = db.execute('''select datestr, hosts from ataobao2.agghosts''', result=True)
        if not r.results:
            uris = AGGRE_URIS[0]
        else:
            used_uris = json.loads(sorted(r.results)[-1][1])
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
    print getconn('2014-01-01')
