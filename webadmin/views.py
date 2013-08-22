#coding:utf-8

import datetime

from flask import Flask, request, redirect

from flask.ext import admin
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext import admin, wtf
from wtforms import widgets
from webadmin.modes import *
from flask.ext.admin import Admin, BaseView, expose
from webadmin import app
from bson.objectid import ObjectId


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

        
        
def formatter(view, context, model, name):
    # `view` is current administrative view
    # `context` is instance of jinja2.runtime.Context
    # `model` is model instance
    # `name` is property name
    print view, context, model, name


class SpiderView(ModelView):
    column_list = ("name", "get_seed", "navi_list", "spider_process", "spider_threads")

    list_template = 'cfz/spider_list.html'
    edit_template = 'cfz/spider_edit.html'
    create_template = 'cfz/spider_create.html'

    def on_model_delete(self, model):
        for navi in model.navi_list:
            app.conn.taobao.spider_navi.remove({"_id":navi.id})
            
            
class SpiderNaviView(ModelView):
#     form_overrides = dict(desc=wtf.PasswordField)
    column_list = ("name",)
    edit_template = 'cfz/code_edit.html'
    create_template = 'cfz/code_create.html'

    def after_model_change(self, form, model, is_created):
        if is_created is True:
            spider_id = request.args.get("spider_id")
            app.conn.taobao.spider.update({"_id":ObjectId(spider_id)}, {"$push":{"navi_list":ObjectId(model.id)}})
            
    
class SchdSeedView(ModelView):
#     form_overrides = dict(desc=wtf.PasswordField)
    column_list = ("name", "redis_key", "seed_list", "schd_seed")
    list_template = 'cfz/seed_list.html'

            
             
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
        return self.render('cfz/spider_monitor.html', **{"rows":rows})


from flask.ext import admin
admin = admin.Admin(app,  'taobao')
admin.add_view(SpiderAdminView())

admin.add_view(MainCategoryView(MainCategory,name="parent", endpoint='MainCategory', category='category'))
admin.add_view(CategoryView(Category,name="sub", endpoint='Category', category='category'))
 
admin.add_view(SchdSeedView(SchdSeed, name="SchdSeed", endpoint='SchdSeed', category='crawl'))
admin.add_view(SpiderView(Spider, name="spider", endpoint='Spider', category='crawl'))
admin.add_view(SpiderNaviView(SpiderNavi, name="spider_navi", endpoint='SpiderNavi', category='crawl'))

admin.add_view(TaobaoUserView(TaobaoUser))

#admin.add_view(SpidersView())

