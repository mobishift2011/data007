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


# Flask views
@app.route('/api/query_domain', methods=['GET', 'POST'])
def query_domain():
    js = request.get_json(force=True, cache=False)
    
#------------------------------------------------------------------------------ 
    conn = pymongo.Connection("localhost", 37017)
    conn.admin.authenticate("root", "chenfuzhi")
    
    row = conn.coupons.site.find_one({"host":js["domain"]})
    if row is not None:
        
#------------------------------------------------------------------------------ 
        ret = {}
        try:
            ret["url_matchs"] = eval(row["url_matchs"])
            ret["cart_extr"] = eval(row["cart_extr"])
            ret["apply_coupon"] = eval(row["apply_coupon"])
            ret["price_extr"] = eval(row["price_extr"])
        except Exception, e:
            return '{"success":0, "err":"%s"}' % e
        ret = {
               "success": 1,
               "data": ret
               }
        return json.dumps(ret, default=default)
#------------------------------------------------------------------------------ 
        
    return '{"success":0}'


@app.route('/api/monitor_price', methods=['GET', 'POST'])
def monitor_price():
    js = request.get_json(force=True, cache=False)
#------------------------------------------------------------------------------ 
    conn = pymongo.Connection("localhost", 37017)
    conn.admin.authenticate("root", "chenfuzhi")
    
    js["timestamp"] = time.strftime("%Y-%M-%d %H:%I:%S")
    ret = conn.coupons.price_monitor.save(js)
    
    return '{"success":1, "id": "%s"}' % str(ret)
#------------------------------------------------------------------------------ 




# Flask views
@app.route('/api/post_cart', methods=['GET', 'POST'])
def post_cart():
    conn = pymongo.Connection("localhost", 37017)
    conn.admin.authenticate("root", "chenfuzhi")
    js = request.get_json(force=True, cache=False)
    
    print  js
    
    if len(js["cart"]) > 0:
        sum = 0
        for good in js["cart"]:
            cnt = int(good["count"])
            price = float(good["price"])
            sum += cnt * price
            print cnt, price, "*****************************"
        
        site = conn.coupons.site.find_one({"host":js["domain"]})
        
        _find = {"money":{"$lte": int(sum)}, "site":site["_id"]}
        rows = conn.coupons.coupons.find(_find)
        rows = list(rows)
        
        print "conn.coupons.coupons.find", _find, rows
        
        rets = []
        if len(rows) > 0:
            for row in rows:
                rets.append({
                             "code":row["code"],
                             "desc":row["desc"],
                             })
            data = {
                    "success":1,
                    "data":rets
                    }
            return json.dumps(data)
        else:
            return '{"success":0, "msg":"not find match coupons."}'
            
    return '{"success":0}'



print "medule api s loaded."
