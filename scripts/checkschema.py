#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import argparse
from settings import DB_HOSTS
from models import db

schemafile = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'schema.cql'))
schema = open(schemafile).read()
keyspace = re.compile(r'use (\S+);', re.IGNORECASE).search(schema).group(1)

def import_schema():
    cmd = 'cqlsh {} -f {}'.format(DB_HOSTS[0].replace(':', ' '), schemafile)
    print cmd
    os.system(cmd)

def get_table_defs():
    tables = {}
    for table, code in re.compile(r'create table if not exists (\S+) \((.*?)\);', re.IGNORECASE|re.DOTALL).findall(schema):
        cols = {}
        for c in code.split('\n'):
            c = c.strip()
            if not c:
                continue
            if c.endswith(','):
                c = c[:-1]
            if c.lower().startswith('primary key'):
                pk = [x.strip() for x in re.compile(r'primary key \((.*)\)', re.IGNORECASE).search(c).group(1).split(',') if x]
            else:
                cname, ctype = c.split(' ', 1)
                ctype = ctype.strip().lower()
                if ctype.lower().endswith('primary key'):
                    ctype = ctype.rsplit(' ', 2)[0].lower()
                    pk = cname.split(', ')
                cols[cname] = ctype
        tables[table] = {'cols':cols, 'pk':pk}
    return tables

def get_table_live():
    v2t = {
        'org.apache.cassandra.db.marshal.UTF8Type': 'text',
        'org.apache.cassandra.db.marshal.LongType': 'bigint',
        'org.apache.cassandra.db.marshal.Int32Type': 'int',
        'org.apache.cassandra.db.marshal.FloatType': 'float',
        'org.apache.cassandra.db.marshal.TimestampType': 'timestamp',
        'org.apache.cassandra.db.marshal.BooleanType': 'boolean',
    }
    tables = {}
    cfs = db.execute('''select columnfamily_name, column_aliases, key_aliases
                        from system.schema_columnfamilies where keyspace_name=:keyspace''', 
                    dict(keyspace=keyspace), result=True).results
    for table, cols, keys in cfs:
        pk = eval(keys)
        pk.extend(eval(cols))
        cols = {}
        for cname, validator in db.execute('''select column_name, validator from system.schema_columns
                        where keyspace_name=:keyspace and columnfamily_name=:cfname allow filtering''',
                    dict(keyspace=keyspace, cfname=table), result=True).results:
            cols[cname] = v2t.get(validator, validator)
        tables[table] = {'cols':cols, 'pk':pk}
    return tables


def check_schema(fix=False):
    t1 = get_table_defs()
    t2 = get_table_live()
    problems = 0
    plans = []
    for table in t1:
        print 'checking table {}'.format(table)
        t1t = t1[table]
        if table not in t2: 
            print '... table {} does not exists'.format(table)
            problems += 1
            stmt = ['create table {}.{} ('.format(keyspace, table)]
            for cname, ctype in t1t['cols'].items():
                stmt.append('  {} {},'.format(cname, ctype))
            stmt.append('  primary key ({})'.format(', '.join(t1t['pk'])))
            stmt.append(');')
            plans.append('\n'.join(stmt))
            continue

        t2t = t2[table]
        if t1t['pk'] != t2t['pk']:
            print '... primary key differs'
            problems += 1
            plans.append('drop table {}.{}'.format(keyspace, table))
            stmt = ['create table {}.{} ('.format(keyspace, table)]
            for cname, ctype in t1t['cols'].items():
                stmt.append('  {} {},'.format(cname, ctype))
            stmt.append('  primary key ({})'.format(', '.join(t1t['pk'])))
            stmt.append(');')
            plans.append('\n'.join(stmt))
            continue

        t2tcnames = set(t2t['cols'].keys()) 
        t1tcnames = set(t1t['cols'].keys())
        missing = list(t1tcnames - t2tcnames)
        unused = list(t2tcnames - t1tcnames)

        if missing:
            print '... missing columns {}'.format(missing)
            for cname in missing:
                ctype = t1t['cols'][cname]
                problems += 1
                plans.append('alter table {}.{} add {} {}'.format(keyspace, table, cname, ctype))

        if unused:
            print '... unused columns {}'.format(unused)
            for cname in unused:
                problems += 1
                if cname in t2t['pk']:
                    print('... oops you are going to delete a primary key, the only way of doing it is to recreate the table')
                    plans.append('drop table {}.{}'.format(keyspace, table))
                    stmt = ['create table {}.{} ('.format(keyspace, table)]
                    for cname, ctype in t1t['cols'].items():
                        stmt.append('  {} {},'.format(cname, ctype))
                    stmt.append('  primary key ({})'.format(', '.join(t1t['pk'])))
                    stmt.append(');')
                    plans.append('\n'.join(stmt))
                else:
                    plans.append('alter table {}.{} drop {}'.format(keyspace, table, cname))

        for cname, ctype in t1t['cols'].items():
            if cname in t2t['cols'] and t2t['cols'][cname] != ctype:
                wtype = t2t['cols'][cname]
                print '... {} has wrong type {}, != {}'.format(cname, wtype, ctype)
                problems += 1
                if cname in t2t['pk']:
                    print '... unfortunately this field is in primary key, we need to rebuild the whole table!!!'
                    plans.append('drop table {}.{}'.format(keyspace, table))
                    stmt = ['create table {}.{} ('.format(keyspace, table)]
                    for cname, ctype in t1t['cols'].items():
                        stmt.append('  {} {},'.format(cname, ctype))
                    stmt.append('  primary key ({})'.format(', '.join(t1t['pk'])))
                    stmt.append(');')
                    plans.append('\n'.join(stmt))
                else:
                    plans.append('alter table {}.{} drop {} '.format(keyspace, table, cname))
                    plans.append('alter table {}.{} add {} {}'.format(keyspace, table, cname, ctype))
    
    print 'check finished, {} problems found'.format(problems)
    if plans:
        print 'fix plans:'
        for plan in plans:
            print ' ', plan.replace('\n', '\n  ')
            if fix:
                db.execute(plan)
        if fix:
            print 'fixed'

def main():
    parser = argparse.ArgumentParser(description='Check (and fix) cql schemas for cassandra')
    parser.add_argument('-f', '--fix', help='run plans against cassandra', action='store_true')
    args = parser.parse_args()
    check_schema(fix=args.fix)

if __name__ == '__main__':
    main()
