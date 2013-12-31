#coding:utf-8


from cqlutils import ConnectionPool
import datetime

def main():
    pool = ConnectionPool(hosts=['ec2-23-22-40-46.compute-1.amazonaws.com:9160'])

    rets = pool.execute('select * from aaa.item', result=True)
    print rets


    for i in xrange(1, 10000):
        pool.execute('insert into aaa.item (id, price, title) values (?, ?, ?)',
                     (i, i*2, str(i*3)))
        print i


#     pool.execute('insert into xxx (key, val) values (:key, :val)',
#                   dict(key='key', val='val'))


#     utcnow = datetime.datetime.utcnow()
#     pool.execute('insert into test.test (id, date, field, value) values (?, ?, ?, ?)',
#                  (1, utcnow, 'testfield', 'testvalue'))
#     r = pool.execute('select * from test.test where id=1 and date=?',
#                      (utcnow,), result=True)
#     assert r.results[0] == (1, utcnow.replace(microsecond=0), 'testfield', 'testvalue')
#
#
#     with pool.connection() as cur:
#         # note cur does not accept dbapi2-favored argument bindings
#         cur.execute('CQL QUERY')
#         cur.execute('INSERT INTO xxx (KEY, COL) VALUES (:key, :val)',
#                     dict(key='key', val='val'))
#         # or you can manually setup bindings for query like this
#         query, bindings = pool.setup_bindings(query, bindings)
#         cur.execute(query, bindings)
#
#
#     pool.batch(['CQL QUERY1', 'CQL QUERY2'])
#     pool.batch([('CQL QUERY1 /W BINDINGS1', bindings1),
#                 ('CQL QUERY2 /W BINDINGS2', bindings2)])



if __name__ == "__main__":
    main()
