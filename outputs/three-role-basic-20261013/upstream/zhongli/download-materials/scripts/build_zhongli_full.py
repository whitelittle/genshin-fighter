"""Build all 25 Zhongli action groups; art candidates, not a game-runtime acceptance."""
from pathlib import Path
import json,sys,hashlib,shutil,re,io
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
from build_zhongli_delivery import LABELS,DURATIONS,PHASES,BOXES,fit,artlib
ROOT=Path(__file__).resolve().parents[1]; O=ROOT/'outputs/zhongli-design-20261011';F=O/'full-actions'
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def save(im,p):
 b=io.BytesIO();im.save(b,format="PNG");p.write_bytes(b.getvalue());Image.open(p).load()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
# Skull-to-chin projected lengths manually estimated against coordinate contact sheets.
# Projection estimates are recorded, never called biological measurements or user approval.
HEAD={'idle':[120,120],'walk':[60]*6,'backwalk':[65,65,65,65,65,65],'jump':[66,66,65,65,64,67],'forwarddash':[60,68,67,66,65,60],'backdash':[60,67,65,66,68,60],'crouch':[60,65,67,70,77,77],'standguard':[60,60,62,62,63,60],'crouchguard':[73,73,75,76,76,74],'light1':[61,61,48,51,55,120],'light2':[62,62,60,60,60,60],'light3':[55,48,60,60,60,60],'heavy':[60,60,52,55,55,60],'crouchlight':[67,62,61,62,63,64],'crouchheavy':[80,75,70,200,70,70],'airlight':[64,64,60,60,64,64],'airheavy':[66,67,64,65,65,65],'skillE':[63,65,60,60],'skillQ':[60]*6,'throw':[61]*6,'victim':[68,67,70,70,70,70],'hit_knockdown':[65,68,68,70,70,70],'wakeup':[70,70,65,70,68,60],'victory':[65]*6,'defeat':[86,86,90,87,86,87]}

def root(im,key,index):
 a=np.array(im);mask=a[:,:,3]>=128;y,x=np.where(mask)
 # Contact marker: choose one real support cluster, never empty space between boots.
 ground=int(y.max()); xs=np.where(mask[max(0,ground-3):ground+1].any(0))[0];clusters=np.split(xs,np.where(np.diff(xs)>8)[0]+1);clusters=[c for c in clusters if len(c)>2];c=max(clusters,key=len) if clusters else xs
 anchor=[float(np.median(c)),float(ground)]
 air=key in ('airlight','airheavy') or key=='jump' and 0<index<5 or key=='backdash' and index in (2,3) or key=='forwarddash' and index in (2,3) or key=='victim' and index in (1,2,3) or key=='hit_knockdown' and index in (2,3)
 if air:
  # Pelvis positions visually registered as normalized guides from each isolated crop.
  pelvis={'jump':[(.77,.65),(.65,.45),(.74,.53),(.66,.55),(.66,.55),(.75,.60)],'airlight':[(.61,.60)]*6,'airheavy':[(.61,.58)]*6,'forwarddash':[(.65,.52)]*6,'backdash':[(.67,.52)]*6,'victim':[(.5,.54)]*6,'hit_knockdown':[(.52,.5)]*6}[key][index]
  anchor=[im.width*pelvis[0],im.height*pelvis[1]]
 return anchor,'pelvis guide' if air else 'actual support pixels'

