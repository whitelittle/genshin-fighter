"""All uncompressed literal assets exactly match editable source banks."""
from pathlib import Path
import sys,json,base64,struct,hashlib,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from compact_assets import ROOT,TARGETS,LuaRuntime
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
raw=LuaRuntime(unpack_returned_tuples=True);raw.execute(a.source.read_text(encoding='utf-8'))
counts={'frames':0,'rectangles':0}
def table(v,count=False):
    if not hasattr(v,'items'):return v
    d=dict(v.items())
    if 'n' in d and ('d' in d or 'bytes' in d or 'raw' in d):
        n=int(d['n'])
        if 'd' in d:
            b=base64.b64decode(d.pop('d'));d['bytes']=list(struct.unpack('<'+'H'*(n*5),b[:n*10]))
        elif 'raw' in d:d['bytes']=d.pop('raw')();assert d.pop('codec')=='raw'
        if count:counts['frames']+=1;counts['rectangles']+=n
    d={k:table(x,count) for k,x in d.items()}
    if set(d)==set(range(1,len(d)+1)):return [d[i] for i in range(1,len(d)+1)]
    return d
order=json.loads((ROOT/'source/order.json').read_text())
for name in TARGETS:
    path=next(ROOT/p for p in order if Path(p).stem==name)
    old=LuaRuntime(unpack_returned_tuples=True);old.execute('__loaders={};'+path.read_text(encoding='utf-8'))
    assert table(old.globals().__loaders[name]())==table(raw.globals().GF_REQUIRE(name),True),name
assert raw.globals().GF_ASSET_PRELOAD_AT_START is False
assert raw.globals().GF_REQUIRE('gf_util').compressionStats.blocks==0
report={'sourceSha256':hashlib.sha256(a.source.read_bytes()).hexdigest(),**counts,'exactRawFieldsPalettesAnchorsAndMetadata':True,'initialSixCharacterDecode':False,'LZ4Blocks':0,'mockOnly':True}
a.out.write_text(json.dumps(report,indent=2),encoding='utf-8');print(report)
