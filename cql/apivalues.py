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

import exceptions


# dbapi Error hierarchy

class Warning(exceptions.StandardError): pass
class Error  (exceptions.StandardError):
    def __init__(self, msg, code=None):
        exceptions.StandardError.__init__(self, msg)
        self.code = code

class InterfaceError(Error): pass
class DatabaseError (Error): pass

class DataError        (DatabaseError): pass
class OperationalError (DatabaseError): pass
class IntegrityError   (DatabaseError): pass
class InternalError    (DatabaseError): pass
class ProgrammingError (DatabaseError): pass
class NotSupportedError(DatabaseError): pass
class NotAuthenticated (DatabaseError): pass


# Module constants

apilevel = 1.0
threadsafety = 1 # Threads may share the module, but not connections/cursors.
paramstyle = 'named'

# Module Type Objects and Constructors

Binary = buffer

try:
    from uuid import UUID  # new in Python 2.5
except ImportError:
    class UUID:
        def __init__(self, bytes):
            self.bytes = bytes

        def get_time(self):
            thisint = reduce(lambda a, b: a<<8 | b, map(ord, self.bytes), 0)
            return ((thisint >> 64 & 0x0fff) << 48 |
                    (thisint >> 80 & 0xffff) << 32 |
                    (thisint >> 96))
