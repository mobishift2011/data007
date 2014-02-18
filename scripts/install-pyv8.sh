#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ `uname` == 'Linux' ]]; then
    mkdir -p pyv8
    cd pyv8
    rm -rf *
    wget https://github.com/observerss/pyv8-binaries/raw/master/pyv8-amd64-py27.tar.gz
    tar xzvf pyv8-amd64-py27.tar.gz
    rm *.tar.gz
    cd ..
    cp -r pyv8 "$DIR/../"
elif [ `uname` == 'Darwin' ]; then
    mkdir -p pyv8
    cd pyv8
    rm -rf *
    wget https://github.com/emmetio/pyv8-binaries/raw/master/pyv8-osx.zip
    unzip pyv8-osx.zip
    touch __init__.py
    rm *.zip
    cd ..
    cp -r pyv8 "$DIR/../"
fi
