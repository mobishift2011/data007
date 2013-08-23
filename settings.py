#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

ROOT_PATH = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(ROOT_PATH, "tests")

ENV = os.environ.get('ENV', 'DEV')
if ENV == '':
    ENV = 'DEV'

envs = {
    'DEV': {
        'QUEUE_URI': 'redis://localhost:6379/11',
        'CACHE_URI': 'redis://localhost:6379/12',
        'DB_HOSTS': ['localhost:9160'],
    },
    'TEST': {
        'QUEUE_URI': 'redis://ec2-107-21-68-149.compute-1.amazonaws.com:6379/11',
        'CACHE_URI': 'redis://ec2-107-21-68-149.compute-1.amazonaws.com:6379/12',
        'DB_HOSTS': [
            'ec2-54-226-12-188.compute-1.amazonaws.com:9160',
            'ec2-23-22-143-204.compute-1.amazonaws.com:9160',
            'ec2-23-22-40-46.compute-1.amazonaws.com:9160',
        ],
    },
}

for key, value in envs.get(ENV, envs['DEV']).iteritems():
    globals()[key] = value
