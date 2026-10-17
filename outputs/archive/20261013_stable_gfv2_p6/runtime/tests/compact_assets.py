"""Exhaustive rectangle/metadata equality and staged preparation CPU comparison."""
from pathlib import Path
import base64,hashlib,json,struct,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT.parent/'work/optimization-test-deps'))
from compact_assets import python_table,TARGETS
from lz4_block import decompress
from lupa.lua53 import LuaRuntime

def load(path):
    rt=LuaRuntime(unpack_returned_tuples=True);rt.execute(path.read_text(encoding='utf-8'));return rt

import argparse
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=ROOT/'dist-compact/genshin_fighter.lua');ap.add_argument('--out',type=Path,default=ROOT/'verification/compact-assets.json');args=ap.parse_args()
normal=ROOT/'dist/genshin_fighter.lua';compact=args.source
a,b=load(normal),load(compact);counts={'frames':0,'rectangles':0}
def canonical(v):
    if isinstance(v,list):return [canonical(x) for x in v]
    if not isinstance(v,dict):return v
    v={k:canonical(x) for k,x in v.items()}
    if 'n' in v and ('d' in v or 'bytes' in v):
        count=v['n']*5
        if 'd' in v:
            raw=base64.b64decode(v.pop('d'));width=1 if v.get('codec')=='r8' else 2
            if v.get('compression')=='lz4':raw=decompress(raw[:v['zlen']])
            assert len(raw)>=count*width and not any(raw[count*width:])
            v['bytes']=list(raw[:count]) if width==1 else list(struct.unpack('<'+'H'*count,raw[:count*2]))
            if v.get('layout')=='planes':v['bytes']=[v['bytes'][axis*v['n']+i] for i in range(v['n']) for axis in range(5)]
        v.pop('codec',None)
        for key in ['compression','layout','zlen']:v.pop(key,None)
    return v
for name in TARGETS:
    old=canonical(python_table(a.globals().GF_REQUIRE(name)));new=canonical(python_table(b.globals().GF_REQUIRE(name)))
    assert old==new,name
    def count(v):
        if isinstance(v,dict):
            if 'n' in v and 'bytes' in v:counts['frames']+=1;counts['rectangles']+=v['n']
            for x in v.values():count(x)
        elif isinstance(v,list):
            for x in v:count(x)
    count(old)
# Shared payload must not share the mutable frame object (bake flags/anchors).
b.execute('''local d=GF_REQUIRE('gf_furina_data');local seen={};for _,img in pairs(d.frames)do assert(not seen[img]);seen[img]=true end''')
actual_frames=0
for key,name in [('raidenshogun','raiden'),('nahida','nahida')]:
    bank=a.globals().GF_REQUIRE('gf_animation_data')[name]['lo']
    extra=a.globals().GF_REQUIRE('gf_inbetween_data')['poses'][name]['lo']
    poses=[pose for group in [bank,extra] for pose,img in group.items() if hasattr(img,'items') and img['n']]
    for pose in poses:
        ia=a.globals().GF_REQUIRE('gf_art').animation(key,'lo',pose)
        ib=b.globals().GF_REQUIRE('gf_art').animation(key,'lo',pose)
        for field in ['n','ax','ay','u','w','h','seam','bytes','pal']:
            assert python_table(ia[field])==python_table(ib[field]),(key,pose,field)
        actual_frames+=1

def benchmark(path,key):
    rt=load(path)
    rt.execute('''instructions=0;debug.sethook(function()instructions=instructions+1000 end,'',1000)''')
    t=time.perf_counter();art=rt.globals().GF_REQUIRE('gf_art');job=art.prepare(key,'lo')
    setup_ms=(time.perf_counter()-t)*1000;setup_instr=rt.globals().instructions
    rt.globals().instructions=0;steps=0;peak=0;t=time.perf_counter()
    while True:
        before=rt.globals().instructions;done=job.step(job,9000);steps+=1
        peak=max(peak,rt.globals().instructions-before)
        if done:break
        assert steps<5000
    return {'prepareSteps':steps,'setupInstructions':setup_instr,'prepareInstructions':rt.globals().instructions,'peakStepInstructions':peak,'mockSetupMs':round(setup_ms,2),'mockPrepareMs':round((time.perf_counter()-t)*1000,2)}
benches={key:{'ordinary':benchmark(normal,key),'compact':benchmark(compact,key)} for key in ['raidenshogun','nahida','furina','kamisatoayaka','clorinde','arlecchino']}
report={'mockOnly':True,'nativeDeviceTested':False,'sourceSha256':hashlib.sha256(compact.read_bytes()).hexdigest(),'ordinarySha256':hashlib.sha256(normal.read_bytes()).hexdigest(),'exactDecodedRectanglesPalettesAndAllMetadata':True,'actualLegacyArtFramesEqual':actual_frames,'independentMutableFrames':True,**counts,'preparation':benches}
args.out.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
