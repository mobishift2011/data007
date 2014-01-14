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
        'RECORD_URI': 'redis://localhost:6379/0',
        'QUEUE_URI': 'redis://localhost:6379/11',
        'CACHE_URIS': [
            'redis://localhost:6379/5',
            'redis://localhost:6379/6',
            'redis://localhost:6379/7',
            'redis://localhost:6379/8',
        ],
        'AGGRE_URIS': [
            [
                'redis://localhost:6379/1',
                'redis://localhost:6379/2',
            ],
            [
                'redis://localhost:6379/3',
                'redis://localhost:6379/4',
            ],        
        ],
        'DB_HOSTS': ['localhost:9160'],
        'DB_HOSTS_BACKUP': ['localhost:9160'],
        'ES_HOSTS': ['localhost:9500'],
    },
    'TEST': {
        'RECORD_URI': 'redis://ec2-54-199-147-18.ap-northeast-1.compute.amazonaws.com:6379/0',
        'QUEUE_URI': 'redis://ec2-54-199-147-18.ap-northeast-1.compute.amazonaws.com:6379/11',
        'CACHE_URIS': [
            'redis://ec2-54-199-147-18.ap-northeast-1.compute.amazonaws.com:6401/12',
            'redis://ec2-54-199-147-18.ap-northeast-1.compute.amazonaws.com:6402/12',
            'redis://ec2-54-199-147-18.ap-northeast-1.compute.amazonaws.com:6403/12',
            'redis://ec2-54-199-147-18.ap-northeast-1.compute.amazonaws.com:6404/12',
        ],
        'AGGRE_URIS': [
            [
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6401/13',
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6402/13',
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6403/13',
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6404/13',
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6405/13',
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6406/13',
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6407/13',
                'redis://ec2-54-199-139-229.ap-northeast-1.compute.amazonaws.com:6408/13',
            ],
            [
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6401/13',
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6402/13',
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6403/13',
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6404/13',
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6405/13',
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6406/13',
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6407/13',
                'redis://ec2-54-199-155-127.ap-northeast-1.compute.amazonaws.com:6408/13',
            ],
        ],
        'DB_HOSTS': [
            'ec2-54-199-146-132.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-143-122.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-146-135.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-143-197.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-142-208.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-146-126.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-139-91.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-142-200.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-141-93.ap-northeast-1.compute.amazonaws.com:9160',
            'ec2-54-199-136-165.ap-northeast-1.compute.amazonaws.com:9160',
        ],
        'DB_HOSTS_BACKUP': [
            'ec2-54-193-57-19.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-57-11.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-57-57.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-56-229.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-57-10.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-57-39.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-56-223.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-57-17.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-56-215.us-west-1.compute.amazonaws.com:9160',
            'ec2-54-193-57-40.us-west-1.compute.amazonaws.com:9160',
        ],
        'ES_HOSTS': ['ec2-54-199-164-67.ap-northeast-1.compute.amazonaws.com:9500'],
        'ADMIN_HOST': '54.199.145.250',
    },
}

for key, value in envs.get(ENV, envs['DEV']).iteritems():
    globals()[key] = value
