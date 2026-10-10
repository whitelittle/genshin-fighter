"""Small explicit trial. Reject incompatible measurements BEFORE scale selection.

Manual projected landmarks are diagnostic estimates, not automated anatomy truth.
No per-axis transforms and no silhouette-height normalization.
"""
import json,math
from copy import deepcopy

LANDMARKS=[
 {'head':[[253,60],[268,129]],'torso':[[242,138],[245,275]],'legs':[[[242,280],[205,365],[168,439]],[[275,280],[298,359],[326,439]]]},
 {'head':[[245,68],[254,132]],'torso':[[225,143],[223,261]],'legs':[[[235,264],[264,337],[299,432]],[[212,267],[188,333],[151,417]]]},
 {'head':[[297,62],[307,125]],'torso':[[284,135],[252,241]],'legs':[[[232,244],[168,304],[92,374]],[[267,242],[329,302],[362,372]]]},
 {'head':[[285,58],[294,121]],'torso':[[278,133],[269,244]],'legs':[[[250,245],[186,319],[133,382]],[[291,248],[354,307],[391,382]]]},
 {'head':[[177,53],[183,112]],'torso':[[170,122],[157,248]],'legs':[[[143,251],[109,326],[79,403]],[[186,253],[214,328],[246,408]]]},
 {'head':[[206,54],[215,114]],'torso':[[201,123],[196,266]],'legs':[[[184,270],[150,345],[124,407]],[[221,270],[223,338],[231,407]]]}
]
NEW_RECOVERY={'head':[[621,179],[665,363]],'torso':[[604,383],[622,746]],
 'legs':[[[588,755],[511,970],[446,1167]],[[695,751],[679,962],[691,1171]]]}

def lengths(m):return [math.dist(*m['head']),math.dist(*m['torso'])]+[sum(math.dist(a,b) for a,b in zip(c,c[1:])) for c in m['legs']]
def evaluate(m,targets,scale):
 native=lengths(m);tolerances=[.06,.08,.12,.12]
 intervals=[(ref*(1-tol)/v,ref*(1+tol)/v) for v,ref,tol in zip(native,targets,tolerances)]
 lo=max(x[0] for x in intervals);hi=min(x[1] for x in intervals)
 weights=[3,3,1,1]
 best=math.exp(sum(w*math.log(ref/v) for v,ref,w in zip(native,targets,weights))/sum(weights)) if lo<=hi else None
 if best is not None:best=max(lo,min(hi,best))
 return {'nativeLengths':native,'beforeWorld':[v*scale for v in native],
   'beforeDeviation':[v*scale/ref-1 for v,ref in zip(native,targets)],
   'admissibleScaleInterval':[lo,hi],'compatible':lo<=hi,'candidateScale':best,
   'afterDeviation':None if best is None else [v*best/ref-1 for v,ref in zip(native,targets)],
   'confidence':'manual projected landmarks; foreshortening/occlusion require visual review, not art acceptance'}

def apply(data,folder,fit,palette):
 cfg=json.loads((folder.parents[1]/'work/furina_scale_registration.json').read_text(encoding='utf-8'))
 mother=data['待机']['sourceFrames'][0];scale=mother['scale'];m=cfg['actions']['待机'][0]
 targets=[math.dist(*m['head'])*scale,math.dist(*m['torso'])*scale]+[sum(math.dist(a,b) for a,b in zip(c,c[1:]))*scale for c in cfg['motherLegs']]
 d=data['轻攻三'];before=deepcopy(d)
 rows=[evaluate(m,targets,f['scale']) for m,f in zip(LANDMARKS,d['sourceFrames'])]
 trial=evaluate(NEW_RECOVERY,targets,.25)
 report={'targets':targets,'segmentOrder':['skull-to-chin','neck-to-pelvis','left hip-knee-ankle','right hip-knee-ankle'],
  'tolerances':[.06,.08,.12,.12],'before':before,'measurements':rows,'newRecovery':trial,
  'policy':'intersect all segment tolerance intervals first; no compatible interval means no scaling fix; then weighted log estimate within intersection; never fit by bbox',
  'changedFrames':[],'visualAcceptance':False,'runtimeIntegrated':False}
 # Do not mechanically calibrate the bent/occluded intermediate poses.
 for i,m in [(4,LANDMARKS[4]),(5,NEW_RECOVERY)]:
  row=rows[i] if i==4 else trial
  assert row['compatible'],f'No safe uniform-scale trial for frame {i}'
  f=deepcopy(d['sourceFrames'][i]);f['scale']=row['candidateScale']
  if i==5:f.update(file='light3-recovery-source-v2.png',source='light3-recovery-source-v2.png',anchor=[600,1390],supportPoint=[443,1390]);f.pop('roi',None)
  # Retain an anatomical hip offset instead of aligning hair or weapon envelope.
  f['anchor'][0]=m['torso'][1][0]-33.66/f['scale']
  f['proportionTrial']={'landmarks':m,'segmentDeviation':row['afterDeviation'],'visualAcceptance':False}
  d['sourceFrames'][i]=f;d['frames'][i],_=fit(f,list(palette),f'latest-light3-consistency-{i}.png')
  report['changedFrames'].append(i)
 d['status']='轻攻三试修：回收倍率多段约束；恢复姿单张返修。中段投影/比例待复核，非整组验收'
 report['after']=deepcopy(d)
 (folder/'light3-consistency-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 return {'changedFrames':[4,5],'generatedRecovery':'light3-recovery-source-v2.png','visualAcceptance':False}
