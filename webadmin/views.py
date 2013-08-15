#coding:utf-8

import datetime

from flask import Flask

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, wtf
from wtforms import widgets
from webadmin.modes import *
from flask.ext.admin import Admin, BaseView, expose
from webadmin import app

class CategoryView(ModelView):
    
    column_filters = ['parentCid', ]
    column_searchable_list = ('parentCid',)
    
    list_template = '/admin/model/list.html'
    column_list = ("parentCid", "name", "cid", "sortOrder")
    
    column_default_sort = ('cid', True)
#     form_args = dict(
#         desc=dict(validators=[wtf.required(), ], widget=widgets.TextArea())
#     )


class MainCategoryView(ModelView):
#     form_overrides = dict(desc=wtf.PasswordField)
    column_list = ("cid", "name", "datatime", "console", "view")
    column_default_sort = ('cid', True)
    list_template = '/cfz/list_category.html'

class RedisQueueView(ModelView):
#     form_overrides = dict(desc=wtf.PasswordField)
    column_list = ("spider", "name", "rule", "prio")
    column_searchable_list = ('rule',)
        
        
class SpiderView(ModelView):
    column_list = ("name", "spider_process", "spider_workers")

#     list_template = 'cfz/list_category.html'
#     edit_template = 'cfz/edit.html'
#     form_widget_args = dict(
#         code={
#             'rows': 10,
#             'cols': 500,
#             'style': 'width:500px;',
#         }
#     )

class TaobaoUserView(ModelView):
    column_list = ("name", "pwd", "enable", "latest")


class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('home.html')
    
class SpiderAdminView(BaseView):
    @expose('/')
    def index(self):
        rows = app.conn.taobao.spider.find({})
        rows = list(rows)
        return self.render('cfz/spiders.html', **{"rows":rows})

from flask.ext import admin
admin = admin.Admin(app,  'taobao')
admin.add_view(SpiderAdminView())

admin.add_view(MainCategoryView(MainCategory,name="parent", endpoint='MainCategory', category='category'))
admin.add_view(CategoryView(Category,name="sub", endpoint='Category', category='category'))
 
admin.add_view(RedisQueueView(RedisQueue,name="queue", endpoint='RedisQueue', category='crawl'))
admin.add_view(SpiderView(Spider, name="spider", endpoint='Spider', category='crawl'))

admin.add_view(TaobaoUserView(TaobaoUser))

print "ddddddddd"
#admin.add_view(SpidersView())


