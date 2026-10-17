"""Proposed event data and standalone action player packaging. Not a game patch."""
from pathlib import Path
import json,shutil,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-actions-20261011'

def main():
 data=json.loads((O/'actions.json').read_text(encoding='utf-8'))
 phase_labels={
  'walk':['左脚接触','下降','通过','右脚接触','下降','通过'],
  'backwalk':['探步','承重','收脚','蹬退','换脚','收稳'],
  'jump':['预蹲','蹬地','上升','顶点','下降','落地'],
  'forwarddash':['待机','蓄脚','蹬地','前移','制动','待机'],
  'backdash':['待机','蓄脚','蹬退','腾空','落脚','待机'],
  'crouch':['屈膝','下沉','低姿','保持'],
  'standguard':['进入','保持','承压','恢复'],'crouchguard':['进入','保持','承压','回蹲'],
  'light2':['撤剑','入鞘','拔枪','射击','后坐','入套'],
  'light3':['握柄','拔刀','斩击','随挥','制动','恢复'],
  'heavy':['收剑','蓄势','瞄准','射击','后坐','恢复'],
  'crouchlight':['准备','蓄势','低刺','随刺','撤回','蹲姿'],
  'crouchheavy':['蓄势','转髋','低扫','随扫','制动','蹲姿'],
  'airlight':['收剑','拔枪','射击','后坐','入套','下降'],
  'airheavy':['举剑','蓄势','下刺','随刺','回收','落地'],
  'E':['拔枪','瞄准','枪后坐','换剑','突刺','制动'],
  'Q':['瞄准确认','确认后坐','头像切入','蓄势','释放','持续冲击一','持续冲击二','持续冲击三','收束','恢复待机'],
  'throw':['收剑接近','接触','压低重心','贴身发力','向前释放','恢复'],
  'victim':['被抓','牵引','失衡','腾空','落地','侧撑'],
  'hit_knockdown':['受击','后仰','失衡','倒地'],
  'wakeup':['侧撑','收膝','单膝','站稳','待机'],
  'victory':['待机','收剑','致意','触帽','收势','待机'],
  'defeat':['失力','跪落','低头','停留']}
 attacks={'light1':(6,3,24,'mid'),'light2':(11,2,18,'mid'),'light3':(9,4,32,'mid'),
  'heavy':(16,4,38,'mid'),'crouchlight':(6,3,20,'low'),'crouchheavy':(12,4,34,'low'),
  'airlight':(7,2,18,'high'),'airheavy':(10,4,36,'high')}
 for key,d in data.items():
  if key in phase_labels:d['phases']=phase_labels[key]
  total=sum(d['durations']);d['totalTicks']=total;d['combatDesign']={'status':'proposed_not_runtime','damage':None,
   'hitstun':None,'blockstun':None,'knockback':None,'invulnerable':False,'boxes':'manual tuning required, not derived from image alpha',
   'cancel':'confirmed hit/block only; exact windows require combat integration',
   'branches':['whiff recovery','block recovery','hit confirmation','interrupt cancels unissued events']}
  if key in attacks:
   start,active,damage,level=attacks[key]
   d['combatDesign'].update(startup=start,active=active,recovery=total-start-active,attackLevel=level,damage=damage)
   d['events']=[{'tick':start,'kind':'shot' if key in ['light2','heavy','airlight'] else 'slash',
     'hitId':'clorinde.'+key+'.1','damageSegments':1}]
  elif key=='E':
   d['events']=[{'tick':8,'kind':'shot','hitId':'clorinde.E.gun','damageSegments':1},
    {'tick':18,'kind':'thrust','hitId':'clorinde.E.sword','damageSegments':1,'collision':'swept, direction fixed'}]
   d['combatDesign'].update(startup=8,activeWindows=[[8,10],[18,22]],recovery=18)
  elif key=='Q':
   d['events']=[{'tick':6,'kind':'confirm-shot','hitId':'clorinde.Q.confirm','damageSegments':1}]+[
    {'tick':t,'kind':'cinematic-slash','hitId':f'clorinde.Q.{i+1}','damageSegments':1,'requires':'confirmation hit'} for i,t in enumerate([70,94,118])]
   d['combatDesign']['branches']=['whiff: no full stage','block: no full stage','confirmed hit: three sword interceptions','interrupt before confirmation: cancel']
   d['shortBranch']={'indices':[0,1,len(d['frames'])-1],'durations':[6,6,12],'events':[d['events'][0]],'stage':False}
  elif key=='throw':
   d['events']=[{'tick':8,'kind':'grab','requires':'grounded target in range','escapeWindow':'proposed tick8-12'},
    {'tick':32,'kind':'release','hitId':'clorinde.throw.release','damageSegments':1}]
   d['pairing']={'clock':'shared 60Hz ticks, not picture index','lockContactUntil':32,'effectLayer':False,
    'wallAndBodySizes':'requires runtime/manual contact validation','victimAction':'victim','method':'grounded forearm/upper-arm clinch and forward release; caster low variant for petite targets'}
  elif key=='victim':d['pairing']={'clock':'same throw clock','releaseTick':32,'nextAction':'wakeup','effectLayer':False}
  if key=='walk':d['motion']={'kind':'walk','direction':1,'distance':90,'worldAndPoseSeparate':True}
  if key=='backwalk':d['motion']={'kind':'walk','direction':-1,'distance':75,'worldAndPoseSeparate':True}
  if key=='jump':d['motion']={'kind':'jump','height':155,'worldAndPoseSeparate':True}
  if key in ['forwarddash','backdash']:d['motion']={'kind':'dash','distance':150 if key=='forwarddash' else -125,'worldAndPoseSeparate':True}
  if key in ['airlight','airheavy']:d['motion']={'kind':'air','height':155,'inheritsJumpProgress':True,'worldAndPoseSeparate':True}
 foe_dir=O/'opponent';foe_dir.mkdir(exist_ok=True)
 ref=R/'outputs/v4-one-character-20261010/ayaka-armed-v2'
 foe=json.loads((ref/'foe-fitted.json').read_text(encoding='utf-8'))
 for v in foe.values():
  shutil.copy2(ref/v['file'],foe_dir/v['file']);v['file']='opponent/'+v['file']
 (O/'opponent.json').write_text(json.dumps(foe,ensure_ascii=False,indent=2),encoding='utf-8')
 models={}
 baseline=R/'outputs/v4-one-character-20261010/baseline-actions'
 params=json.loads((baseline/'parameters.json').read_text(encoding='utf-8'))
 for model,character in [('raiden','raidenshogun'),('nahida','nahida')]:
  poses={}
  for p in params['characters'][character]['poses']:
   if p['origin']!='keyframes' or not p['pose'].startswith(('basic_','hurt_','victim_','throw_')):continue
   target=foe_dir/model/Path(p['file']).name;target.parent.mkdir(exist_ok=True)
   shutil.copy2(baseline/p['file'],target)
   poses[p['pose']]={'file':target.relative_to(O).as_posix(),'ax':p['ax'],'ay':p['ay'],'scale':p['u'],
    'nativeUnitRetained':True,'width':p['w'],'height':p['h'],'contactStatus':'manual source-local attachment candidate'}
  models[model]=poses
 (O/'opponent-models.json').write_text(json.dumps(models,ensure_ascii=False,indent=2),encoding='utf-8')
 portrait=R/'assets/roster-v2/clorinde-official-head.png'
 if portrait.exists():shutil.copy2(portrait,O/'portrait.png')
 else:
  alternate=R/'work/github-review-20261009/assets/roster-v2/clorinde-official-head.png'
  if alternate.exists():shutil.copy2(alternate,O/'portrait.png')
 (O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 version=hashlib.sha256((O/'actions.json').read_bytes()).hexdigest()[:12]
 (O/'action-data.js').write_text('window.CLORINDE_VERSION='+json.dumps(version)+';\nwindow.CLORINDE_ACTIONS='+json.dumps(data,ensure_ascii=False)+';\nwindow.CLORINDE_OPPONENT='+json.dumps(foe,ensure_ascii=False)+';\nwindow.CLORINDE_OPPONENT_MODELS='+json.dumps(models,ensure_ascii=False)+';',encoding='utf-8')
 # Data-only Lua module: no attempt to claim actual combat integration.
 def lua(v):
  if v is None:return 'nil'
  if isinstance(v,bool):return 'true' if v else 'false'
  if isinstance(v,(int,float)):return str(v)
  if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
  if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
  return '{'+','.join('['+lua(k)+']='+lua(val) for k,val in v.items())+'}'
 frames={}
 for key,d in data.items():
  for f in d['frames']:
   frames[f['file']]=json.loads((O/f['rectData']).read_text(encoding='utf-8'))
  for variant in d.get('variants',{}).values():
   for f in variant['frames']:frames[f['file']]=json.loads((O/f['rectData']).read_text(encoding='utf-8'))
 effects=json.loads((O/'effects.json').read_text(encoding='utf-8')) if (O/'effects.json').exists() else {}
 for f in effects.values():frames[f['fit']['file']]=json.loads((O/f['fit']['rectData']).read_text(encoding='utf-8'))
 portraitFit=json.loads((O/'portrait-fit.json').read_text(encoding='utf-8')) if (O/'portrait-fit.json').exists() else None
 if portraitFit:frames[portraitFit['file']]=json.loads((O/portraitFit['rectData']).read_text(encoding='utf-8'))
 (O/'clorinde_animation_data.lua').write_text('-- Candidate animation data only; proposed events, no combat acceptance.\nreturn '+lua({'actions':data,'frames':frames,'effects':effects,'portrait':{'source':'portrait.png','fit':portraitFit}}),encoding='utf-8')
 print(json.dumps({'actions':len(data),'poses':sum(len(d['frames']) for d in data.values()),'runtimeIntegrated':False},ensure_ascii=False))

if __name__=='__main__':main()
