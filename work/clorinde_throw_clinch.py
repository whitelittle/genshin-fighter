from clorinde_assets import O,extract,canonical_fit
from clorinde_pose_profiles import measure
from PIL import Image
import numpy as np,json,hashlib
data=json.loads((O/'actions.json').read_text(encoding='utf-8'));palette=json.loads((O/'palette.json').read_text())
def build(kind):
 name=f'source/throw-clinch-{kind}-v3.png';items,_=extract(O/name,4);out=[]
 for i,(im,info) in enumerate(items):
  # Complete, actual source bodies only. Border rejects remain in source archive.
  file=f'frames/throw-clinch-{kind}-v3-{i}.png';im.save(O/file);p=measure(im)
  a=np.asarray(im)[:,:,3];ys,xs=np.where(a>=128);floor=float(ys.max());s=.55 if kind=='adult' else .59
  hip=p.get('hip');anchor=[hip[0] if hip else im.width*.60,floor]
  source={'file':file,'source':name,'anchor':anchor,'scale':s,**info,'sourceHash':hashlib.sha256((O/file).read_bytes()).hexdigest(),
   'landmarkProposal':p,'anchorStatus':'grounded source-local hip and sole candidate; visual review',
   'calibrationStatus':'explicit uniform source unit; no X/Y deformation'}
  fit,_=canonical_fit(im,anchor,s,palette,f'throw-clinch-{kind}-v3-{i}');out.append((source,fit))
 return out
a=build('adult');low=build('low');d=data['throw']
def variant(items):
 sources=[data['idle']['sourceFrames'][0]]+[x[0] for x in items]+[data['idle']['sourceFrames'][0]]
 frames=[data['idle']['frames'][0]]+[x[1] for x in items]+[data['idle']['frames'][0]]
 return {'sourceFrames':sources,'frames':frames,'durations':[4,4,8,16,6,12],
  'phases':['收剑接近','接触','压低重心','贴身发力','向前释放','恢复'],
  'gripKind':'forearm and upper-arm clinch, not wrist suspension'}
adult=variant([a[1],a[1],a[2],a[3]])
child=variant([low[1],low[1],low[2],a[3]])
for key in ['sourceFrames','frames','durations','phases']:d[key]=adult[key]
data['victim']['durations']=adult['durations']
d['variants']={'raiden':adult,'nahida':child}
d['pairingProfiles']={
 'status':'source-local points for standalone preview; actual game contact/escape/wall tests pending',
 'captureTick':8,'releaseTick':32,'releaseTravel':170,'flightTicks':10,
 'raiden':{'casterGrip':[[0,0],[500,235],[500,235],[596,198],[588,172],[0,0]],'targetPoints':[[36,21],[35,28]],'targetPoses':['basic_0','victim_0','victim_0','victim_1','victim_3','victim_5']},
 'nahida':{'casterGrip':[[0,0],[559,275],[559,275],[655,260],[588,172],[0,0]],'targetPoints':[[38,24],[39,20]],'targetPoses':['basic_0','victim_0','victim_0','victim_1','victim_3','victim_5']}}
d['status']='贴身控制与前送候选；对手沿用既有素材，低位姿由克洛琳德自身下沉完成'
d['sourceRejectedForActive']={'adult':[0],'low':[0,3],'reason':'outer-boundary contact; intact alternatives selected; sources preserved'}
(O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print([(kind,i,im[0]['anchor'],im[0]['landmarkProposal'].get('hands')) for kind,ls in [('adult',a),('low',low)] for i,im in enumerate(ls)])
