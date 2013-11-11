#!/bin/bash
add-apt-repository -y ppa:chris-lea/redis-server
apt-get -y update && apt-get -y install redis-server

/etc/init.d/redis-server stop
update-rc.d redis-server disable
rm /etc/init.d/redis-server

cat > /etc/init/redis-server.conf <<END
description "redis server"

start on runlevel [2345]
stop on runlevel [!2345]

limit nofile 50000 50000

respawn

exec sudo -u redis /usr/bin/redis-server /etc/redis/redis.conf

END

cat > /etc/redis/redis.conf <<END
daemonize no
pidfile /var/run/redis/redis-server.pid
port 6379
timeout 0
loglevel notice
logfile /var/log/redis/redis-server.log
databases 16
save 900 1
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis
slave-serve-stale-data yes
slave-read-only yes
slave-priority 100
appendonly no
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb
lua-time-limit 5000
slowlog-log-slower-than 10000
slowlog-max-len 128
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-entries 512
list-max-ziplist-value 64
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
activerehashing yes
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit slave 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60
END

echo "vm.overcommit_memory = 1" >> /etc/sysctl.conf
sysctl vm.overcommit_memory=1

start redis-server

