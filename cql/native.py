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
from cql.marshal import (int32_pack, int32_unpack, uint16_pack, uint16_unpack,
                         int8_pack, int8_unpack)
from cql.cqltypes import lookup_cqltype
from cql.connection import Connection
from cql.cursor import Cursor, _VOID_DESCRIPTION, _COUNT_DESCRIPTION
from cql.apivalues import ProgrammingError, OperationalError
from cql.query import PreparedQuery, prepare_query, cql_quote_name
import socket
import itertools
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


PROTOCOL_VERSION             = 0x01
PROTOCOL_VERSION_MASK        = 0x7f

HEADER_DIRECTION_FROM_CLIENT = 0x00
HEADER_DIRECTION_TO_CLIENT   = 0x80
HEADER_DIRECTION_MASK        = 0x80

class ConsistencyLevel(object):
    @classmethod
    def name_from_value(cls, value):
        return {0: 'ANY',
                1: 'ONE',
                2: 'TWO',
                3: 'THREE',
                4: 'QUORUM',
                5: 'ALL',
                6: 'LOCAL_QUORUM',
                7: 'EACH_QUORUM',
                10:'LOCAL_ONE'}[value]

    @classmethod
    def value_from_name(cls, name):
        return {'ANY': 0,
                'ONE': 1,
                'TWO': 2,
                'THREE': 3,
                'QUORUM': 4,
                'ALL': 5,
                'LOCAL_QUORUM': 6,
                'EACH_QUORUM': 7,
                'LOCAL_ONE': 10}[name]

class CqlResult:
    def __init__(self, column_metadata, rows):
        self.column_metadata = column_metadata
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)

    def __str__(self):
        return '<CqlResult: column_metadata=%r, rows=%r>' \
               % (self.column_metadata, self.rows)
    __repr__ = __str__

class PreparedResult:
    def __init__(self, queryid, param_metadata):
        self.queryid = queryid
        self.param_metadata = param_metadata

    def __str__(self):
        return '<PreparedResult: queryid=%r, column_metadata=%r>' \
               % (self.queryid, self.column_metadata)
    __repr__ = __str__


_message_types_by_name = {}
_message_types_by_opcode = {}

class _register_msg_type(type):
    def __init__(cls, name, bases, dct):
        if not name.startswith('_'):
            _message_types_by_name[cls.name] = cls
            _message_types_by_opcode[cls.opcode] = cls

class _MessageType(object):
    __metaclass__ = _register_msg_type
    params = ()

    def __init__(self, **kwargs):
        for pname in self.params:
            try:
                pval = kwargs[pname]
            except KeyError:
                raise ValueError("%s instances need the %s keyword parameter"
                                 % (self.__class__.__name__, pname))
            setattr(self, pname, pval)

    def send(self, f, streamid, compression=None):
        body = StringIO()
        self.send_body(body)
        body = body.getvalue()
        version = PROTOCOL_VERSION | HEADER_DIRECTION_FROM_CLIENT
        flags = 0
        if compression is not None and len(body) > 0:
            body = compression(body)
            flags |= 0x1
        msglen = int32_pack(len(body))
        header = ''.join(map(int8_pack, (version, flags, streamid, self.opcode))) \
                 + msglen
        f.write(header)
        if len(body) > 0:
            f.write(body)

    def __str__(self):
        paramstrs = ['%s=%r' % (pname, getattr(self, pname)) for pname in self.params]
        return '<%s(%s)>' % (self.__class__.__name__, ', '.join(paramstrs))
    __repr__ = __str__

