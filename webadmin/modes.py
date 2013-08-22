#coding:utf-8
import datetime

from flask import Flask

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, wtf
from wtforms import widgets
from webadmin import db
import time
import datetime
    
class EmProp(db.EmbeddedDocument):
    
    name = db.StringField()
    required = db.BooleanField()
    childTemplate = db.StringField()
    parentPid = db.IntField()
    isKeyProp = db.BooleanField()
    pid = db.IntField()
    cid = db.IntField()
    parentVid = db.IntField()
    isColorProp = db.BooleanField()
    isSaleProp = db.BooleanField()
    categoryPropValueList = db.StringField()
    sortOrder = db.IntField()
    type = db.StringField()
    isAllowAlias = db.BooleanField()
    

class Category(db.Document):
    '''
    '''
    name = db.StringField(max_length=500)
    cid = db.StringField(max_length=500)
    parentCid = db.StringField(max_length=500)
    isParent = db.StringField(max_length=500)
    sortOrder = db.StringField(max_length=500)
    categoryPropList = db.StringField(max_length=500)
    featureList = db.StringField(max_length=500)
    childCategoryList = db.ListField(db.EmbeddedDocumentField(EmProp))
    
    def __unicode__(self):
        return self.name
    

class MainCategory(db.Document):
    '''
    '''
    
    cid = db.StringField(max_length=500)
    name = db.StringField(max_length=500)
    datatime = db.DateTimeField()
    
    def __unicode__(self):
        return self.name

class Navi(db.EmbeddedDocument):
    url_rule = db.StringField(max_length=500)
    code = db.StringField()
    
    
class Spider(db.Document):
    '''
    '''
    name = db.StringField(max_length=500)
    spider_process = db.IntField(min_value=1, max_value=100, default=1)
    spider_workers = db.IntField(min_value=1, max_value=10000, default=100)
    navi_list = db.ListField(db.EmbeddedDocumentField(Navi))
    def __unicode__(self):
        return self.name
    
    
    
class SpiderNavi(db.Document):
    name = db.StringField(max_length=500, required=True)
    python_code = db.StringField(default=open("webadmin/code_tpl.py").read())
    def __unicode__(self):
        return self.name
    
    
class Spider(db.Document):
    '''
    '''
    name = db.StringField(max_length=500, required=True)
    get_seed = db.StringField(required=True, default=open("webadmin/code_tpl_seed.py").read())
    spider_process = db.IntField(default=1)
    spider_threads = db.IntField(default=100)
    navi_list = db.ListField(db.ReferenceField(SpiderNavi))
    def __unicode__(self):
        return self.name

class SchdSeed(db.Document):
    '''
    '''
    name = db.StringField(max_length=500, required=True)
    redis_key = db.StringField(max_length=500, required=True)
    schd_datetime = db.DateTimeField()
    schd_times = db.IntField(default=0)
    seed_list = db.ListField(db.StringField(max_length=500))
    def __unicode__(self):
        return self.name


class TaobaoUser(db.Document):
    '''
    '''
    name = db.StringField(max_length=500)
    pwd = db.StringField(max_length=500)
    email = db.StringField(max_length=500)
    cookie = db.StringField()
    enable = db.BooleanField(default=True)
    latest = db.DateTimeField(default=datetime.datetime.utcnow())

    def __unicode__(self):
        return self.name
    
#------------------------------------------------------------------------------ ec2

class EC2_Schd(db.Document):
    '''
    '''
    name = db.StringField(max_length=500)
    spider_name = db.ReferenceField(Spider)
    ec2_region = db.StringField(max_length=500, choices=[(),
                                                         (),
                                                         (),
                                                         (),
                                                         ])
    instance_num = db.StringField(max_length=500)
    cookie = db.StringField()
    enable = db.BooleanField(default=True)
    latest = db.DateTimeField(default=datetime.datetime.utcnow())

    def __unicode__(self):
        return self.name