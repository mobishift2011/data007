from caches import LC


print bin(int(LC.gethash('item').hmget('24405056006')[0]))
#print LC.gethash('item').hset('22403775078', 145600000001383869847)