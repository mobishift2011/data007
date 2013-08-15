#!/bin/bash
if [[ `uname` == 'Linux' ]]; then
    sudo echo > /etc/apt/sources.list.d/cassandra.list <<EOL
    deb http://www.apache.org/dist/cassandra/debian 10x main
    deb-src http://www.apache.org/dist/cassandra/debian 10x main
    EOL
    gpg --keyserver wwwkeys.pgp.net --recv-keys 4BD736A82B5C1B00
    sudo apt-key add ~/.gnupg/pubring.gpg
    sudo apt-get -y update
    sudo apt-get install cassandra 
fi
