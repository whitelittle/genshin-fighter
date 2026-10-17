from pathlib import Path
import json,hashlib,csv,sys,numpy as np
from PIL import Image
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';data=json.loads((o/'actions.json').read_text(encoding='utf-8'));fx=json.loads((o/'effects.json').read_text(encoding='utf-8'));portrait=json.loads((o/'portrait-fit.json').read_text(encoding='utf-8'));models=json.loads((o/'opponent-models.json').read_text(encoding='utf-8'));pairs=json.loads((o/'pairing-profiles.json').read_text(encoding='utf-8'));browser=json.loads((o/'browser-full-delivery.json').read_text(encoding='utf-8'))
assert len(data)==25;assert sum(len(a['frames']) for a in data.values())==138
assert sum(data['Q']['durations'])==162 and sum(data['Q']['shortBranch']['durations'])==24;assert data['Q']['cinematic']['hitTicks']==[70,94,118]
assert len(browser['allStates'])==276 and len(browser['pairs'])==48 and len(browser['qBranches'])==32 and len(browser['groundChains'])==8
assert all(s['ready'] for key in ['allStates','pairs','qBranches'] for s in browser[key]);assert not browser['consoleErrors']
for s in browser['qBranches']:
 if s['branch']!='hit':assert s['total']==24 and not s['fullStage']
for s in browser['pairs']:
 if s['contact']:
  assert sum((a-b)**2 for a,b in zip(s['contact']['caster'],s['contact']['target']))<1e-8;assert abs(s['foe']['root'][1]-550)<1e-6
for s in browser['groundChains']:assert s['before']['root']==s['after']['root'] and s['before']['frameFile']==s['after']['frameFile']
frames={};sourcefiles=set();body=[]
for key,main in data.items():
 for a in [main]+[{**main,**v} for v in main.get('variants',{}).values()]:
  assert len(a['sourceFrames'])==len(a['frames'])==len(a['durations'])==len(a['phases']);assert all(n>0 for n in a['durations'])
  for sf,ff in zip(a['sourceFrames'],a['frames']):
   im=np.array(Image.open(o/sf['file']).convert('RGBA'));raw=np.array(Image.open(o/sf['source']).convert('RGBA').crop(sf['roi']));mask=im[:,:,3]>0;assert np.array_equal(im[mask],raw[mask]);sourcefiles.add(sf['file']);frames[ff['file']]=json.loads((o/ff['rectData']).read_text(encoding='utf-8'));body.append(ff)
for f in [v['fit'] for v in fx.values()]+[portrait]:frames[f['file']]=json.loads((o/f['rectData']).read_text(encoding='utf-8'))
for file,meta in frames.items():
 im=np.array(Image.open(o/file).convert('RGBA'));rebuilt=np.zeros_like(im)
 for x,y,w,h,c in meta['rects']:rebuilt[y:y+h,x:x+w]=meta['palette'][c]+[255]
 assert np.array_equal(im,rebuilt),file
assert all(v['outerAlpha128Pixels']==0 for v in fx.values())
own=json.loads((o/'extraction-ownership-audit.json').read_text(encoding='utf-8'));assert own['status']=='passed'
for model,char in [('raiden','raidenshogun'),('nahida','nahida')]:
 base=r/'outputs/v4-one-character-20261010/baseline-actions';original=json.loads((base/'parameters.json').read_text(encoding='utf-8'))['characters'][char]['poses'];lookup={p['pose']:p for p in original if p['origin']=='keyframes'}
 for key,f in models[model].items():
  p=lookup[key];assert hashlib.sha256((o/f['file']).read_bytes()).hexdigest()==p['png_sha256'];assert [f['ax'],f['ay'],f['scale']]==[p['ax'],p['ay'],p['u']]
 for phase,pr in pairs[model].items():
  a={**data['throw'],**data['throw'].get('variants',{}).get(model,{})};sf=a['sourceFrames'][int(phase)];im=Image.open(o/sf['file']).convert('RGBA');assert im.getpixel(tuple(round(x) for x in pr['caster']))[3]>=180;im=Image.open(o/models[model][pr['targetKey']]['file']).convert('RGBA');assert im.getpixel(tuple(round(x) for x in pr['target']))[3]>=180
# Pure data export. Consumers use zero-based rectangle color + 1 for Lua palette.
def lua(v):
 if v is None:return 'nil'
 if isinstance(v,bool):return 'true' if v else 'false'
 if isinstance(v,(int,float)):return str(v)
 if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
 if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
 return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in v.items())+'}'
package={'character':'arlecchino','candidate':True,'actions':data,'frames':frames,'effects':fx,'portrait':portrait,'opponents':models,'pairing':pairs,'battleRuntimeIntegrated':False}
file=o/'arlecchino_animation_data.lua';file.write_text('-- Complete candidate data; not battle/platform acceptance.\nreturn '+lua(package),encoding='utf-8')
sys.path.insert(0,str(r/'work/optimization-test-deps'));from lupa.lua53 import LuaRuntime
module=LuaRuntime(unpack_returned_tuples=True).execute(file.read_text(encoding='utf-8'));assert module['character']=='arlecchino';assert len(list(module['actions'].keys()))==25
with (o/'frame-order.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['action','state','phase','ticks','source','source_unit','anchor_x','anchor_y','fit','rectangles']);
 for key,a in data.items():
  for i,(sf,ff,n,phase) in enumerate(zip(a['sourceFrames'],a['frames'],a['durations'],a['phases'])):w.writerow([key,i,phase,n,sf['file'],sf['scale'],*sf['anchor'],ff['file'],ff['rectangles']])
report={'actions':25,'mainDisplayStates':138,'uniqueBodySpritesIncludingVariants':len(sourcefiles),'effects':8,'portrait':'separate source/fit','opaqueOwnership':own,'sourceRGBA':'retained bytes equal original ROI','rectangles':'all actual body/FX/portrait targets reconstructed exactly','lua':'Lua5.3 data module loaded, not combat simulation','browser':{'mainStates':276,'QBranchStates':32,'pairedStates':48,'groundChainTransitions':8,'consoleErrors':0},'peakBodyRects':max(f['rectangles'] for f in body),'peakFXRects':max(v['fit']['rectangles'] for v in fx.values()),'opponentArtworkAndUnits':'original baseline hashes and units verified','candidate':True,'artUserAccepted':False,'battleRuntimeIntegrated':False,'simulator':'not run','device':'not observed','performanceAccepted':False}
(o/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');load={'status':'proposed, not platform pool acceptance','bodyBuffersPerActor':2,'twoOwnActorBodyCapacity':4*report['peakBodyRects'],'visibleTwoOwnBodiesTwoFX':2*report['peakBodyRects']+2*report['peakFXRects'],'bodyLoading':'current/next action only; deduplicate shared files','FXLoading':'shared pools, predecode and atomic swap','portrait':'separate palette/pool','unmeasured':'hidden controls, actual property updates, platform and device cost'};(o/'load-plan.json').write_text(json.dumps(load,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