def read_frame(f, decompressor=None):
    header = f.read(8)
    version, flags, stream, opcode = map(int8_unpack, header[:4])
    body_len = int32_unpack(header[4:])
    assert version & PROTOCOL_VERSION_MASK == PROTOCOL_VERSION, \
            "Unsupported CQL protocol version %d" % version
    assert version & HEADER_DIRECTION_MASK == HEADER_DIRECTION_TO_CLIENT, \
            "Unexpected request from server with opcode %04x, stream id %r" % (opcode, stream)
    assert body_len >= 0, "Invalid CQL protocol body_len %r" % body_len
    body = f.read(body_len)
    if flags & 0x1:
        if decompressor is None:
            raise ProtocolException("No decompressor available for compressed frame!")
        body = decompressor(body)
        flags ^= 0x1
    if flags:
        warn("Unknown protocol flags set: %02x. May cause problems." % flags)
    msgclass = _message_types_by_opcode[opcode]
    msg = msgclass.recv_body(StringIO(body))
    msg.stream_id = stream
    return msg

error_classes = {}

class ErrorMessage(_MessageType):
    opcode = 0x00
    name = 'ERROR'
    params = ('code', 'message', 'info')
    summary = 'Unknown'

    @classmethod
    def recv_body(cls, f):
        code = read_int(f)
        msg = read_string(f)
        subcls = error_classes.get(code, cls)
        extra_info = subcls.recv_error_info(f)
        return subcls(code=code, message=msg, info=extra_info)

    def summarymsg(self):
        msg = 'code=%04x [%s] message="%s"' \
              % (self.code, self.summary, self.message)
        if self.info is not None:
            msg += (' info=' + str(self.info))
        return msg

    def __str__(self):
        return '<ErrorMessage %s>' % self.summarymsg()
    __repr__ = __str__

    @staticmethod
    def recv_error_info(f):
        pass

class ErrorMessageSubclass(_register_msg_type):
    def __init__(cls, name, bases, dct):
        if cls.errorcode is not None:
            error_classes[cls.errorcode] = cls

class ErrorMessageSub(ErrorMessage):
    __metaclass__ = ErrorMessageSubclass
    errorcode = None

class RequestExecutionException(ErrorMessageSub):
    pass

class RequestValidationException(ErrorMessageSub):
    pass

class ServerError(ErrorMessageSub):
    summary = 'Server error'
    errorcode = 0x0000

class ProtocolException(ErrorMessageSub):
    summary = 'Protocol error'
    errorcode = 0x000A

class UnavailableExceptionErrorMessage(RequestExecutionException):
    summary = 'Unavailable exception'
    errorcode = 0x1000

    @staticmethod
    def recv_error_info(f):
        return {
            'consistencylevel': read_consistencylevel(f),
            'required': read_int(f),
            'alive': read_int(f),
        }

class OverloadedErrorMessage(RequestExecutionException):
    summary = 'Coordinator node overloaded'
    errorcode = 0x1001

class IsBootstrappingErrorMessage(RequestExecutionException):
    summary = 'Coordinator node is bootstrapping'
    errorcode = 0x1002

class TruncateError(RequestExecutionException):
    summary = 'Error during truncate'
    errorcode = 0x1003

class RequestTimeoutException(RequestExecutionException):
    pass

class WriteTimeoutErrorMessage(RequestTimeoutException):
    summary = 'Timeout during write request'
    errorcode = 0x1100

    @staticmethod
    def recv_error_info(f):
        return {
            'consistencylevel': read_consistencylevel(f),
            'received': read_int(f),
            'blockfor': read_int(f),
            'writetype': read_string(f),
        }

class ReadTimeoutErrorMessage(RequestTimeoutException):
    summary = 'Timeout during read request'
    errorcode = 0x1200

    @staticmethod
    def recv_error_info(f):
        return {
            'consistencylevel': read_consistencylevel(f),
            'received': read_int(f),
            'blockfor': read_int(f),
            'data_present': bool(read_byte(f)),
        }

class SyntaxException(RequestValidationException):
    summary = 'Syntax error in CQL query'
    errorcode = 0x2000

class UnauthorizedErrorMessage(RequestValidationException):
    summary = 'Unauthorized'
    errorcode = 0x2100

