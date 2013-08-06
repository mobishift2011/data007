#!/bin/bash
if [[ `uname` == 'Darwin' ]]; then
    brew install libxml2 libxslt
    brew install libevent libev
else
    sudo apt-get -y install libxml2-dev libxslt-dev
    sudo apt-get -y install libevent-dev libev-dev
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
sudo easy_install -U pip
sudo pip install -U virtualenvwrapper

source /usr/local/bin/virtualenvwrapper.sh

if [ "x$1" == "x" ]; then
  mkvirtualenv ataobao
  workon ataobao
fi

pip install -r "$DIR/../requirements.txt"
legit install
