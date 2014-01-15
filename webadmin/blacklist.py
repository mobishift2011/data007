#!/usr/bin/env python
# -*- encoding: utf-8 -*-

try:
    from models import db
except Exception, e:
    print "#########", e

from webadmin import app
from flask import request, render_template, redirect
from crawler.tbitem import get_item

import time
import traceback

KEYSPACE = 'ataobao2'
blacklist = None
whitelist = None
last_update = None

def get_lists():
    global last_update, blacklist, whitelist
    if last_update is None or last_update < time.time() - 86400:
        r = db.execute('select type, args, value from ataobao2.blacklist', result=True)
        last_update = time.time()
        blacklist = list(reversed([ row[1:] for row in r.results if row[0] == 'shopblack' ]))
        whitelist = list(reversed([ row[1:] for row in r.results if row[0] == 'shopwhite' ]))
    return blacklist, whitelist

get_lists()

@app.route('/blacklist/')
def blacklist_index():
    blacklist, whitelist = get_lists()
    return render_template('blacklist/index.html', blacklist=blacklist, whitelist=whitelist)

@app.route('/blacklist/add')
def blacklist_add():
    global blacklist, whitelist
    if whitelist is None:
        whitelist = []
    if blacklist is None:
        blacklist = []
    type = request.args.get('type') 
    if type == 'blacklist':
        for itemid in request.args.get('itemid', '0').split(','):
            try:
                itemid = int(itemid)
            except:
                itemid = 0
            if itemid == 0:
                # illegal input
                pass    
            elif itemid not in [v[1] for v in blacklist]:
                # should get shopid and save to blacklist
                i = get_item(itemid)
                if not i or 'error' in i:
                    pass
                else:
                    if i['shopid'] != 0:
                        shopid = i['shopid']
                        print 'inserting shopblack, {}, {}'.format(shopid, itemid)
                        blacklist.insert(0, [shopid, itemid])
                        db.execute('insert into ataobao2.blacklist (type, args, value) values (:type, :args, :value)',
                                    dict(type='shopblack', args=str(shopid), value=str(itemid)))
    elif type == 'whitelist':
        for shopid in request.args.get('shopid', '0').split(','):
            try:
                shopid = int(shopid)
            except:
                shopid = 0
            if shopid == 0:
                pass
            else:
                print 'inserting shopwhite, {}'.format(shopid)
                whitelist.insert(0, [shopid, None])
                db.execute('insert into ataobao2.blacklist (type, args) values (:type, :args)',
                            dict(type='shopwhite', args=str(shopid)))
    return redirect('/blacklist/#'+type)

@app.route('/blacklist/del')
def blacklist_del():
    global blacklist, whitelist
    if whitelist is None:
        whitelist = []
    if blacklist is None:
        blacklist = []
    type = 'shop' + request.args.get('type', 'blacklist')[:-4]
    shopid = request.args.get('shopid', 0)
    print 'deleting {} {}'.format(type, shopid)
    blacklist = [r for r in blacklist if str(r[0]) != str(shopid)]
    whitelist = [r for r in whitelist if str(r[0]) != str(shopid)]
    db.execute('delete from ataobao2.blacklist where type=:type and args=:args',
                dict(type=type, args=str(shopid))) 

    return redirect('/blacklist/#'+request.args.get('type', 'blacklist'))
