import re
import redis
import traceback

from caches import conn

pipes = {}

for c in conn.conns:
    print 'cleaning on {}'.format(c)
    keys = c.keys()
    count = 0
    for key in keys:
        count += 1
        if 'count' in key or 'bucket' in key:
            continue
        n = conn.get_redis(key)
        for r in conn.conns:
            if r != n:
                if r not in pipes:
                    pipes[r] = r.pipeline()
                pipes[r].delete(key)
        if count % 10000 == 0:
            for key, pipe in pipes.items():
                pipe.execute()
        print count

    for key, pipe in pipes.items():
        pipe.execute()
    print count
