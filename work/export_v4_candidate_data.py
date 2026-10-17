"""Pack checked candidate rectangles; test with the real V3 Lua5.3 decoder."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
sys.path.insert(0,str(ROOT/'work/github-review-20261009/game/tools'))
from lupa.lua53 import LuaRuntime
import artlib
from v4_candidate_policy import offline_export_eligible
R=ROOT/'work/v4-handoff-20261009-partial';V=R/'V4'
OUT=V/'data'/(sys.argv[1] if len(sys.argv)>1 else 'codex-candidates-20261009')
if OUT.exists() and any(OUT.iterdir()):
    raise SystemExit('Output snapshot already exists; choose a new version, do not overwrite verified history')
OUT.mkdir(parents=True,exist_ok=True)
overlay=json.loads((V/'design/CODEX_CURRENT_OVERLAY_20261009.json').read_text(encoding='utf-8'))
folders=[]
for e in overlay['entries']:
    selected=e.get('codex_preferred_candidate')
    if selected:
        candidate=next(r for r in e['codex_sources'] if r['source']==selected)
        if not offline_export_eligible(candidate):continue
        folders.append((e['actionId'],R/candidate['evidence_folder']))
for name in ['yaemiko-crouchheavy-fox-pink-v1','neuvillette-cane-prop-v1']:
    folder=V/'evidence/codex-batch-20261009'/name
    if (folder/'fit.json').exists():folders.append((name,folder))
utilfile=ROOT/'work/github-review-20261009/V3/source/modules/gf_util.lua'
rt=LuaRuntime(unpack_returned_tuples=True)
util=rt.execute('local __loaders={}\n'+utilfile.read_text(encoding='utf-8')+'\nreturn __loaders["gf_util"]()')
items=[];frames_total=0
for name,folder in folders:
    report=json.loads((folder/'fit.json').read_text(encoding='utf-8'))
    palette=report['palette'];frames=[]
    for i,f in enumerate(report['frames']):
        rects=f.get('bounded_rects',f['rects'])
        raw=artlib.pack_rects(rects);encoded=artlib.b64(raw)
        decoded=util.decodeAll(encoded)
        assert bytes(decoded[j] for j in range(1,len(raw)+1))==raw,name
        recovered=[tuple(decoded[j+k] for k in range(5)) for j in range(1,len(raw)+1,5)]
        image=Image.open(folder/f'fit-{i}.png').convert('RGBA')
        if not (folder/f'fit-{i}.png').exists():raise AssertionError('missing image')
        rebuilt=artlib.render(recovered,palette,*image.size)
        assert np.array_equal(np.asarray(rebuilt),np.asarray(image)),name
        frames.append({'n':len(rects),'w':image.width,'h':image.height,'data':encoded,
                       'palette':palette,'anchor':None,'anchor_status':'unmeasured_not_runtime_ready'})
        frames_total+=1
    items.append({'id':name,'frames':frames,'source_sha256':report['source_sha256'],
                  'runtime_ready':False,'accepted':False})
payload={'status':'candidate_data_only','codec':'V3 artlib.pack_rects uint8 xywhColor + artlib.b64 zero padding',
         'decoder_verified':'actual V3 gf_util under Lua5.3, every byte and reconstructed target pixel',
         'items':items,'frames':frames_total,'runtime_ready':False,
         'reason':'World root/grip/semantic acceptance missing; not a client script or game integration'}
(OUT/'candidate-data.json').write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def lua(v):
    if v is None:return 'nil'
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,(float,int)):return str(v)
    if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
    if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
    return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in v.items())+'}'
code='-- Candidate rectangles only. Missing world anchors; do not replace client Lua.\nreturn '+lua(payload)+'\n'
(OUT/'candidate-data.lua').write_text(code,encoding='utf-8')
module=rt.execute(code);assert module.runtime_ready is False and module.frames==frames_total
verification={'assets':len(items),'frames':frames_total,'lua_runtime':'lupa.lua53',
              'real_v3_decoder_sha256':hashlib.sha256(utilfile.read_bytes()).hexdigest(),
              'byte_decode_passed':True,'target_pixel_reconstruction_passed':True,
              'lua_module_load_passed':True,'runtime_ready':False,'game_integrated':False,
              'json_sha256':hashlib.sha256((OUT/'candidate-data.json').read_bytes()).hexdigest(),
              'lua_sha256':hashlib.sha256((OUT/'candidate-data.lua').read_bytes()).hexdigest()}
(OUT/'verification.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
print(json.dumps(verification,indent=2))
