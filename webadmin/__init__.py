from flask import Flask

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, wtf
from wtforms import widgets
import redis
import os



app = Flask(__name__)

app.config['SECRET_KEY'] = '123456790'
app.config['MONGODB_SETTINGS'] = {'DB': 'taobao',
                                  "HOST": 'localhost',
                                  "PORT": 27017}

app.__rootdir__ = os.getcwd()



# Create models
db = MongoEngine()
db.init_app(app)
#db.connection.admin.authenticate("root", "chenfuzhi")

app.conn = db.connection
app.redis = redis.Redis("localhost", 6379)

__all__ = ["app", "modes", "api", "views", "cqlui", "blacklist"]

from webadmin import *


