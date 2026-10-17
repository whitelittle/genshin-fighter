"""Optional lossless asset export: field width and immutable palette/payload sharing.

Editable artwork and ordinary build are untouched. No general-purpose decompressor.
"""
from pathlib import Path
import base64,hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'work/optimization-test-deps'))
from lupa.lua53 import LuaRuntime
from lz4_block import compress,decompress
TARGETS=['gf_animation_data','gf_inbetween_data','gf_furina_data','gf_ayaka_data','gf_clorinde_data','gf_arlecchino_data']

class Ref:
    def __init__(self,code):self.code=code

def literal(v):
    if isinstance(v,Ref):return v.code
    if isinstance(v,dict):return '{'+','.join('['+literal(k)+']='+literal(x) for k,x in v.items())+'}'
    if isinstance(v,list):return '{'+','.join(map(literal,v))+'}'
    if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
    if v is None:return 'nil'
    if isinstance(v,bool):return 'true' if v else 'false'
    return repr(v)

def python_table(v):
    if not hasattr(v,'items'):return v
    d={k:python_table(x) for k,x in v.items()}
    if d and set(d)==set(range(1,len(d)+1)):return [d[i] for i in range(1,len(d)+1)]
    return {k:d[k] for k in sorted(d,key=lambda k:(str(type(k)),str(k)))}

def compact_module(path,name,compressed=False):
    rt=LuaRuntime(unpack_returned_tuples=True);rt.execute('__loaders={};'+path.read_text(encoding='utf-8'))
    data=python_table(rt.globals().__loaders[name]())
    palettes=[];payloads=[];pal_ids={};payload_ids={}
    stats={'frames':0,'r8':0,'r16':0,'rectangles':0,'oldDecodedBytes':0,'newDecodedBytes':0,'paletteReferences':0,'payloadReferences':0,'compressedFrames':0}
    def intern(v,bank,ids,prefix):
        key=literal(v)
        if key not in ids:ids[key]=len(bank)+1;bank.append(v)
        return Ref(f'{prefix}[{ids[key]}]')
    def walk(v):
        if isinstance(v,list):
            for x in v:walk(x)
        if not isinstance(v,dict):return
        if isinstance(v.get('pal'),list):
            v['pal']=intern(v['pal'],palettes,pal_ids,'palettes');stats['paletteReferences']+=1
        if 'n' in v and ('d' in v or 'bytes' in v):
            n=v['n'];count=n*5
            if 'bytes' in v:
                values=v.pop('bytes');assert len(values)==count
            else:
                old=base64.b64decode(v['d']);assert count*2<=len(old)<=count*2+2
                assert not any(old[count*2:]);values=list(struct.unpack('<'+'H'*count,old[:count*2]))
            assert all(isinstance(x,int) and 0<=x<=65535 for x in values)
            width=1 if max(values,default=0)<=255 else 2
            raw=bytes(values) if width==1 else struct.pack('<'+'H'*count,*values)
            packed=raw+b'\0'*((-len(raw))%3)
            if compressed and width==1:
                planes=bytes(values[axis+5*i] for axis in range(5) for i in range(n))
                plane_packed=planes+b'\0'*((-len(planes))%3)
                z=compress(plane_packed);assert decompress(z)==plane_packed
                if len(z)+24<len(packed):
                    v['compression']='lz4';v['layout']='planes';v['zlen']=len(z);stats['compressedFrames']+=1
                    packed=z+b'\0'*((-len(z))%3)
            v['d']=intern(base64.b64encode(packed).decode(),payloads,payload_ids,'payloads')
            v['codec']='r8' if width==1 else 'r16'
            stats['frames']+=1;stats[v['codec']]+=1;stats['rectangles']+=n
            stats['oldDecodedBytes']+=count*2;stats['newDecodedBytes']+=len(raw);stats['payloadReferences']+=1
        for x in v.values():walk(x)
    walk(data)
    code=f"__loaders['{name}']=function()\nlocal palettes={literal(palettes)}\nlocal payloads={literal(payloads)}\nreturn {literal(data)} end\n"
    stats.update(oldModuleBytes=path.stat().st_size,newModuleBytes=len(code.encode()),uniquePalettes=len(palettes),uniquePayloads=len(payloads))
    return code.encode(),stats

def build_compact(out,compressed=False,legacy=False):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    order=json.loads((ROOT/'source/order.json').read_text(encoding='utf-8'));chunks=[];reports={}
    for rel in order:
        p=ROOT/rel;name=p.stem
        if name in (TARGETS if legacy else TARGETS[2:]):
            code,stats=compact_module(p,name,compressed);reports[name]=stats
        else:code=p.read_bytes()
        if rel=='source/prefix.lua':
            profile='LZ4压缩' if compressed else '紧凑编码'
            code=(f"GF_ASSET_PRELOAD_AT_START=true\nGF_ASSET_PROFILE='{profile}'\n".encode()+code)
        chunks.append(code)
    raw=b''.join(chunks);sha=hashlib.sha256(raw).hexdigest()
    (out/'genshin_fighter.lua').write_bytes(raw)
    manifest={'profile':'lz4-assets-v1' if compressed else 'compact-assets-v1','minified':False,'bytes':len(raw),'sha256':sha,'modules':reports,'ordinaryBytes':sum((ROOT/p).stat().st_size for p in order),'nativeDeviceTested':False,'preparationAtInitialLoading':True,'legacyNumericTablesRetained':not legacy}
    (out/'build.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2));return manifest
if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,default=ROOT/'dist-compact');ap.add_argument('--compressed',action='store_true');ap.add_argument('--legacy',action='store_true');a=ap.parse_args();build_compact(a.out,a.compressed,a.legacy)
