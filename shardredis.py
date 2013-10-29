#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" shard redis queries by (cate1,cate2) """
from hash_ring import HashRing
from redis import Redis

cmd_keys = {'delete', 'keys', 'pexpire', 'renamenx', 'dump', 'migrate', 'pexpireat', 
            'restore', 'exists', 'move', 'pttl', 'sort', 'expire', 'object', 'randomkey', 
            'ttl', 'expireat', 'persist', 'rename', 'type'}
cmd_strings = {'append', 'getbit', 'mget', 'setex', 'bitcount', 'getrange', 'mset', 'setnx',
              'bitop', 'getset', 'msetnx', 'setrange', 'decr', 'incr', 'decrby', 'incrby', 
              'set', 'get', 'incrbyfloat', 'setbit'}
cmd_hashes = {'hdel', 'hincrby', 'hmget', 'hvals', 'hexists', 'hincrbyfloat', 'hmset', 'hget',
              'hkeys',  'hset', 'hgetall', 'hlen', 'hsetnx'}
cmd_lists = {'blpop', 'llen', 'lrem', 'rpush', 'brpop', 'lpop', 'lset', 'rpushx', 'brpoplpush',
             'lpush', 'ltrim', 'lindex', 'lpushx', 'rpop', 'linsert', 'lrange', 'rpoplpush'}
cmd_sets = {'sadd', 'sinter', 'smove', 'sunion', 'scard', 'sinterstore', 'spop', 'sunionstore',
            'sdiff', 'sismember', 'srandmember', 'sdiffstore', 'smembers', 'srem'}
cmd_zsets = {'zadd', 'zinterstore', 'zrem', 'zrevrangebyscore', 'zcard', 'zrange', 'zremrangebyrank',
             'zrevrank', 'zcount', 'zrangebyscore', 'zremrangebyscore', 'zscore', 'zincrby',
             'zrank', 'zrevrange', 'zunionstore'}

cmd_mods = cmd_hashes | cmd_lists | cmd_sets | cmd_zsets | cmd_strings

class ShardRedis(object):
    cache = {}
    def __init__(self, conns, pipelines=None):
        length = len(conns)
        if length not in ShardRedis.cache:
            ShardRedis.cache[length] = HashRing(range(length))
        self.ring = ShardRedis.cache[length]
        self.conns = conns
        self.pipelines = pipelines

    def getconn(self, index):
        if self.pipelines:
            conn = self.pipelines[index]
        else:
            conn = self.conns[index]
        return conn

    def __getattribute__(self, name):
        if name in cmd_mods:
            def func(*args, **kwargs): 
                if 'name' in kwargs:
                    index = self.ring.get_node(kwargs['name'])
                else:
                    index = self.ring.get_node(args[0])

                return getattr(self.getconn(index), name)(*args, **kwargs)
            return func
        elif name == 'pipeline':
            def func(*args, **kwargs):
                return ShardRedis(conns=self.conns, pipelines=[conn.pipeline(*args, **kwargs) for conn in self.conns])
            return func
        elif name == 'execute':
            def func():
                if self.pipelines:
                    result = []
                    for p in self.pipelines:
                        result.extend(p.execute())
                    self.pipelines = None
                    return result
            return func
        elif name in ['flushall']:
            def func(*args, **kwargs):
                results = []
                for index in self.ring.nodes:
                    conn = self.conns[index]
                    results.append(getattr(conn, name)(*args, **kwargs))
                return results
            return func
        elif name == 'info':
            def func(*args, **kwargs):
                result = {}
                for index in self.ring.nodes:
                    d = self.conns[index].info()
                    for key in d:
                        if key not in result:
                            result[key] = []
                        result[key].append(d[key])   
                return result
            return func
        else:
            try:
                attr = object.__getattribute__(self, name)
            except:
                return ValueError("Unsupported operation: {}".format(name))
            else:
                return attr