class InvalidRequestException(RequestValidationException):
    summary = 'Invalid query'
    errorcode = 0x2200

class ConfigurationException(RequestValidationException):
    summary = 'Query invalid because of configuration issue'
    errorcode = 0x2300

class AlreadyExistsException(ConfigurationException):
    summary = 'Item already exists'
    errorcode = 0x2400

    @staticmethod
    def recv_error_info(f):
        return {
            'keyspace': read_string(f),
            'table': read_string(f),
        }

class StartupMessage(_MessageType):
    opcode = 0x01
    name = 'STARTUP'
    params = ('cqlversion', 'options')

    KNOWN_OPTION_KEYS = set((
        'CQL_VERSION',
        'COMPRESSION',
    ))

    def send_body(self, f):
        optmap = self.options.copy()
        optmap['CQL_VERSION'] = self.cqlversion
        write_stringmap(f, optmap)

class ReadyMessage(_MessageType):
    opcode = 0x02
    name = 'READY'
    params = ()

    @classmethod
    def recv_body(cls, f):
        return cls()

class AuthenticateMessage(_MessageType):
    opcode = 0x03
    name = 'AUTHENTICATE'
    params = ('authenticator',)

    @classmethod
    def recv_body(cls, f):
        authname = read_string(f)
        return cls(authenticator=authname)

class CredentialsMessage(_MessageType):
    opcode = 0x04
    name = 'CREDENTIALS'
    params = ('creds',)

    def send_body(self, f):
        write_short(f, len(self.creds))
        for credkey, credval in self.creds:
            write_string(f, credkey)
            write_string(f, credval)

class OptionsMessage(_MessageType):
    opcode = 0x05
    name = 'OPTIONS'
    params = ()

    def send_body(self, f):
        pass

class SupportedMessage(_MessageType):
    opcode = 0x06
    name = 'SUPPORTED'
    params = ('cqlversions', 'options',)

    @classmethod
    def recv_body(cls, f):
        options = read_stringmultimap(f)
        cqlversions = options.pop('CQL_VERSION')
        return cls(cqlversions=cqlversions, options=options)

class QueryMessage(_MessageType):
    opcode = 0x07
    name = 'QUERY'
    params = ('query', 'consistencylevel',)

    def send_body(self, f):
        write_longstring(f, self.query)
        write_consistencylevel(f, self.consistencylevel)

