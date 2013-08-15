#!/bin/bash
####
# Set up SO:
####
apt-get -y update && apt-get -y upgrade

####
# Download and install Redis:
####
mkdir build
cd build
wget -q http://redis.googlecode.com/files/redis-2.6.14.tar.gz
tar xzf redis-2.6.14.tar.gz
rm -f redis-2.6.14.tar.gz
cd redis-2.6.14
make
make install

####
# Set up Redis
####
rm -rf /etc/redis /var/lib/redis
mkdir /etc/redis /var/lib/redis
cp src/redis-server src/redis-cli /usr/local/bin
cp redis.conf /etc/redis
#sed -e "s/^daemonize no$/daemonize yes/" -e "s/^# bind 127.0.0.1$/bind 127.0.0.1/" -e "s/^dir \.\//dir \/var\/lib\/redis\//" -e "s/^loglevel verbose$/loglevel notice/" -e "s/^logfile stdout$/logfile \/var\/log\/redis.log/" redis.conf > /etc/redis/redis.conf

####
# Redis correctly installed.
# Download script for running Redis
####
wget -q https://gist.github.com/observerss/6238444/raw/d48b84d89289df39eaddc53f1e9a918f776b3074/redis-server
mv redis-server /etc/init.d
chmod 755 /etc/init.d/redis-server

####
# To start Redis just uncomment this line
####
service redis-server start
