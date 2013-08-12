from crawler.jsctx import get_ctx

def test_eval():
    ctx = get_ctx()
    assert 3 == ctx.eval("1+2")

def test_object():
    ctx = get_ctx()
    assert {'a': 1, 'b': 2} == dict(ctx.eval('d={a:1,b:2}'))
