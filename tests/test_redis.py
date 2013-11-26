from shardredis import ShardRedis
from thinredis import ThinHash, ThinSet, CappedSortedSet
from redis import Redis

def _test_thinhash(conn):
    conn.delete('test')
    h = ThinHash('test', 10000, connection=conn)
    l = range(10)
    l.extend(range(10))
    h.hmset(*l)
    assert list(h.hmget(*range(10))) == ['1', None, '3', None, '5', None, '7', None, '9', None]

def _test_thinset(conn):
    conn = Redis(db=1)
    conn.delete('test')
    s = ThinSet('test', 10000, connection=conn)
    l = range(10) 
    s.add(*l)
    assert s.contains(*range(0, 20, 2)) == [True, True, True, True, True, False, False, False, False, False]


def test_thinhash_normal():
    conn = Redis(db=1)
    _test_thinhash(conn)

def test_thinhash_shard():
    conn = ShardRedis(conns=[Redis(db=1), Redis(db=2), Redis(db=3), Redis(db=4)])
    _test_thinhash(conn)

def test_thinset_normal():
    conn = Redis(db=1)
    _test_thinset(conn)

def test_thinset_shard():
    conn = ShardRedis(conns=[Redis(db=1), Redis(db=2), Redis(db=3), Redis(db=4)])
    _test_thinset(conn)

def test_cappedsortedset_shard():
    conn = ShardRedis(conns=[Redis(db=1), Redis(db=2), Redis(db=3), Redis(db=4)])
    conn.flushall() 
    cs = CappedSortedSet('test', 5, conn=conn, skey='test')
    for member, score in [(1, 1), (3, 3), (5, 5), (7, 7), (9, 9), (2, 2), (4, 4), (6, 6)]:
        cs.zadd(member, score)
    assert cs.zrange(0, -1) == ['4', '5', '6', '7', '9']

def test_cappedsortedset_normal():
    conn = Redis(db=1)
    conn.flushall() 
    cs = CappedSortedSet('test', 5, conn=conn)
    for member, score in [(1, 1), (3, 3), (5, 5), (7, 7), (9, 9), (2, 2), (4, 4), (6, 6)]:
        cs.zadd(member, score)
    assert cs.zrange(0, -1) == ['4', '5', '6', '7', '9']
