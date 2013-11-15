#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from models import db
from webadmin import app
from flask import request, render_template

import traceback

KEYSPACE = 'ataobao2'

def paginate(count=0, page=1, limit=20, **kwargs):
    offset = (page - 1) * limit
    next_offset = offset + limit
    pages = [page]
    prev_page = page - 1
    next_page = page + 1
    prev_page_limit = kwargs.get('prev_page_limit', 2)
    next_page_limit = kwargs.get('next_page_limit', 2)
    total_page = (count / limit) + int(bool(count % limit))

    while prev_page and prev_page_limit:
        pages.append(prev_page)
        prev_page -= 1
        prev_page_limit -= 1

    while (next_page <= total_page) and next_page_limit:
        pages.append(next_page)
        next_page +=1
        next_page_limit -= 1

    pages.sort()
    paginator = {
        'count': count,
        'limit': limit,
        'current': page,
        'pages': pages,
        'next_offset': min(next_offset, count),
        'has_previous': bool(offset > 0),
        'has_next': bool(next_offset < count),
    }
    return paginator

@app.route('/cqlui/')
def cqlui_index():
    return render_template('cqlui/index.html')

@app.route('/cqlui/table/<string:table>/', methods=['GET', 'POST'])
def cqlui_table(table):
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 20))
    order_by = request.args.get('order_by')
    limit_clause = 'limit {}'.format(limit)
    where_clause = ''
    order_by_clause = ''

    try:
        if request.method == 'POST':
            for k, v in request.form.iteritems():
                if not k or not v:
                    continue
                if not where_clause:
                    where_clause = 'where {} = {}'.format(k, v)
                else:
                    where_clause += 'and {} = {}'.format(k, v)

        if order_by:
            order_by_clause = 'order by {} {}'.format(order_by, request.args.get('scend')).strip()

        count = int(db.execute('select count(*) from {}.{} {}'.format(\
            KEYSPACE, table, where_clause), result=True)[1][0][0])
        columns, rows = db.execute('select * from {}.{} {} {} {}'.format(\
            KEYSPACE, table, where_clause, order_by_clause, limit_clause), result=True)
    except:
        traceback.print_exc()
        count = 0
        try:
            columns, rows = db.execute('select * from {}.{} {}'.format(\
                KEYSPACE, table, limit_clause), result=True)
            rows = []
        except:
            traceback.print_exc()

    return render_template('cqlui/table.html', \
        columns=columns, rows=rows, table=table, **paginate(count=count, page=page, limit=limit))