class ResultMessage(_MessageType):
    opcode = 0x08
    name = 'RESULT'
    params = ('kind', 'results',)

    KIND_VOID          = 0x0001
    KIND_ROWS          = 0x0002
    KIND_SET_KEYSPACE  = 0x0003
    KIND_PREPARED      = 0x0004
    KIND_SCHEMA_CHANGE = 0x0005

    type_codes = {
        0x0001: 'ascii',
        0x0002: 'bigint',
        0x0003: 'blob',
        0x0004: 'boolean',
        0x0005: 'counter',
        0x0006: 'decimal',
        0x0007: 'double',
        0x0008: 'float',
        0x0009: 'int',
        0x000A: 'text',
        0x000B: 'timestamp',
        0x000C: 'uuid',
        0x000D: 'varchar',
        0x000E: 'varint',
        0x000F: 'timeuuid',
        0x0010: 'inet',
        0x0020: 'list',
        0x0021: 'map',
        0x0022: 'set',
    }

    FLAGS_GLOBAL_TABLES_SPEC = 0x0001

    @classmethod
    def recv_body(cls, f):
        kind = read_int(f)
        if kind == cls.KIND_VOID:
            results = None
        elif kind == cls.KIND_ROWS:
            results = cls.recv_results_rows(f)
        elif kind == cls.KIND_SET_KEYSPACE:
            ksname = read_string(f)
            results = ksname
        elif kind == cls.KIND_PREPARED:
            results = cls.recv_results_prepared(f)
        elif kind == cls.KIND_SCHEMA_CHANGE:
            results = cls.recv_results_schema_change(f)
        return cls(kind=kind, results=results)

    @classmethod
    def recv_results_rows(cls, f):
        colspecs = cls.recv_results_metadata(f)
        rowcount = read_int(f)
        rows = [cls.recv_row(f, len(colspecs)) for x in xrange(rowcount)]
        return CqlResult(column_metadata=colspecs, rows=rows)

    @classmethod
    def recv_results_prepared(cls, f):
        queryid = read_shortbytes(f)
        colspecs = cls.recv_results_metadata(f)
        return (queryid, colspecs)

    @classmethod
    def recv_results_metadata(cls, f):
        flags = read_int(f)
        glob_tblspec = bool(flags & cls.FLAGS_GLOBAL_TABLES_SPEC)
        colcount = read_int(f)
        if glob_tblspec:
            ksname = read_string(f)
            cfname = read_string(f)
        colspecs = []
        for x in xrange(colcount):
            if glob_tblspec:
                colksname = ksname
                colcfname = cfname
            else:
                colksname = read_string(f)
                colcfname = read_string(f)
            colname = read_string(f)
            coltype = cls.read_type(f)
            colspecs.append((colksname, colcfname, colname, coltype))
        return colspecs

    @classmethod
    def recv_results_schema_change(cls, f):
        change = read_string(f)
        ks = read_string(f)
        cf = read_string(f)
        return (change, ks, cf)

    @classmethod
    def read_type(cls, f):
        optid = read_short(f)
        try:
            cqltype = lookup_cqltype(cls.type_codes[optid])
        except KeyError:
            raise cql.NotSupportedError("Unknown data type code 0x%x. Have to skip"
                                        " entire result set." % optid)
        if cqltype.typename in ('list', 'set'):
            subtype = cls.read_type(f)
            cqltype = cqltype.apply_parameters(subtype)
        elif cqltype.typename == 'map':
            keysubtype = cls.read_type(f)
            valsubtype = cls.read_type(f)
            cqltype = cqltype.apply_parameters(keysubtype, valsubtype)
        return cqltype

    @staticmethod
    def recv_row(f, colcount):
        return [read_value(f) for x in xrange(colcount)]

class PrepareMessage(_MessageType):
    opcode = 0x09
    name = 'PREPARE'
    params = ('query',)

    def send_body(self, f):
        write_longstring(f, self.query)

class ExecuteMessage(_MessageType):
    opcode = 0x0A
    name = 'EXECUTE'
    params = ('queryid', 'queryparams', 'consistencylevel',)

    def send_body(self, f):
        write_shortbytes(f, self.queryid)
        write_short(f, len(self.queryparams))
        for param in self.queryparams:
            write_value(f, param)
        write_consistencylevel(f, self.consistencylevel)

known_event_types = frozenset((
    'TOPOLOGY_CHANGE',
    'STATUS_CHANGE',
))

class RegisterMessage(_MessageType):
    opcode = 0x0B
    name = 'REGISTER'
    params = ('eventlist',)

    def send_body(self, f):
        write_stringlist(f, self.eventlist)

class EventMessage(_MessageType):
    opcode = 0x0C
    name = 'EVENT'
    params = ('eventtype', 'eventargs')

    @classmethod
    def recv_body(cls, f):
        eventtype = read_string(f).upper()
        if eventtype in known_event_types:
            readmethod = getattr(cls, 'recv_' + eventtype.lower())
            return cls(eventtype=eventtype, eventargs=readmethod(f))
        raise cql.NotSupportedError('Unknown event type %r' % eventtype)

    @classmethod
    def recv_topology_change(cls, f):
        # "NEW_NODE" or "REMOVED_NODE"
        changetype = read_string(f)
        address = read_inet(f)
        return dict(changetype=changetype, address=address)

    @classmethod
    def recv_status_change(cls, f):
        # "UP" or "DOWN"
        changetype = read_string(f)
        address = read_inet(f)
        return dict(changetype=changetype, address=address)


