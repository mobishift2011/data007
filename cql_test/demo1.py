#coding:utf-8

import cql

host = ""
port = ""
keyspace = ""


con = cql.connect(host, port, keyspace)
cursor = con.cursor()

cursor.execute("CQL QUERY", dict(kw='Foo', kw2='Bar'))


#     - cursor.description  # None initially, list of N tuples that represent
#                               the N columns in a row after an execute. Only
#                               contains type and name info, not values.
#     - cursor.rowcount     # -1 initially, N after an execute
#     - cursor.arraysize    # variable size of a fetchmany call
#     - cursor.fetchone()   # returns  a single row
#     - cursor.fetchmany()  # returns  self.arraysize # of rows
#     - cursor.fetchall()   # returns  all rows, don't do this.

cursor.execute("ANOTHER QUERY", **more_kwargs)
for row in cursor:  # Iteration is equivalent to lots of fetchone() calls
    doRowMagic(row)

cursor.close()
con.close()
