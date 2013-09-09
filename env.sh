#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH=$DIR:$PYTHONPATH
export ENV=$1
source /usr/local/bin/virtualenvwrapper.sh
workon ataobao
