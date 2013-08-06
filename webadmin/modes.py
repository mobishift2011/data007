#coding:utf-8
import datetime

from flask import Flask

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, wtf
from wtforms import widgets
from webadmin import db

    
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
    

class Spider(db.Document):
    '''
    '''
    name = db.StringField(max_length=500)
    navi_list = db.StringField(max_length=500)
    
    datatime = db.DateTimeField()
    
    def __unicode__(self):
        return self.name


class RedisQueue(db.Document):
    '''
    '''
    name = db.StringField(max_length=500)
    def __unicode__(self):
        return self.name
    
    
    