def main():
 reg=json.loads((F/'source-registrations.json').read_text());assert set(reg)==set(LABELS)
 rows=[];target=114*330/920
 for key,poses in reg.items():
  assert len(poses)==len(HEAD[key]),(key,len(poses))
  for i,p in enumerate(poses):
   im=Image.open(F/p['file']).convert('RGBA');assert min(im.size)>50,(key,i,im.size)
   p.update(id=f'{key}-{i}',index=i,scale=target/HEAD[key][i],headProjection=HEAD[key][i],headTarget=target)
   p['anchor'],p['rootKind']=root(im,key,i);p['image']=im;p['key']=key;rows.append(p)
 palette=artlib.build_palette([artlib.downscale(p['image'],p['scale']/4) for p in rows],20,seed=11)+[[40,29,27]]
 bank={};checks=[]
 for key,label in LABELS.items():
  original=[];initial=[];fitted=[];rr=[]
  for p in [r for r in rows if r['key']==key]:
   im=p['image'];i=p['index'];source={'file':p['file'],'anchor':p['anchor'],'scale':p['scale'],'source':p['source'],'roi':p['roi'],'rootKind':p['rootKind']};original.append(source)
   for mode,opt,dest in [('initial',False,initial),('optimized',True,fitted)]:
    out,rects=fit(im,p['scale'],palette,opt);fn=f'fitted/{key}-{i}-{mode}.png';save(out,F/fn);a=[v*p['scale']/4 for v in p['anchor']];dest.append({'file':fn,'anchor':a,'scale':4,'source':p['source'],'sourceFrame':p['file']})
    write(F/f'rects/{key}-{i}-{mode}.json',{'palette':palette,'width':out.width,'height':out.height,'rects':rects,'anchor':a,'scale':4,'sourceSHA256':sha(F/p['source']),'frameSHA256':sha(F/p['file']),'fittedSHA256':sha(F/fn)})
    if opt:rr.append(len(rects))
   checks.append({k:v for k,v in p.items() if k!='image'}|{'sourceSHA256':sha(F/p['source']),'frameSHA256':sha(F/p['file']),'fittedSHA256':sha(F/fitted[-1]['file']),'rectangles':rr[-1],'registration':'head projection manually estimated; support pixel cluster / airborne pelvis guide; no independent anatomy acceptance'})
  ds=[24,24] if key=='idle' else [7,7,12,10] if key=='skillE' else DURATIONS[key];ph=['吸气','呼气'] if key=='idle' else ['合掌蓄势','下压生成','保持','恢复'] if key=='skillE' else PHASES.get(key,['准备','出手','有效','随挥','回收','恢复'])
  data={'actionId':'zhongli_'+key,'frames':fitted,'initialFrames':initial,'sourceFrames':original,'durations':ds,'phases':ph,'events':[],'status':'全动作素材候选；正式战斗、模拟器、真机及用户验收未完成','previewOnly':True}
  if key in BOXES:
   start=sum(ds[:2]);active=sum(ds[2:4]) if key!='skillE' else ds[2]
   data['events']=[{'tick':start,'kind':{'skillE':'pillar-create','skillQ':'q-confirm','throw':'grab'}.get(key,'hit'),'hitId':f'zhongli_{key}_1','damageSegments':1}]
   data['combatDesign']={'startup':start,'active':active,'recovery':sum(ds)-start-active,'box':BOXES[key],'lunge':18 if key=='heavy' else 0,'level':'low' if key.startswith('crouch') else 'high' if key.startswith('air') else 'mid','damage':None,'hitstun':None,'pushback':None,'cancel':'命中/防御确认后候选取消，数值待正式战斗调参','invulnerability':0,'hurtbox':[-42,0,84,280],'movement':'地面支撑或浮空承接；展示位移独立','status':'design-only'}
  if key=='skillE':
   data['combatDesign'].update(startup=19,active=7,recovery=10,pillarLimit=1,passiveDamage=False,casterHitBeforeRelease='cancel',casterHitAfterRelease='pillar persists')
   data['events']=[{'tick':14,'kind':'pillar-create','damageSegments':0},{'tick':19,'kind':'pillar-create-hit','hitId':'zhongli_skillE_1','damageSegments':1}]
   data['bodyActionDurations']=data['durations'][:];data['bodyActionTicks']=36;data['neutralDisplayTailTicks']=58
   data['durations'][-1]+=58;data['phases'][-1]='恢复／岩脊存续与消散'
  if key=='skillQ':
   data['events'][0]['damageSegments']=0
   data['branches']={'hit':{'durations':[8,8,10,44,12,12],'damageSegments':1,'petrifyTicks':30,'cutin':[19,38],'meteorTick':44,'damageTick':52},'whiff':{'durations':ds,'damageSegments':0,'cinematic':False},'block':{'durations':ds,'damageSegments':0,'cinematic':False}}
   data['cinematic']={'hitTicks':[52],'portrait':'ultimate-portrait.png','portraitFit':'ultimate-portrait-fit.png'}
  if key=='throw':data['events']=[{'tick':5,'kind':'grab'},{'tick':5,'kind':'pair-lock'},{'tick':18,'kind':'release','hitId':'zhongli_throw_release','damageSegments':1},{'tick':31,'kind':'victim-land'},{'tick':38,'kind':'victim-down'}];data['pairing']={'victim':'被投','lockTicks':[5,18],'releaseTick':18,'landingTick':31,'wakeup':'起身','noFX':True,'escape':'起手可逃脱；倒地/空中/无敌不可再抓','status':'paired presentation, not combat simulation'}
  
  if key=='light1':
   for kind in ('frames','initialFrames','sourceFrames'):data[kind].append(data[kind][0])
   data['durations'].append(8);data['phases'].append('持枪归位')
   data['combatDesign']['recovery']+=8
  bank[label]=data
 # Reuse semantically identical boundary poses; preserve all alternative source frames in inventory.
 for label in ('前冲','后撤','胜利'):
  for kind in ('frames','initialFrames','sourceFrames'):
   bank[label][kind][0]=bank['待机'][kind][0];bank[label][kind][-1]=bank['待机'][kind][0]
 for kind in ('frames','initialFrames','sourceFrames'):
  bank['起身'][kind][0]=bank['受击与倒地'][kind][-1];bank['起身'][kind][-1]=bank['待机'][kind][0];bank['被投'][kind][-1]=bank['受击与倒地'][kind][-1]
 for key,label,n,cols in [('pillarFx','E · 地心',4,2),('meteorFx','Q · 天星',3,3)]:
  src=O/f'sources/{key}.png';shutil.copy(src,F/f'sources/{key}.png');sheet=Image.open(src).convert('RGBA');rowsn=2 if n==4 else 1;originals=[];fits=[]
  ims=[sheet.crop((i%cols*sheet.width//cols,i//cols*sheet.height//rowsn,(i%cols+1)*sheet.width//cols,(i//cols+1)*sheet.height//rowsn)) for i in range(n)]
  pal=artlib.build_palette([artlib.downscale(im,.16) for im in ims],16,seed=11)+[[46,31,20]]
  for i,im in enumerate(ims):
   fn=f'frames/{key}-{i}.png';save(im,F/fn);scale=.64 if n==4 else .7;anchor=[im.width*.5,im.height-1] if n==4 else [im.width*.5,im.height*.65];originals.append({'file':fn,'anchor':anchor,'scale':scale,'source':f'sources/{key}.png'})
   f,rects=fit(im,scale,pal,False);name=f'fitted/{key}-{i}.png';save(f,F/name);a=[v*scale/4 for v in anchor];fits.append({'file':name,'anchor':a,'scale':4,'source':f'sources/{key}.png'});write(F/f'rects/{key}-{i}.json',{'palette':pal,'width':f.width,'height':f.height,'rects':rects,'anchor':a,'scale':4,'sourceSHA256':sha(src),'fittedSHA256':sha(F/name)})
  bank[label]['effects']={'sourceFrames':originals,'frames':fits,'fitFrames':fits,'startTick':14 if n==4 else 44,'duration':80 if n==4 else 35,'worldOffset':[205,0],'followActor':False,'independent':True}
 src=ROOT/'assets/roster-v2/zhongli-official-head.png';shutil.copy(src,F/'ultimate-portrait.png');im=Image.open(src).convert('RGBA');pal=artlib.build_palette([im],20)+[[40,29,27]];p,rects=fit(im,.9,pal,True);save(p,F/'ultimate-portrait-fit.png');write(F/'rects/portrait.json',{'palette':pal,'width':p.width,'height':p.height,'rects':rects,'sourceSHA256':sha(src),'fittedSHA256':sha(F/'ultimate-portrait-fit.png')})
 write(F/'actions.json',bank);write(F/'pose-report.json',{'palette':palette,'poses':checks,'bodyRectangles':{'max':max(c['rectangles'] for c in checks),'mean':sum(c['rectangles'] for c in checks)/len(checks)},'pipeline':'premultiplied BOX / weighted OKLab / exact painter / 1 logical inner outline with pale-area protection','sourceCommit':'1c21eb57ffb1b8d88b41cbb743c46a34864849df','browserQA':'未执行，当前环境无受支持浏览器','runtime':'未接入','device':'未验收','anatomy':'projection estimates / root guides; no independent anatomical approval'})
 write(F/'action-cards.json',{k:{name:v for name,v in d.items() if name not in ('frames','initialFrames','sourceFrames')} for k,d in bank.items()})
 print(json.dumps({'groups':len(bank),'displayPoses':sum(len(d['frames']) for d in bank.values()),'uniqueBodyPoses':len(checks)},ensure_ascii=False))
if __name__=='__main__':main()
