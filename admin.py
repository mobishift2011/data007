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
from webadmin.modes import *
from webadmin.views import *





# Flask views
@app.route('/')
def index():
    return '<a href="/admin/">Click me to get to Admin!</a> \
        <br><a href="/cqlui/">Click me to get to CQL UI Tool!</a>'


if __name__ == '__main__':
    # Create admin
    # Start app
    import os
    import sys
    
    try:
        if sys.argv[1] == 'debug':
            app.debug = True
    except:
        pass
    app.run('0.0.0.0', 9992)

