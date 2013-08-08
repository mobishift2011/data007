#!/bin/bash
if [[ `uname` == 'Darwin' ]]; then
    brew install libxml2 libxslt
    brew install libevent libev
    brew install v8
else
    sudo apt-get -y install libxml2-dev libxslt-dev
    sudo apt-get -y install libevent-dev libev-dev
    sudo apt-get -y install libv8-dev
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sudo easy_install -U pip
sudo pip install -U virtualenvwrapper

source /usr/local/bin/virtualenvwrapper.sh

if [ "x$1" == "x" ]; then
  mkvirtualenv ataobao
  workon ataobao
fi

if [[ `uname` == 'Darwin' ]]; then
    pip install -e git://github.com/brokenseal/PyV8-OS-X#egg=pyv8
else
    pip install -v pyv8
fi 

pip install -r "$DIR/../requirements.txt"
#legit install
