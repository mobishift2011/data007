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
            'ec2-107-21-167-122.compute-1.amazonaws.com:9160',
            'ec2-50-16-109-195.compute-1.amazonaws.com:9160',
            'ec2-75-101-172-166.compute-1.amazonaws.com:9160',
            'ec2-54-211-56-82.compute-1.amazonaws.com:9160',
            'ec2-50-16-97-89.compute-1.amazonaws.com:9160',
        ],
    },
}

for key, value in envs.get(ENV, envs['DEV']).iteritems():
    globals()[key] = value
