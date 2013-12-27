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

import re
from cql.apivalues import ProgrammingError
from cql.cqltypes import lookup_casstype

stringlit_re = re.compile(r"""('[^']*'|"[^"]*")""")
comments_re = re.compile(r'(/\*(?:[^*]|\*[^/])*\*/|//.*$|--.*$)', re.MULTILINE)
param_re = re.compile(r'''
    ( \W )            # don't match : at the beginning of the text (meaning it
                      # immediately follows a comment or string literal) or
                      # right after an identifier character
    : ( \w+ )
    (?= \W )          # and don't match a param that is immediately followed by
                      # a comment or string literal either
''', re.IGNORECASE | re.VERBOSE)

def replace_param_substitutions(query, replacer):
    split_strings = stringlit_re.split(' ' + query + ' ')
    split_str_and_cmt = []
    for p in split_strings:
        if p[:1] in '\'"':
            split_str_and_cmt.append(p)
        else:
            split_str_and_cmt.extend(comments_re.split(p))
    output = []
    for p in split_str_and_cmt:
        if p[:1] in '\'"' or p[:2] in ('--', '//', '/*'):
            output.append(p)
        else:
            output.append(param_re.sub(replacer, p))
    assert output[0][0] == ' ' and output[-1][-1] == ' '
    return ''.join(output)[1:-1]

class PreparedQuery(object):
    def __init__(self, querytext, itemid, vartypes, paramnames):
        self.querytext = querytext
        self.itemid = itemid
        self.vartypes = map(lookup_casstype, vartypes)
        self.paramnames = paramnames
        if len(self.vartypes) != len(self.paramnames):
            raise ProgrammingError("Length of variable types list is not the same"
                                   " length as the list of parameter names")

    def encode_params(self, params):
        return [t.to_binary(t.validate(params[n])) for (n, t) in zip(self.paramnames, self.vartypes)]

def prepare_inline(query, params, cql_major_version=3):
    """
    For every match of the form ":param_name", call cql_quote
    on kwargs['param_name'] and replace that section of the query
    with the result
    """

    def param_replacer(match):
        return match.group(1) + cql_quote(params[match.group(2)], cql_major_version)
    return replace_param_substitutions(query, param_replacer)

def prepare_query(querytext):
    paramnames = []
    def found_param(match):
        pre_param_text = match.group(1)
        paramname = match.group(2)
        paramnames.append(paramname)
        return pre_param_text + '?'
    transformed_query = replace_param_substitutions(querytext, found_param)
    return transformed_query, paramnames

def cql_quote(term, cql_major_version=3):
    if isinstance(term, unicode):
        return "'%s'" % __escape_quotes(term.encode('utf8'))
    elif isinstance(term, str):
        return "'%s'" % __escape_quotes(str(term))
    elif isinstance(term, bool) and cql_major_version == 2:
        return "'%s'" % str(term)
    else:
        return str(term)

def __escape_quotes(term):
    assert isinstance(term, basestring)
    return term.replace("'", "''")

def cql_quote_name(name):
    if isinstance(name, unicode):
        name = name.encode('utf8')
    return '"%s"' % name.replace('"', '""')
