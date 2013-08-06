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
    
#     form_overrides = dict(desc=wtf.PasswordField)

    list_template = '/admin/model/list.html'
    column_list = ("parentCid", "name", "cid", "sortOrder")
    
    column_default_sort = ('cid', True)
#     form_args = dict(
#         desc=dict(validators=[wtf.required(), ], widget=widgets.TextArea())
#     )

#     form_widget_args = dict(
#         desc={
#             'rows': 10,
#             'cols': 500,
#             'style': 'width:500px;',
#         }
#     )

class MainCategoryView(ModelView):
#     form_overrides = dict(desc=wtf.PasswordField)
    column_list = ("cid", "name", "datatime", "console", "view")
    column_default_sort = ('cid', True)
    list_template = '/cfz/list_category.html'
    

class MyView(BaseView):
    @expose('/')
    def index(self):
        return self.render('home.html')
    
class SeedView(BaseView):
    @expose('/')
    def index(self):
        return self.render('seed.html')
    
    

from flask.ext import admin
admin = admin.Admin(app,  'taobao')
admin.add_view(MainCategoryView(MainCategory,name="parent", endpoint='MainCategory', category='category'))
admin.add_view(CategoryView(Category,name="sub", endpoint='Category', category='category'))
admin.add_view(SeedView())
