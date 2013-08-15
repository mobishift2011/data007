#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#####################
# install system deps
#####################
if [[ `uname` == 'Darwin' ]]; then
    brew install libxml2 libxslt
    brew install libevent libev
    brew install redis-server
    brew install cassandra
    brew install v8
else
    sudo apt-get -y install build-essential make
    sudo apt-get -y install libxml2-dev libxslt-dev
    sudo apt-get -y install libevent-dev libev-dev
    sudo apt-get -y install libv8-dev libboost-python-dev
    sudo bash "$DIR/install-redis.sh"
    sudo bash "$DIR/install-cassandra.sh"
fi

##################
# make virtualenvs
##################
sudo easy_install -U pip
sudo pip install -U virtualenvwrapper

source /usr/local/bin/virtualenvwrapper.sh

if [ "x$1" == "x" ]; then
  mkvirtualenv ataobao
  workon ataobao
fi

##############
# install pyv8
##############
if [[ `uname` == 'Darwin' ]]; then
    pip install -e git://github.com/brokenseal/PyV8-OS-X#egg=pyv8
else
    bash "$DIR/install-pyv8.sh"
    #pip install -v pyv8
fi 

pip install -r "$DIR/../requirements.txt"