def read_byte(f):
    return int8_unpack(f.read(1))

def write_byte(f, b):
    f.write(int8_pack(b))

def read_int(f):
    return int32_unpack(f.read(4))

def write_int(f, i):
    f.write(int32_pack(i))

def read_short(f):
    return uint16_unpack(f.read(2))

def write_short(f, s):
    f.write(uint16_pack(s))

def read_consistencylevel(f):
    return ConsistencyLevel.name_from_value(read_short(f))

def write_consistencylevel(f, cl):
    write_short(f, ConsistencyLevel.value_from_name(cl))

def read_string(f):
    size = read_short(f)
    contents = f.read(size)
    return contents.decode('utf8')

def write_string(f, s):
    if isinstance(s, unicode):
        s = s.encode('utf8')
    write_short(f, len(s))
    f.write(s)

def read_longstring(f):
    size = read_int(f)
    contents = f.read(size)
    return contents.decode('utf8')

def write_longstring(f, s):
    if isinstance(s, unicode):
        s = s.encode('utf8')
    write_int(f, len(s))
    f.write(s)

def read_shortbytes(f):
    size = read_short(f)
    contents = f.read(size)
    return contents.encode('hex')

def write_shortbytes(f, sb):
    decoded = sb.decode('hex')
    write_short(f, len(decoded))
    f.write(decoded)

def read_stringlist(f):
    numstrs = read_short(f)
    return [read_string(f) for x in xrange(numstrs)]

def write_stringlist(f, stringlist):
    write_short(f, len(stringlist))
    for s in stringlist:
        write_string(f, s)

def read_stringmap(f):
    numpairs = read_short(f)
    strmap = {}
    for x in xrange(numpairs):
        k = read_string(f)
        strmap[k] = read_string(f)
    return strmap

def write_stringmap(f, strmap):
    write_short(f, len(strmap))
    for k, v in strmap.items():
        write_string(f, k)
        write_string(f, v)

def read_stringmultimap(f):
    numkeys = read_short(f)
    strmmap = {}
    for x in xrange(numkeys):
        k = read_string(f)
        strmmap[k] = read_stringlist(f)
    return strmmap

def write_stringmultimap(f, strmmap):
    write_short(f, len(strmmap))
    for k, v in strmmap.items():
        write_string(f, k)
        write_stringlist(f, v)

def read_value(f):
    size = read_int(f)
    if size < 0:
        return None
    return f.read(size)

def write_value(f, v):
    if v is None:
        write_int(f, -1)
    else:
        write_int(f, len(v))
        f.write(v)

def read_inet(f):
    size = read_byte(f)
    addrbytes = f.read(size)
    port = read_int(f)
    if size == 4:
        addrfam = socket.AF_INET
    elif size == 16:
        addrfam = socket.AF_INET6
    else:
        raise cql.InternalError("bad inet address: %r" % (addrbytes,))
    return (socket.inet_ntop(addrfam, addrbytes), port)

def write_inet(f, addrtuple):
    addr, port = addrtuple
    if ':' in addr:
        addrfam = socket.AF_INET6
    else:
        addrfam = socket.AF_INET
    addrbytes = socket.inet_pton(addrfam, addr)
    write_byte(f, len(addrbytes))
    f.write(addrbytes)
    write_int(f, port)


