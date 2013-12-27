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

from cql.apivalues import ProgrammingError, NotSupportedError

class Connection(object):
    cql_major_version = 3

    def __init__(self, host, port, keyspace, user=None, password=None, cql_version=None,
                 compression=None, consistency_level="ONE", transport=None):
        """
        Params:
        * host ...............: hostname of Cassandra node.
        * port ...............: port number to connect to.
        * keyspace ...........: keyspace to connect to.
        * user ...............: username used in authentication (optional).
        * password ...........: password used in authentication (optional).
        * cql_version.........: CQL version to use (optional).
        * compression.........: whether to use compression. For Thrift connections,
        *                       this can be None or the name of some supported
        *                       compression type (like "GZIP"). For native
        *                       connections, this is treated as a boolean, and if
        *                       true, the connection will try to find a type of
        *                       compression supported by both sides.
        * consistency_level ..: consistency level to use for CQL3 queries (optional);
        *                       "ONE" is the default CL, other supported values are:
        *                       "ANY", "TWO", "THREE", "QUORUM", "LOCAL_ONE", "LOCAL_QUORUM",
        *                       "EACH_QUORUM" and "ALL";
        *                       overridable on per-query basis.
        * transport...........: Thrift transport to use (optional);
        *                       not applicable to NativeConnection.
        """
        self.host = host
        self.port = port
        self.keyspace = keyspace
        self.cql_version = cql_version
        self.compression = compression
        self.consistency_level = consistency_level
        self.transport = transport
        self.open_socket = False

        self.credentials = None
        if user or password:
            self.credentials = {"username": user, "password": password}

        self.establish_connection()
        self.open_socket = True

        if self.keyspace:
            self.set_initial_keyspace(self.keyspace)

    def __str__(self):
        return ("%s(host=%r, port=%r, keyspace=%r, %s)"
                % (self.__class__.__name__, self.host, self.port, self.keyspace,
                   self.open_socket and 'conn open' or 'conn closed'))

    def keyspace_changed(self, keyspace):
        self.keyspace = keyspace

    ###
    # Connection API
    ###

    def close(self):
        if not self.open_socket:
            return
        self.terminate_connection()
        self.open_socket = False

    def commit(self):
        """
        'Database modules that do not support transactions should
          implement this method with void functionality.'
        """
        return

    def rollback(self):
        raise NotSupportedError("Rollback functionality not present in Cassandra.")

    def cursor(self):
        if not self.open_socket:
            raise ProgrammingError("Connection has been closed.")
        curs = self.cursorclass(self)
        curs.compression = self.compression
        curs.consistency_level = self.consistency_level
        return curs

# TODO: Pull connections out of a pool instead.
def connect(host, port=None, keyspace=None, user=None, password=None,
            cql_version=None, native=False, compression=None,
            consistency_level="ONE", transport=None):
    """
    Create a connection to a Cassandra node.

    @param host Hostname of Cassandra node.
    @param port Port number to connect to (default 9160 for thrift, 8000
                for native)
    @param keyspace If set, authenticate to this keyspace on connection.
    @param user If set, use this username in authentication.
    @param password If set, use this password in authentication.
    @param cql_version If set, try to use the given CQL version. If unset,
                uses the default for the connection.
    @param compression Whether to use compression. For Thrift connections,
                this can be None or the name of some supported compression
                type (like "GZIP"). For native connections, this is treated
                as a boolean, and if true, the connection will try to find
                a type of compression supported by both sides.
    @param consistency_level Consistency level to use for CQL3 queries (optional);
                "ONE" is the default CL, other supported values are:
                "ANY", "TWO", "THREE", "QUORUM", "LOCAL_QUORUM",
                "EACH_QUORUM" and "ALL"; overridable on per-query basis.
    @param transport If set, use this Thrift transport instead of creating one;
                doesn't apply to native connections.

    @returns a Connection instance of the appropriate subclass.
    """

    if native:
        from native import NativeConnection
        connclass = NativeConnection
        if port is None:
            port = 8000
    else:
        from thrifteries import ThriftConnection
        connclass = ThriftConnection
        if port is None:
            port = 9160
    return connclass(host, port, keyspace, user, password,
                     cql_version=cql_version, compression=compression,
                     consistency_level=consistency_level, transport=transport)
