"""Uncompressed lazy scalar fields; no LZ4/base64 or whole-roster decode."""
from pathlib import Path
import sys,json,struct,base64,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
from compact_assets import ROOT,TARGETS,Ref,literal,python_table,LuaRuntime

READ_FIELDS="""local function fields(s)
 local b={};local i=1
 while i<=#s do
  local v=s:byte(i);i=i+1
  if v>=192 then v=(v-192)*64+s:byte(i)-128;i=i+1 end
  b[#b+1]=v-32
 end
 return b
end
"""
def field_literal(values):
    assert max(values,default=0)<2016 and min(values,default=0)>=0
    # One scalar per Unicode codepoint; printable offset avoids NUL/control bytes.
    # This is field serialization, with no compressed stream or decompressor.
    text=''.join(chr(v+32) for v in values);level=0
    while ']'+('='*level)+']' in text:level+=1
    eq='='*level
    return '['+eq+'['+text+']'+eq+']'

def module(path,name):
    rt=LuaRuntime(unpack_returned_tuples=True);rt.execute('__loaders={};'+path.read_text(encoding='utf-8'))
    data=python_table(rt.globals().__loaders[name]());stats={'frames':0,'rectangles':0}
    palettes=[];paletteIds={};factories=[];factoryIds={}
    def walk(v):
        if isinstance(v,list):
            for x in v:walk(x)
        if not isinstance(v,dict):return
        if isinstance(v.get('pal'),list):
            signature=literal(v['pal'])
            if signature not in paletteIds:paletteIds[signature]=len(palettes)+1;palettes.append(v['pal'])
            v['pal']=Ref('palettes['+str(paletteIds[signature])+']')
        if 'n' in v and ('bytes' in v or 'd' in v):
            count=v['n']*5
            if 'bytes' in v:values=v.pop('bytes')
            else:
                raw=base64.b64decode(v.pop('d'));values=list(struct.unpack('<'+'H'*count,raw[:count*2]))
            assert len(values)==count
            signature=literal(values)
            if signature not in factoryIds:factoryIds[signature]=len(factories)+1;factories.append(Ref('function() return fields('+field_literal(values)+') end'))
            v['raw']=Ref('rectangles['+str(factoryIds[signature])+']');v['codec']='raw'
            stats['frames']+=1;stats['rectangles']+=v['n']
        for x in v.values():walk(x)
    walk(data)
    return (f"__loaders['{name}']=function()\n"+READ_FIELDS+'local palettes='+literal(palettes)+'\nlocal rectangles='+literal(factories)+'\nreturn '+literal(data)+' end\n').encode(),stats

def build(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);chunks=[];reports={}
    order=json.loads((ROOT/'source/order.json').read_text(encoding='utf-8'))
    for rel in order:
        p=ROOT/rel
        if p.stem in TARGETS:code,stats=module(p,p.stem);reports[p.stem]=stats
        else:code=p.read_bytes()
        if rel=='source/prefix.lua':code=b"GF_RAW_ASSET_TABLES=true\nGF_ASSET_PRELOAD_AT_START=false\nGF_ASSET_PROFILE='raw-literal-tables'\n"+code
        chunks.append(code)
    raw=b''.join(chunks);assert len(raw)<7500000,'raw client exceeds source size budget'
    manifest={'profile':'raw-scalar-fields','compressed':False,'fieldSerialization':'one scalar per printable UTF8 codepoint; lazy reading; no base64/LZ4','minified':False,'initialSixCharacterDecode':False,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'modules':reports,'nativeDeviceTested':False}
    (out/'genshin_fighter.lua').write_bytes(raw);(out/'build.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8');print(manifest)
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();build(a.out)