class NativeCursor(Cursor):
    def prepare_query(self, query):
        pquery, paramnames = prepare_query(query)
        prepared = self._connection.wait_for_request(PrepareMessage(query=pquery))
        if isinstance(prepared, ErrorMessage):
            raise cql.Error('Query preparation failed: %s' % prepared.summarymsg())
        if prepared.kind != ResultMessage.KIND_PREPARED:
            raise cql.InternalError('Query preparation did not result in prepared query')
        queryid, colspecs = prepared.results
        kss, cfs, names, ctypes = zip(*colspecs)
        return PreparedQuery(query, queryid, ctypes, paramnames)

    def get_response(self, query, consistency_level):
        qm = QueryMessage(query=query, consistencylevel=consistency_level)
        return self._connection.wait_for_request(qm)

    def get_response_prepared(self, prepared_query, params, consistency_level):
        qparams = [params[pname] for pname in prepared_query.paramnames]
        em = ExecuteMessage(queryid=prepared_query.itemid, queryparams=qparams,
                            consistencylevel=consistency_level)
        return self._connection.wait_for_request(em)

    def get_column_metadata(self, column_id):
        return self.decoder.decode_metadata_and_type_native(column_id)

    def columninfo(self, row):
        return xrange(len(row))

    def columnvalues(self, row):
        return row

    def handle_cql_execution_errors(self, response):
        if not isinstance(response, ErrorMessage):
            return
        if isinstance(response, UnauthorizedErrorMessage):
            eclass = cql.NotAuthenticated
        elif isinstance(response, RequestExecutionException):
            eclass = cql.OperationalError
        elif isinstance(response, RequestValidationException):
            eclass = cql.ProgrammingError
        else:
            eclass = cql.InternalError
        raise eclass(response.summarymsg())

    def process_execution_results(self, response, decoder=None):
        self.handle_cql_execution_errors(response)
        if not isinstance(response, ResultMessage):
            raise cql.InternalError('Query execution resulted in %s!?' % (response,))
        if response.kind == ResultMessage.KIND_PREPARED:
            raise cql.InternalError('Query execution resulted in prepared query!?')

        self.rs_idx = 0
        self.description = None
        self.result = []
        self.name_info = ()

        if response.kind == ResultMessage.KIND_VOID:
            self.description = _VOID_DESCRIPTION
        elif response.kind == ResultMessage.KIND_SET_KEYSPACE:
            self._connection.keyspace_changed(response.results)
            self.description = _VOID_DESCRIPTION
        elif response.kind == ResultMessage.KIND_ROWS:
            schema = response.results.column_metadata
            self.decoder = (decoder or self.default_decoder)(schema)
            self.result = response.results.rows
            if self.result:
                self.get_metadata_info(self.result[0])
        elif response.kind == ResultMessage.KIND_SCHEMA_CHANGE:
            self.description = _VOID_DESCRIPTION
        else:
            raise Exception('unknown response kind %s: %s' % (response.kind, response))
        self.rowcount = len(self.result)

    def get_compression(self):
        return self._connection.compression

    def set_compression(self, val):
        if val != self.get_compression():
            raise NotImplementedError("Setting per-cursor compression is not "
                                      "supported in NativeCursor.")

    compression = property(get_compression, set_compression)

class debugsock:
    def __init__(self, sock):
        self.sock = sock

    def write(self, data):
        print '[sending %r]' % (data,)
        self.sock.send(data)

    def read(self, readlen):
        data = ''
        while readlen > 0:
            add = self.sock.recv(readlen)
            print '[received %r]' % (add,)
            if add == '':
                raise cql.InternalError("short read of %s bytes (%s expected)"
                                        % (len(data), len(data) + readlen))
            data += add
            readlen -= len(add)
        return data

    def close(self):
        pass

locally_supported_compressions = {}

try:
    import snappy
except ImportError:
    pass
else:
    # work around apparently buggy snappy decompress
    def decompress(byts):
        if byts == '\x00':
            return ''
        return snappy.decompress(byts)
    locally_supported_compressions['snappy'] = (snappy.compress, decompress)

