"""Load the archived modules without native application startup."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
from lupa.lua53 import LuaRuntime
BASE=ROOT/'work/github-review-20261009/V3'
def load_runtime(base=BASE):
    rt=LuaRuntime(unpack_returned_tuples=True)
    order=json.loads((base/'source/order.json').read_text(encoding='utf-8'))
    code='\n'.join((base/p).read_text(encoding='utf-8') for p in order if p!='source/bootstrap.lua')
    rt.execute(code)
    return rt
def plain(v):
    if not hasattr(v,'items'):return v
    values=dict(v.items())
    if values and set(values)==set(range(1,len(values)+1)):
        return [plain(values[i]) for i in range(1,len(values)+1)]
    return {str(k):plain(x) for k,x in values.items()}
