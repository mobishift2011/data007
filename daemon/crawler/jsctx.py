""" Using V8 to parse Javascript more efficienctly

Refer to ../scripts/setupenv.sh about how to install v8/pyv8 on Linux/Mac

Usage::

    >>> from jsctx import get_ctx
    >>> ctx = get_ctx()
    >>> ctx.eval("1+2")
    3

    >>> dict(ctx.eval("d={a:1,b:2}"))
    {'a': 1, 'b': 2}

"""
import sys

try:
    import PyV8
except:
    from pyv8 import PyV8
    if 'linux' in sys.platform:
        need_decode = True
    else:
        need_decode = False

def get_ctx():
    if not hasattr(get_ctx, 'ctx'):
        ctx = PyV8.JSContext()
        ctx.enter()
        get_ctx.ctx = ctx
    return get_ctx.ctx
