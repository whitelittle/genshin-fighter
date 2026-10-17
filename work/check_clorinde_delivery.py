"""File, pixel, event and shared-pose audit, not art/simulator/device acceptance."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-actions-20261011'

def main():
 data=json.loads((O/'actions.json').read_text(encoding='utf-8'));assert len(data)==25
 effects=json.loads((O/'effects.json').read_text(encoding='utf-8'));assert len(effects)==6
 files=set();rectfiles=set();body_sources=set();body_fits=set();events=[]
 for key,d in data.items():
  n=len(d['frames']);assert n==len(d['sourceFrames'])==len(d['durations'])==len(d['phases'])
  assert all(isinstance(t,int) and t>0 for t in d['durations'])
  assert d['totalTicks']==sum(d['durations'])
  assert not d['runtimeIntegrated']
  for f in d['frames']:
   files.add(f['file']);rectfiles.add(f['rectData']);body_fits.add(f['file'])
  for f in d['sourceFrames']:
   files.add(f['file']);files.add(f['source']);body_sources.add(f['file']);assert len(f['anchor'])==2 and f['scale']>0
   assert not ('scaleX' in f or 'scaleY' in f)
  for model,v in d.get('variants',{}).items():
   assert model in ['raiden','nahida']
   assert len(v['frames'])==len(v['sourceFrames'])==len(v['durations'])==len(v['phases'])
   assert v['durations']==d['durations']
   for f in v['frames']:files.add(f['file']);rectfiles.add(f['rectData']);body_fits.add(f['file'])
   for f in v['sourceFrames']:files.add(f['file']);files.add(f['source']);body_sources.add(f['file'])
  ids=[]
  for e in d['events']:
   assert 0<=e['tick']<d['totalTicks'];events.append({'action':key,**e})
   if e.get('hitId'):ids.append(e['hitId'])
  assert len(ids)==len(set(ids))
 for key in ['forwarddash','backdash','victory']:
  for field in ['frames','sourceFrames']:
   assert data[key][field][0]==data['idle'][field][0]
   assert data[key][field][-1]==data['idle'][field][0]
 for field in ['frames','sourceFrames']:
  assert data['hit_knockdown'][field][-1]==data['wakeup'][field][0]
  assert data['wakeup'][field][-1]==data['idle'][field][0]
 assert data['Q']['shortBranch']['stage'] is False
 assert data['Q']['totalTicks']==162 and sum(data['Q']['shortBranch']['durations'])==24
 assert data['Q']['cinematic']['hitTicks']==[70,94,118]
 assert len(data['Q']['shortBranch']['events'])==1
 assert all(e.get('requires')=='confirmation hit' for e in data['Q']['events'][1:])
 assert data['throw']['pairing']['effectLayer'] is False
 assert data['victim']['pairing']['effectLayer'] is False
 assert data['throw']['durations']==data['victim']['durations']
 assert data['throw']['events'][1]['tick']==data['victim']['pairing']['releaseTick']==32
 for field in ['frames','sourceFrames']:
  assert data['victim'][field][4]==data['hit_knockdown'][field][-1]
  assert data['victim'][field][5]==data['wakeup'][field][1]
 models=json.loads((O/'opponent-models.json').read_text(encoding='utf-8'))
 baseline=R/'outputs/v4-one-character-20261010/baseline-actions'
 for model,poses in models.items():
  native='raidenshogun' if model=='raiden' else 'nahida'
  for p in poses.values():
   original=baseline/native/Path(p['file']).name
   assert original.exists()
   assert hashlib.sha256(original.read_bytes()).digest()==hashlib.sha256((O/p['file']).read_bytes()).digest()
   files.add(p['file'])
 for model,p in data['throw']['pairingProfiles'].items():
  if model not in models:continue
  v=data['throw']['variants'][model]
  for i in [1,2,3,4]:
   x,y=p['casterGrip'][i]
   assert Image.open(O/v['sourceFrames'][i]['file']).convert('RGBA').getpixel((x,y))[3]>180,(model,i,'caster contact outside alpha')
  for i,xy in enumerate(p['targetPoints']):
   assert Image.open(O/models[model]['victim_'+str(i)]['file']).convert('RGBA').getpixel(tuple(xy))[3]>180,(model,i,'opponent contact outside alpha')
 portrait=json.loads((O/'portrait-fit.json').read_text(encoding='utf-8'))
 files.add('portrait.png');files.add(portrait['file']);rectfiles.add(portrait['rectData'])
 for fx in effects.values():files.add(fx['source']['file']);files.add(fx['fit']['file']);rectfiles.add(fx['fit']['rectData'])
 stats=[]
 for name in sorted(files):
  p=O/name;assert p.exists(),name
  with Image.open(p) as im:im.verify()
 for name in sorted(rectfiles):
  d=json.loads((O/name).read_text(encoding='utf-8'));im=np.asarray(Image.open(O/d['file']).convert('RGBA'));out=np.zeros_like(im)
  total_area=0
  for x,y,w,h,c in d['rects']:
   assert w>0 and h>0 and x>=0 and y>=0 and x+w<=im.shape[1] and y+h<=im.shape[0]
   out[y:y+h,x:x+w]=d['palette'][c]+[255];total_area+=w*h
  assert np.array_equal(im,out),name
  visible=int((im[:,:,3]>0).sum())
  stats.append({'file':d['file'],'rectangles':len(d['rects']),'visibleLogicalPixels':visible,'paintedLogicalArea':total_area,'overlapAreaRatio':total_area/max(1,visible)})
 body=[s for s in stats if s['file'] in body_fits];fx=[s for s in stats if s['file'].startswith('fit/fx-')]
 peak_body=max(s['rectangles'] for s in body);peak_fx=max(s['rectangles'] for s in fx)
 lua_status='unavailable'
 try:
  sys.path.insert(0,str(R/'work/optimization-test-deps'))
  from lupa.lua53 import LuaRuntime
  lua=LuaRuntime(unpack_returned_tuples=True);module=lua.execute((O/'clorinde_animation_data.lua').read_text(encoding='utf-8'))
  assert len(list(module['actions'].keys()))==25
  assert module['actions']['Q']['shortBranch']['stage'] is False
  assert len(list(module['effects'].keys()))==6
  lua_status='Lua 5.3 data module load passed; not battle simulation'
 except ImportError:pass
 report={'actions':len(data),'displayPoses':sum(len(d['frames']) for d in data.values()),
  'uniqueActiveBodySourceFiles':len(body_sources),'uniqueActiveBodyFitFiles':len(body_fits),'effects':len(effects),
  'fileChecks':'passed','pixelRoundtrip':'passed for quantized outlined target','eventsAndSharedPoses':'passed',
  'lua':lua_status,'peakBodyRectangles':peak_body,'peakEffectRectangles':peak_fx,
  'bodyRectangleMean':sum(s['rectangles'] for s in body)/len(body),
  'proposedTwoActorTwoBodyBufferCapacity':4*peak_body,'proposedVisibleTwoBodyTwoEffectRectangles':2*peak_body+2*peak_fx,
  'frameMetrics':stats,'events':events,'sourceFileSizes':{name:(O/name).stat().st_size for name in sorted(files)},
  'worldScale':'provisional uniform source drawing units, not art acceptance','visualAcceptance':'not accepted',
  'battleRuntimeIntegrated':False,'simulator':'not run','device':'not observed','performanceAccepted':False}
 browser=O/'browser-verification.json'
 if browser.exists():report['browser']=json.loads(browser.read_text(encoding='utf-8'))
 (O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 recipe={'status':'plan only, no platform pool/load acceptance','common':['idle','walk','backwalk','jump','crouch','standguard','crouchguard','light1','light2','light3','hit_knockdown','wakeup'],
  'streamOnDemand':['E','Q','throw','victim','victory','defeat','heavy','crouchlight','crouchheavy','airlight','airheavy','forwarddash','backdash'],
  'cpuData':'store rectangles once per unique file; shared poses reuse same identity',
  'visibleBodies':2,'bodyBuffersPerActor':2,'sharedBodyRectCapacityEstimate':4*peak_body,
  'swap':'predecode; bounded property diffs to inactive buffer; commit atomically; preserve previous complete pose',
  'effects':'preallocate shared gun/bullet/impact/sword pools; no allocation per projectile',
  'diffDrawing':'required runtime work, not implemented by PNG canvas preview','platformControlsAndHiddenPool':'not measured',
  'overflow':'do not enable formal character until hard budget measured; never display partially written body'}
 (O/'load-recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding='utf-8')
 manifest={p.relative_to(O).as_posix():{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in O.rglob('*') if p.is_file() and p.name!='manifest.json'}
 (O/'manifest.json').write_text(json.dumps({'status':'complete candidate action coverage, not art/game acceptance','files':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({k:report[k] for k in ['actions','displayPoses','uniqueActiveBodySourceFiles','effects','fileChecks','pixelRoundtrip','lua','peakBodyRectangles','peakEffectRectangles']},ensure_ascii=False))

if __name__=='__main__':main()
