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

from cql.apivalues import *
from cql.connection import connect
from cql import cqltypes


class DBAPITypeObject:

    def __init__(self, *values):
        self.values = list(values) + [t.cass_parameterized_type(full=True) for t in values]

    def __cmp__(self,other):
        if other in self.values:
            return 0
        if other < self.values:
            return 1
        else:
            return -1

STRING = DBAPITypeObject(cqltypes.BytesType, cqltypes.AsciiType, cqltypes.UTF8Type)

BINARY = DBAPITypeObject(cqltypes.BytesType, cqltypes.UUIDType)

NUMBER = DBAPITypeObject(cqltypes.LongType, cqltypes.IntegerType, cqltypes.DecimalType,
                         cqltypes.FloatType, cqltypes.DoubleType, cqltypes.Int32Type,
                         cqltypes.CounterColumnType)

DATETIME = DBAPITypeObject(cqltypes.TimeUUIDType, cqltypes.DateType)

# just include all of them
ROWID = DBAPITypeObject(*cqltypes._cqltypes.values())
