#coding:utf-8
import datetime
from flask import Flask

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, wtf
from wtforms import widgets
# Create application
from webadmin import app
from flask import request
from urlparse import urlparse
import pymongo
from bson.json_util import default
import json
import re
import time
import psutil
import subprocess
from multiprocessing import Process
from twisted.python import log

FPID = "/tmp/server_admin.pid"
FLOG = "/var/log/server_admin.log"

RUN_PATH = "/home/cfz/ataobao/daemon"
# Flask views
@app.route('/server_admin/')
def server_admin():
    act = request.args.get('act', '')
    if act == "status":
        try:
            pid = open(FPID, 'r').read()
            p = psutil.Process(int(pid))
            return '{"success":1, "msg":"%s"}' % p.name
        except Exception, e:
            return '{"success":0, "msg":"%s"}' % e
        
    elif act == "start":
        
        args = ["twistd",
                 "-y",
                 "%s/server.py" % RUN_PATH,
                 "--pidfile=%s" % FPID,
                 "--logfile=%s" % FLOG,
                 "--rundir=%s/" % RUN_PATH,
                 ]
        print args
        
        try:
            out = subprocess.call(args)
            if out == 0:
                return '{"success":1, "msg":"ok"}'
            elif out == 1:
                return '{"success":1, "msg":"is seen already running."}'
            
        except Exception, e:
            log.err()
            return '{"success":0, "msg":"%s"}' % e
        
        
    elif act == "stop":
        try:
            pid = open(FPID, 'r').read()
            p = psutil.Process(int(pid))
            p.terminate()
            return '{"success":1, "msg":"%s"}' % p.name
        except Exception, e:
            return '{"success":0, "msg":"%s"}' % e




@app.route('/test_python_code/')
def test_python_code():
    act = request.args.get('act', '')
    



print "medule api s loaded."
