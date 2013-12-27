# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import zlib
import cql
from cql.cursor import Cursor, _VOID_DESCRIPTION, _COUNT_DESCRIPTION
from cql.query import cql_quote, cql_quote_name, prepare_query, PreparedQuery
from cql.connection import Connection
from cql.cassandra import Cassandra
from thrift.Thrift import TApplicationException
from thrift.transport import TTransport, TSocket
from thrift.protocol import TBinaryProtocol
from cql.cassandra.ttypes import (AuthenticationRequest, Compression,
        ConsistencyLevel, CqlResultType, InvalidRequestException,
        UnavailableException, TimedOutException, SchemaDisagreementException)

MIN_THRIFT_FOR_PREPARED_QUERIES = (19, 27, 0)
MIN_THRIFT_FOR_CL_IN_PROTOCOL = (19, 35, 0)

class ThriftCursor(Cursor):
    def __init__(self, parent_connection):
        Cursor.__init__(self, parent_connection)

        if hasattr(parent_connection.client, 'execute_prepared_cql_query') \
                and parent_connection.remote_thrift_version >= MIN_THRIFT_FOR_PREPARED_QUERIES:
            self.supports_prepared_queries = True

        cl_in_protocol = parent_connection.remote_thrift_version >= MIN_THRIFT_FOR_CL_IN_PROTOCOL
        self.use_cql3_methods = cl_in_protocol and self.cql_major_version == 3

    def compress_query_text(self, querytext):
        if self.compression == 'GZIP':
            compressed_q = zlib.compress(querytext)
        else:
            compressed_q = querytext
        req_compression = getattr(Compression, self.compression or 'NONE')
        return compressed_q, req_compression

    def prepare_query(self, query):
        if isinstance(query, unicode):
            raise ValueError("CQL query must be bytes, not unicode")
        prepared_q_text, paramnames = prepare_query(query)
        compressed_q, compression = self.compress_query_text(prepared_q_text)

        if self.use_cql3_methods:
            doquery = self._connection.client.prepare_cql3_query
        else:
            doquery = self._connection.client.prepare_cql_query

        presult = doquery(compressed_q, compression)

        assert presult.count == len(paramnames)
        if presult.variable_types is None and presult.count > 0:
            raise cql.ProgrammingError("Cassandra did not provide types for bound"
                                       " parameters. Prepared statements are only"
                                       " supported with cql3.")
        return PreparedQuery(query, presult.itemId, presult.variable_types, paramnames)

    def get_response(self, cql_query, consistency_level):
        compressed_q, compress = self.compress_query_text(cql_query)
        cl = getattr(ConsistencyLevel, consistency_level)
        if self.use_cql3_methods:
            doquery = self._connection.client.execute_cql3_query
            return self.handle_cql_execution_errors(doquery, compressed_q, compress, cl)
        else:
            doquery = self._connection.client.execute_cql_query
            return self.handle_cql_execution_errors(doquery, compressed_q, compress)

    def get_response_prepared(self, prepared_query, params, consistency_level):
        paramvals = prepared_query.encode_params(params)
        cl = getattr(ConsistencyLevel, consistency_level)
        if self.use_cql3_methods:
            doquery = self._connection.client.execute_prepared_cql3_query
            return self.handle_cql_execution_errors(doquery, prepared_query.itemid,
                                                    paramvals, cl)
        else:
            doquery = self._connection.client.execute_prepared_cql_query
            return self.handle_cql_execution_errors(doquery, prepared_query.itemid,
                                                    paramvals)

    def handle_cql_execution_errors(self, executor, *args, **kwargs):
        try:
            return executor(*args, **kwargs)
        except InvalidRequestException, ire:
            raise cql.ProgrammingError("Bad Request: %s" % ire.why)
        except SchemaDisagreementException, sde:
            raise cql.IntegrityError("Schema versions disagree, (try again later).")
        except UnavailableException:
            raise cql.OperationalError("Unable to complete request: one or "
                                       "more nodes were unavailable.")
        except TimedOutException:
            raise cql.OperationalError("Request did not complete within rpc_timeout.")
        except TApplicationException, tapp:
            raise cql.InternalError("Internal application error")

    def process_execution_results(self, response, decoder=None):
        if response.type == CqlResultType.ROWS:
            self.decoder = (decoder or self.default_decoder)(response.schema)
            self.result = [r.columns for r in response.rows]
            self.rs_idx = 0
            self.rowcount = len(self.result)
            if self.result:
                self.get_metadata_info(self.result[0])
        elif response.type == CqlResultType.INT:
            self.result = [(response.num,)]
            self.rs_idx = 0
            self.rowcount = 1
            # TODO: name could be the COUNT expression
            self.description = _COUNT_DESCRIPTION
            self.name_info = None
        elif response.type == CqlResultType.VOID:
            self.result = []
            self.rs_idx = 0
            self.rowcount = 0
            self.description = _VOID_DESCRIPTION
            self.name_info = ()
        else:
            raise Exception('unknown result type %s' % response.type)

        # 'Return values are not defined.'
        return True

    def columnvalues(self, row):
        return [column.value for column in row]

    def columninfo(self, row):
        return (column.name for column in row)

class ThriftConnection(Connection):
    cursorclass = ThriftCursor

    def establish_connection(self):
        if self.transport is None:
            socket = TSocket.TSocket(self.host, self.port)
            self.transport = TTransport.TFramedTransport(socket)

        if not self.transport.isOpen():
            self.transport.open()

        protocol = TBinaryProtocol.TBinaryProtocolAccelerated(self.transport)
        self.client = Cassandra.Client(protocol)

        if self.credentials:
            self.client.login(AuthenticationRequest(credentials=self.credentials))

        self.remote_thrift_version = tuple(map(int, self.client.describe_version().split('.')))

        if self.cql_version:
            self.set_cql_version(self.cql_version)

    def set_cql_version(self, cql_version):
        if self.remote_thrift_version < MIN_THRIFT_FOR_CL_IN_PROTOCOL:
            self.client.set_cql_version(cql_version)
        try:
            self.cql_major_version = int(cql_version.split('.')[0])
        except ValueError:
            pass

    def set_initial_keyspace(self, keyspace):
        c = self.cursor()
        if self.cql_major_version >= 3:
            ksname = cql_quote_name(keyspace)
        else:
            ksname = cql_quote(keyspace)
        c.execute('USE %s' % ksname)
        c.close()

    def terminate_connection(self):
        self.transport.close()
