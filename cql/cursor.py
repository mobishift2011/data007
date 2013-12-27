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

import cql
from cql.decoders import SchemaDecoder
from cql.query import prepare_inline

_COUNT_DESCRIPTION = (None, None, None, None, None, None, None)
_VOID_DESCRIPTION = None

class Cursor:
    default_decoder = SchemaDecoder
    supports_prepared_queries = False
    supports_column_types = True
    supports_name_info = True

    def __init__(self, parent_connection):
        self._connection = parent_connection
        self.cql_major_version = parent_connection.cql_major_version

        # A list of 7-tuples corresponding to the column metadata for the
        # current row (populated on execute() and on fetchone()):
        #  (column_name, type_code, None, None, None, None, nulls_ok=True)
        self.description = None

        # A list of 2-tuples (name_bytes, type_code), corresponding to the
        # raw bytes of the column names for each column in the current row,
        # in order, and the types under which they can be deserialized
        self.name_info = None

        self.arraysize = 1
        self.rowcount = -1      # Populate on execute()
        self.compression = None
        self.consistency_level = None
        self.decoder = None

    ###
    # Cursor API
    ###

    def close(self):
        self._connection = None

    def pre_execution_setup(self):
        self.__checksock()
        self.rs_idx = 0
        self.rowcount = 0
        self.description = None
        self.name_info = None
        self.column_types = None

    def prepare_inline(self, query, params):
        try:
            return prepare_inline(query, params, self.cql_major_version)
        except KeyError, e:
            raise cql.ProgrammingError("Unmatched named substitution: " +
                                       "%s not given for %r" % (e, query))

    def execute(self, cql_query, params={}, decoder=None, consistency_level=None):
        # note that 'decoder' here is actually the decoder class, not the
        # instance to be used for decoding. bad naming, but it's in use now.
        if isinstance(cql_query, unicode):
            raise ValueError("CQL query must be bytes, not unicode")
        self.pre_execution_setup()
        prepared_q = self.prepare_inline(cql_query, params)
        cl = consistency_level or self.consistency_level
        response = self.get_response(prepared_q, cl)
        return self.process_execution_results(response, decoder=decoder)

    def execute_prepared(self, prepared_query, params={}, decoder=None,
                         consistency_level=None):
        # note that 'decoder' here is actually the decoder class, not the
        # instance to be used for decoding. bad naming, but it's in use now.
        self.pre_execution_setup()
        cl = consistency_level or self.consistency_level
        response = self.get_response_prepared(prepared_query, params, cl)
        return self.process_execution_results(response, decoder=decoder)

    def get_metadata_info(self, row):
        self.description = description = []
        self.name_info = name_info = []
        self.column_types = column_types = []
        for colid in self.columninfo(row):
            name, nbytes, vtype, ctype = self.get_column_metadata(colid)
            column_types.append(vtype)
            description.append((name, vtype.cass_parameterized_type(),
                                None, None, None, None, True))
            name_info.append((nbytes, ctype))

    def get_column_metadata(self, column_id):
        return self.decoder.decode_metadata_and_type(column_id)

    def decode_row(self, row):
        values = []
        bytevals = self.columnvalues(row)
        for val, vtype, nameinfo in zip(bytevals, self.column_types, self.name_info):
            values.append(self.decoder.decode_value(val, vtype, nameinfo[0]))
        return values

    def fetchone(self):
        self.__checksock()
        if self.rs_idx == len(self.result):
            return None

        row = self.result[self.rs_idx]
        self.rs_idx += 1
        if self.description is _COUNT_DESCRIPTION:
            return row
        else:
            if self.cql_major_version < 3:
                # (don't bother redecoding descriptions or names otherwise)
                self.get_metadata_info(row)
            return self.decode_row(row)

    def fetchmany(self, size=None):
        self.__checksock()
        if size is None:
            size = self.arraysize
        # we avoid leveraging fetchone here to avoid decoding metadata unnecessarily
        L = []
        while len(L) < size and self.rs_idx < len(self.result):
            row = self.result[self.rs_idx]
            self.rs_idx += 1
            L.append(self.decode_row(row))
        return L

    def fetchall(self):
        return self.fetchmany(len(self.result) - self.rs_idx)

    def executemany(self, operation_list, argslist):
        self.__checksock()
        opssize = len(operation_list)
        argsize = len(argslist)

        if opssize > argsize:
            raise cql.InterfaceError("Operations outnumber args for executemany().")
        elif opssize < argsize:
            raise cql.InterfaceError("Args outnumber operations for executemany().")

        for idx in xrange(opssize):
            self.execute(operation_list[idx], *argslist[idx])

    ###
    # extra, for cqlsh
    ###

    def _reset(self):
        self.rs_idx = 0

    ###
    # Iterator extension
    ###

    def next(self):
        if self.rs_idx >= len(self.result):
            raise StopIteration
        return self.fetchone()

    def __iter__(self):
        return self

    ###
    # Unsupported, unimplemented optionally
    ###

    def setinputsizes(self, sizes):
        pass # DO NOTHING

    def setoutputsize(self, size, *columns):
        pass # DO NOTHING

    def callproc(self, procname, *args):
        raise cql.NotSupportedError()

    def nextset(self):
        raise cql.NotSupportedError()

    ###
    # Helpers
    ###

    def __checksock(self):
        if self._connection is None or not self._connection.open_socket:
            raise cql.ProgrammingError("Cursor has been closed.")