class NativeConnection(Connection):
    cursorclass = NativeCursor

    def __init__(self, *args, **kwargs):
        self.make_reqid = itertools.count().next
        self.responses = {}
        self.waiting = {}
        self.conn_ready = False
        self.compressor = self.decompressor = None
        self.event_watchers = {}
        Connection.__init__(self, *args, **kwargs)

    def establish_connection(self):
        self.conn_ready = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.host, self.port))
        self.socketf = s.makefile(bufsize=0)
        self.sockfd = s
        self.open_socket = True
        supported = self.wait_for_request(OptionsMessage())
        self.supported_cql_versions = supported.cqlversions
        self.remote_supported_compressions = supported.options['COMPRESSION']

        if self.cql_version:
            if self.cql_version not in self.supported_cql_versions:
                raise ProgrammingError("cql_version %r is not supported by"
                                       " remote (w/ native protocol). Supported"
                                       " versions: %r"
                                       % (self.cql_version, self.supported_cql_versions))
        else:
            self.cql_version = self.supported_cql_versions[0]

        opts = {}
        compresstype = None
        if self.compression:
            overlap = set(locally_supported_compressions) \
                    & set(self.remote_supported_compressions)
            if len(overlap) == 0:
                warn("No available compression types supported on both ends."
                     " locally supported: %r. remotely supported: %r"
                     % (locally_supported_compressions,
                        self.remote_supported_compressions))
            else:
                compresstype = iter(overlap).next() # choose any
                opts['COMPRESSION'] = compresstype
                compr, decompr = locally_supported_compressions[compresstype]
                # set the decompressor here, but set the compressor only after
                # a successful Ready message
                self.decompressor = decompr

        sm = StartupMessage(cqlversion=self.cql_version, options=opts)
        startup_response = self.wait_for_request(sm)
        while True:
            if isinstance(startup_response, ReadyMessage):
                self.conn_ready = True
                if compresstype:
                    self.compressor = compr
                break
            if isinstance(startup_response, AuthenticateMessage):
                self.authenticator = startup_response.authenticator
                if self.credentials is None:
                    raise ProgrammingError('Remote end requires authentication.')
                cm = CredentialsMessage(creds=self.credentials)
                startup_response = self.wait_for_request(cm)
            elif isinstance(startup_response, ErrorMessage):
                raise ProgrammingError("Server did not accept credentials. %s"
                                       % startup_response.summarymsg())
            else:
                raise cql.InternalError("Unexpected response %r during connection setup"
                                        % startup_response)


    def set_initial_keyspace(self, keyspace):
        c = self.cursor()
        c.execute('USE %s' % cql_quote_name(self.keyspace))
        c.close()

    def terminate_connection(self):
        self.socketf.close()
        self.sockfd.close()

    def wait_for_request(self, msg):
        """
        Given a message, send it to the server, wait for a response, and
        return the response.
        """

        return self.wait_for_requests(msg)[0]

    def send_msg(self, msg):
        reqid = self.make_reqid()
        msg.send(self.socketf, reqid, compression=self.compressor)
        return reqid

    def wait_for_requests(self, *msgs):
        """
        Given any number of message objects, send them all to the server
        and wait for responses to each one. Once they arrive, return all
        of the responses in the same order as the messages to which they
        respond.
        """

        reqids = []
        for msg in msgs:
            reqid = self.send_msg(msg)
            reqids.append(reqid)
        resultdict = self.wait_for_results(*reqids)
        return [resultdict[reqid] for reqid in reqids]

    def wait_for_results(self, *reqids):
        """
        Given any number of stream-ids, wait until responses have arrived for
        each one, and return a dictionary mapping the stream-ids to the
        appropriate results.

        For internal use, None may be passed in place of a reqid, which will
        be considered satisfied when a message of any kind is received (and, if
        appropriate, handled).
        """

        waiting_for = set(reqids)
        results = {}
        for r in reqids:
            try:
                result = self.responses.pop(r)
            except KeyError:
                pass
            else:
                results[r] = result
                waiting_for.remove(r)
        while waiting_for:
            newmsg = read_frame(self.socketf, decompressor=self.decompressor)
            if newmsg.stream_id in waiting_for:
                results[newmsg.stream_id] = newmsg
                waiting_for.remove(newmsg.stream_id)
            else:
                self.handle_incoming(newmsg)
            if None in waiting_for:
                results[None] = newmsg
                waiting_for.remove(None)
        return results

    def wait_for_result(self, reqid):
        """
        Given a stream-id, wait until a response arrives with that stream-id,
        and return the msg.
        """

        return self.wait_for_results(reqid)[reqid]

    def handle_incoming(self, msg):
        if msg.stream_id < 0:
            self.handle_pushed(msg)
            return
        try:
            cb = self.waiting.pop(msg.stream_id)
        except KeyError:
            self.responses[msg.stream_id] = msg
        else:
            cb(msg)

    def callback_when(self, reqid, cb):
        """
        Callback cb with a message object once a message with a stream-id
        of reqid is received. The callback may be immediate, if a response
        is already in the received queue.

        Otherwise, note also that the callback may not be called immediately
        upon the arrival of the response packet; it may have to wait until
        something else waits on a result.
        """

        try:
            msg = self.responses.pop(reqid)
        except KeyError:
            pass
        else:
            return cb(msg)
        self.waiting[reqid] = cb

    def request_and_callback(self, msg, cb):
        """
        Given a message msg and a callable cb, send the message to the server
        and call cb with the result once it arrives. Note that the callback
        may not be called immediately upon the arrival of the response packet;
        it may have to wait until something else waits on a result.
        """

        reqid = self.send_msg(msg)
        self.callback_when(reqid, cb)

    def handle_pushed(self, msg):
        """
        Process an incoming message originated by the server.
        """
        watchers = self.event_watchers.get(msg.eventtype, ())
        for cb in watchers:
            cb(msg.eventargs)

    def register_watcher(self, eventtype, cb):
        """
        Request that any events of the given type be passed to the given
        callback when they arrive. Note that the callback may not be called
        immediately upon the arrival of the event packet; it may have to wait
        until something else waits on a result, or until wait_for_even() is
        called.

        If the event type has not been registered for already, this may
        block while a new REGISTER message is sent to the server.

        The available event types are in the cql.native.known_event_types
        list.

        When an event arrives, a dictionary will be passed to the callback
        with the info about the event. Some example result dictionaries:

        (For STATUS_CHANGE events:)

          {'changetype': u'DOWN', 'address': ('12.114.19.76', 8000)}

        (For TOPOLOGY_CHANGE events:)

          {'changetype': u'NEW_NODE', 'address': ('19.10.122.13', 8000)}
        """

        if isinstance(eventtype, str):
            eventtype = eventtype.decode('utf8')
        try:
            watchers = self.event_watchers[eventtype]
        except KeyError:
            ans = self.wait_for_request(RegisterMessage(eventlist=(eventtype,)))
            if isinstance(ans, ErrorMessage):
                raise cql.ProgrammingError("Server did not accept registration"
                                           " for %s events: %s"
                                           % (eventtype, ans.summarymsg()))
            watchers = self.event_watchers.setdefault(eventtype, [])
        watchers.append(cb)

    def unregister_watcher(self, eventtype, cb):
        """
        Given an eventtype and a callback previously registered with
        register_watcher(), remove that callback from the list of watchers for
        the given event type.
        """

        if isinstance(eventtype, str):
            eventtype = eventtype.decode('utf8')
        self.event_watchers[eventtype].remove(cb)

    def wait_for_event(self):
        """
        Wait for any sort of event to arrive, and handle it via the
        registered callbacks. It is recommended that some event watchers
        be registered before calling this; otherwise, no events will be
        sent by the server.
        """
        eventsseen = []
        def i_saw_an_event(ev):
            eventsseen.append(ev)
        wlists = self.event_watchers.values()
        for wlist in wlists:
            wlist.append(i_saw_an_event)
        while not eventsseen:
            self.wait_for_result(None)
        for wlist in wlists:
            wlist.remove(i_saw_an_event)
