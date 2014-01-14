#!/usr/bin/env python
from cqlutils import ConnectionPool
from settings import DB_HOSTS, DB_HOSTS_BACKUP

db1 = ConnectionPool(DB_HOSTS)
db2 = ConnectionPool(DB_HOSTS_BACKUP)

def getdb(dbname=None):
    """ db2 get 2/3 load, db1 get 1/3 load """
    if dbname is None:
        import random        
        reload(random)
        dbname = random.choice(['db1', 'db2', 'db2'])
        
    return {'db1':db1,'db2':db2}.get(dbname, db2)
