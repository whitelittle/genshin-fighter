"""Generate an isolated candidate client; never modify accepted V3."""
from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
from PIL import Image
from v3_runtime_harness import ROOT,BASE
sys.path.insert(0,str(ROOT/'work/github-review-20261009/game/tools'))
from fit_v4_prototype import scan_rects
import artlib
V=ROOT/'work/v4-handoff-20261009-partial/V4'
OUT=ROOT/'outputs/v4-one-character-20261010/ayaka-training-probe'
OUT.mkdir(parents=True,exist_ok=True)
SRC=OUT/'source';shutil.copytree(BASE/'source',SRC,dirs_exist_ok=True)
sources={
 'idle':V/'evidence/kamisatoayaka-idle-review',
 'walk':V/'evidence/kamisatoayaka-walk-review',
 **{name:V/'evidence/codex-batch-20261009'/file for name,file in {
 'back':'kamisatoayaka-backwalk-body-v1','crouch':'kamisatoayaka-crouch-body-v2',
 'jump':'kamisatoayaka-jump-body-v1','guard':'kamisatoayaka-standguard-body-v1',
 'hurt':'kamisatoayaka-hit_knockdown-body-v1','getup':'kamisatoayaka-wakeup-body-v1'}.items()}}
frames={};counts={};provenance=[]
idle=Image.open(sources['idle']/'optimized-0.png').convert('RGBA')
scale=335/(idle.getbbox()[3]-idle.getbbox()[1])
def frame(im,palette,u):
 a=np.asarray(im);idx=np.full(a.shape[:2],-1,dtype=np.int16)
 # Preserve fitted target colors, including the one-pixel colored outline.
 for ci,col in enumerate(palette):idx[(a[:,:,:3]==np.array(col[:3])).all(axis=2)&(a[:,:,3]>0)]=ci
 assert not ((a[:,:,3]>0)&(idx<0)).any(),'unmapped fitted color'
 rr=scan_rects(idx)
 # Draft support-band proxy is recorded and NOT a final calibrated world root.
 y,x=np.nonzero(a[:,:,3]>0);bottom=int(y.max())+1
 support=x[y>=bottom-3];ax=float(np.median(support)) if len(support) else im.width/2
 return {'n':len(rr),'d':artlib.b64(artlib.pack_rects(rr)),'pal':[c[:3]+[255] for c in palette],
         'ax':ax,'ay':bottom,'w':im.width,'h':im.height,'u':u}
for group,folder in sources.items():
 f=json.loads((folder/'fit.json').read_text(encoding='utf-8'));pal=f['palette']
 candidates=sorted(folder.glob('optimized-*.png')) if group in ['idle','walk'] else sorted(folder.glob('fit-*.png'))
 counts[group]=len(candidates)
 for n,p in enumerate(candidates):
  im=Image.open(p).convert('RGBA');frames[f'{group}_{n}']=frame(im,pal,scale)
  provenance.append({'pose':f'{group}_{n}','image':p.relative_to(ROOT).as_posix(),
                     'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'draft_anchor':{'ax':frames[f'{group}_{n}']['ax'],'ay':frames[f'{group}_{n}']['ay']},
                     'anchor_method':'lowest opaque support-band median; candidate diagnostic, requires manual body/foot calibration'})
portrait=idle.crop((0,0,idle.width,min(25,idle.height)))
canvas=Image.new('RGBA',(90,90));portrait.thumbnail((80,80),Image.Resampling.NEAREST)
canvas.alpha_composite(portrait,((90-portrait.width)//2,(90-portrait.height)//2))
frames['portrait']=frame(canvas,json.loads((sources['idle']/'fit.json').read_text(encoding='utf-8'))['palette'],1)
def lua(v):
 if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,(int,float)):return str(v)
 if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
 return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in v.items())+'}'
data={'frames':frames,'counts':counts,'body_peak':max(f['n'] for k,f in frames.items() if k!='portrait')}
(SRC/'modules/gf_candidate_ayaka_data.lua').write_text("__loaders['gf_candidate_ayaka_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
shutil.copyfile(ROOT/'work/v4_candidate_ayaka.lua',SRC/'modules/gf_candidate_ayaka.lua')
(SRC/'candidate-install.lua').write_text("\nGF_REQUIRE('gf_candidate_ayaka').install()\nGF_RELEASE_ID='V4-Ayaka-Training-Probe-20261010'\nGF_BUILD='candidate-ground-movement-only'\nGF_FIRST_SCENE='fight'\nGF_FIRST_ARGS={chars={'kamisatoayaka','raidenshogun'},mode='training',cpu={0,0},rounds=2,time=99,seed=21}\n",encoding='utf-8')
order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'));i=order.index('source/bootstrap.lua')
order[i:i]=['source/modules/gf_candidate_ayaka_data.lua','source/modules/gf_candidate_ayaka.lua','source/candidate-install.lua']
(SRC/'order.json').write_text(json.dumps(order,indent=2),encoding='utf-8')
client=b''.join((OUT/p).read_bytes() for p in order)
(OUT/'GF_V4_Ayaka_Training_Probe.lua').write_bytes(client)
report={'candidate':True,'game_bootstrap_bundled':True,'formal_integrated':False,'user_accepted':False,
        'scope':'movement/receive-hit training probe; attacks E Q throw dash disabled, missing animation states explicitly pending',
        'frames':len(frames)-1,'groups':counts,'body_peak_images':data['body_peak'],'double_body_images':data['body_peak']*2,
        'scale_design_units_per_pixel':scale,'anchors':'automatic draft, not final foot/grip calibration',
        'client_sha256':hashlib.sha256(client).hexdigest(),'provenance':provenance,
        'baseline_unchanged':all((SRC/Path(p).relative_to('source')).read_bytes()==(BASE/p).read_bytes() for p in json.loads((BASE/'source/order.json').read_text(encoding='utf-8')) if p!='source/prefix.lua'),
        'native_device_tested':False,'visual_semantic_accepted':False}
(OUT/'build-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='provenance'},ensure_ascii=False))
