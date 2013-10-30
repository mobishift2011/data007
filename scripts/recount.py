from caches import LC, IF, WC

def recount_thinset(ts):
    print 'counting', ts.name
    count = 0
    total = ts.modulo
    batch = 10000
    for i in range(total/batch):
        p = ts.conn.pipeline()
        for j in range(batch):
            if i*batch+j >= total:
                break
            bucket = 'thinset_{}_{}'.format(ts.name, i*batch+j)
            p.scard(bucket)
        count += sum(p.execute())
        print 'current count', count
    ts.conn.set(ts.counterkey, count) 

def recount_thinhash(th):
    print 'counting', th.name
    count = 0
    total = th.modulo
    batch = 10000
    for i in range(total/batch):
        p = th.conn.pipeline()
        for j in range(batch):
            if i*batch+j >= total:
                break
            bucket = 'thinhash_{}_{}'.format(th.name, i*batch+j)
            p.hlen(bucket)
        count += sum(p.execute())
        print 'current count', count
    th.conn.set(th.counterkey, count)

if __name__ == '__main__':
    #recount_thinset(WC)
    #recount_thinset(IF)
    #recount_thinhash(LC.gethash('shop'))
    recount_thinhash(LC.gethash('item'))
