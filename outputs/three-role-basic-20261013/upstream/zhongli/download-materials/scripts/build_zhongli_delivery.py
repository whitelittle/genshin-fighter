"""Zhongli candidate art delivery. Uses repository artlib; no runtime combat mutation."""
from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/zhongli-design-20261011'
sys.path.insert(0,str(ROOT/'game/tools'))
import artlib

LABELS=dict(idle='待机',walk='前走',backwalk='后退',jump='跳跃',forwarddash='前冲',backdash='后撤',crouch='蹲下',standguard='站立格挡',crouchguard='蹲防',light1='轻攻一',light2='轻攻二',light3='轻攻三',heavy='站重',crouchlight='蹲轻',crouchheavy='蹲重',airlight='空轻',airheavy='空重',skillE='E · 地心',skillQ='Q · 天星',throw='投技',victim='被投',hit_knockdown='受击与倒地',wakeup='起身',victory='胜利',defeat='败北')
DURATIONS={'idle':[12]*6,'walk':[6]*6,'backwalk':[7]*6,'jump':[6,7,9,8,7,7],'forwarddash':[3,3,4,4,5,5],'backdash':[3,3,4,4,5,5],'crouch':[3]*6,'standguard':[4,4,10,5,5,5],'crouchguard':[4,4,10,5,5,5],'light1':[3,3,2,2,5,6],'light2':[4,4,3,2,6,7],'light3':[5,5,3,3,7,9],'heavy':[6,7,3,3,10,12],'crouchlight':[3,3,2,2,5,6],'crouchheavy':[6,6,3,3,10,12],'airlight':[3,3,3,3,5,5],'airheavy':[5,5,3,3,7,8],'skillE':[7,7,3,4,12,10],'skillQ':[8,8,3,4,12,12],'throw':[5,7,6,5,8,8],'victim':[5,7,6,5,8,8],'hit_knockdown':[5,5,7,8,9,14],'wakeup':[10,7,7,8,8,6],'victory':[12,10,12,14,10,12],'defeat':[10,10,12,12,12,24]}
PHASES={'idle':['吸气起','胸肩上提','吸气顶','呼气','胸肩回落','循环归位'],'walk':['右脚接地','右承重','左过腿','左脚接地','左承重','右过腿'],'backwalk':['右脚后触','后移承重','左脚后过','左脚后触','后移承重','右脚后过'],'jump':['蓄力','起跳','上升','顶点','下降','落地'],'forwarddash':['待机','启动','推进','跨步','制动','待机'],'backdash':['待机','退重心','蹬地','后跃','落地','待机'],'crouch':['站立','屈膝','降重心','蹲入','蹲稳','保持'],'standguard':['准备','架手','防御','受力','保持','恢复'],'crouchguard':['低姿','架手','防御','受力','保持','恢复'],'throw':['抓取','锁腕','牵引','掌推释放','随挥','恢复'],'victim':['抓取','锁腕','牵引','释放','落地','倒地'],'hit_knockdown':['站受击','后仰','空受击','下落','落地','倒地'],'wakeup':['倒地','撑肘','坐起','跪撑','起身','待机'],'victory':['待机','整衣','抬头','收手','归位','待机'],'defeat':['低头','失衡','单膝','双膝','支撑','败北']}
BOXES={'light1':[40,160,250,55],'light2':[35,130,245,90],'light3':[25,60,235,180],'heavy':[50,135,300,85],'crouchlight':[30,30,200,60],'crouchheavy':[20,0,270,65],'airlight':[25,-15,240,70],'airheavy':[15,-170,200,185],'skillE':[165,0,95,290],'skillQ':[50,20,220,180],'throw':[25,80,100,180]}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def extract(path,count):
 im=Image.open(path).convert('RGBA'); a=np.asarray(im); labels,n=ndimage.label(a[:,:,3]>=64)
 sizes=np.bincount(labels.ravel()); ids=sorted(range(1,n+1),key=lambda i:sizes[i],reverse=True)[:count]
 if len(ids)!=count or min(sizes[i] for i in ids)<1000:raise ValueError(f'{path}: {count} substantial poses required')
 records=[]
 for ident in ids:
  ys,xs=np.where(labels==ident); roi=[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
  crop=im.crop(roi); arr=np.array(crop); arr[:,:,3]=np.where(labels[roi[1]:roi[3],roi[0]:roi[2]]==ident,arr[:,:,3],0)
  records.append({'roi':roi,'image':Image.fromarray(arr),'center':[float(np.median(xs)),float(np.median(ys))],'touchesSheetEdge':bool(roi[0]==0 or roi[1]==0 or roi[2]==im.width or roi[3]==im.height)})
 records.sort(key=lambda r:(int(r['center'][1]//(im.height/2)) if count in (4,6) else 0,r['center'][0]))
 return records

def anchor_guess(im,air=False):
 # Provisional actual support pixels, not crop centre. Manual registrations override this.
 a=np.array(im); mask=a[:,:,3]>=128; ys,xs=np.where(mask)
 if air:return [float(np.median(xs)),im.height*.56]
 dark=(a[:,:,0]<160)&(a[:,:,1]<135)&(a[:,:,2]<125)&mask
 yy,xx=np.where(dark); bottom=int(yy.max()); footx=xx[yy>=bottom-5]
 return [float(np.median(footx)),float(bottom)]

def fit(im,scale,palette,optimized=True):
 small=artlib.downscale(im,scale/4); idx=artlib.apply_palette(small,palette)
 if optimized:
  opaque=idx>=0; inner=opaque&~ndimage.binary_erosion(opaque,structure=np.ones((3,3)),border_value=0)
  # Keep bright face, silver and pale fabric; edge applies only to darker silhouette pixels.
  rgb=np.asarray(small)[:,:,:3]; bright=(rgb.max(2)>210)&(rgb.min(2)>130)
  idx[inner&~bright]=len(palette)-1
 rects=artlib.painter(idx); out=artlib.render(rects,palette,small.width,small.height)
 rebuilt=np.full(idx.shape,-1,dtype=int)
 for x,y,w,h,c in rects:rebuilt[y:y+h,x:x+w]=c
 if not np.array_equal(idx,rebuilt):raise AssertionError('painter reconstruction mismatch')
 return out,rects

def main():
 regpath=OUT/'landmarks.json'; reg=json.loads(regpath.read_text()) if regpath.exists() else {}
 adoption=json.loads((OUT/'素材复用登记.json').read_text())
 prepared={}; body=[]
 for key in LABELS:
  src=OUT/f'sources/{key}.png'
  if not src.exists():raise FileNotFoundError(src)
  if key in ('idle','walk'):
   records=[]
   for file in adoption[key]['sourceFrames']:
    im=Image.open(OUT/file).convert('RGBA');records.append({'roi':[0,0,im.width,im.height],'image':im,'center':[im.width/2,im.height/2],'touchesSheetEdge':True,'existingFile':file})
  else:records=extract(src,4 if key=='skillE' else 6)
  prepared[key]=records
  body.extend(artlib.downscale(r['image'],.12) for r in records)
 palette=artlib.build_palette(body,20,seed=11)+[[40,29,27]]
 bank={}; report={'sourceCommit':'1c21eb57ffb1b8d88b41cbb743c46a34864849df','palette':palette,'pipeline':'game/tools/artlib.py: premultiplied BOX / weighted OKLab / painter','actions':{},'runtime':'not integrated','device':'not observed','anatomy':'manual/provisional registrations; does not claim approval'}
 for key,label in LABELS.items():
  records=prepared[key]; section=reg.get(key,{}); scale=section.get('scale',.48 if key=='idle' else .68); src=OUT/f'sources/{key}.png'; original=[]; fitted=[]; counts=[]; registration=[]
  for i,r in enumerate(records):
   im=r['image']; name=f'frames/{key}-{i}.png'; im.save(OUT/name)
   mark=section.get('poses',[])[i] if i<len(section.get('poses',[])) else {}
   anchor=mark.get('anchor',anchor_guess(im,key in ('airlight','airheavy') or (key=='jump' and i in (1,2,3,4))))
   original.append({'file':name,'anchor':anchor,'scale':scale,'roi':r['roi'],'source':f'sources/{key}.png','rootKind':'pelvis' if key in ('airlight','airheavy') or (key=='jump' and i in (1,2,3,4)) else 'support','landmarks':mark,'registrationStatus':mark.get('status','provisional support detection')})
   initial,_=fit(im,scale,palette,False); initial.save(OUT/f'fitted/{key}-{i}-initial.png')
   optimized,rects=fit(im,scale,palette,True); f=f'fitted/{key}-{i}.png'; optimized.save(OUT/f)
   fa=[v*scale/4 for v in anchor]; fitted.append({'file':f,'anchor':fa,'scale':4,'source':f'sources/{key}.png','sourceFrame':name})
   write(OUT/f'rects/{key}-{i}.json',{'palette':palette,'width':optimized.width,'height':optimized.height,'rects':rects,'anchor':fa,'scale':4,'sourceROI':r['roi'],'sourceSHA256':sha(src),'sourceFrameSHA256':sha(OUT/name),'fittedSHA256':sha(OUT/f),'optimizedOutline':'one logical inner pixel, light-area protected','previewOnly':True})
   counts.append(len(rects)); registration.append({'roi':r['roi'],'scale':scale,'anchor':anchor,'landmarks':mark,'edge':r['touchesSheetEdge']})
  durations=[24,24] if key=='idle' else [7,7,12,10] if key=='skillE' else DURATIONS[key]; phaseList=['吸气','呼气'] if key=='idle' else ['蓄势','下压生成','保持','恢复'] if key=='skillE' else PHASES.get(key,['准备','出手','有效','随挥','回收','恢复']); data={'actionId':'zhongli_'+key,'frames':fitted,'sourceFrames':original,'durations':durations,'phases':phaseList,'events':[],'previewOnly':True,'status':'动作素材候选；比例/动作需人工复核，未接正式战斗'}
  if key in BOXES:
   start=sum(durations[:2]); active=sum(durations[2:4]); data['events']=[{'tick':start,'kind':'hit' if key not in ('skillE','skillQ','throw') else {'skillE':'pillar-create','skillQ':'q-confirm','throw':'grab'}[key],'hitId':f'zhongli_{key}_1','damageSegments':1}]
   data['combatDesign']={'startup':start,'active':active,'recovery':sum(durations[4:]),'box':BOXES[key],'lunge':18 if key=='heavy' else 0,'level':'low' if key.startswith('crouch') else 'high' if key.startswith('air') else 'mid','damage':'待战斗调参','cancel':'命中/防御确认候选；未接入','invulnerability':0,'hurtbox':[ -42,0,84,280],'status':'design-only'}
  if key=='skillE':data['combatDesign'].update(pillarLimit=1,passiveDamage=False,casterHitBeforeRelease='cancel',casterHitAfterRelease='pillar persists for candidate lifetime')
  if key=='skillQ':
   data['branches']={'hit':{'durations':[8,8,10,44,12,12],'damageSegments':1,'petrifyTicks':30,'cutin':[19,38],'meteorTick':44,'damageTick':52},'whiff':{'durations':durations,'damageSegments':0,'cinematic':False},'block':{'durations':durations,'damageSegments':0,'cinematic':False}}
   data['combatDesign']['branches']=['命中确认完整演出','落空短恢复','防御短恢复']; data['cinematic']={'hitTicks':[52],'portrait':'ultimate-portrait.png','portraitFit':'ultimate-portrait-fit.png'}
  if key=='throw':data['events']+=[{'tick':12,'kind':'pair-lock'},{'tick':18,'kind':'release','hitId':'zhongli_throw_release','damageSegments':1}];data['pairing']={'victim':'被投','anchor':'wrist/chest candidate contact','releaseTick':18,'landingTick':23,'noFX':True,'escape':'startup candidate escape allowed; no regrab while down/air/invulnerable'}
  bank[label]=data;report['actions'][key]={'sha256':sha(src),'rectangles':counts,'registrations':registration,'sourceSize':Image.open(src).size,'adoption':adoption.get(key), 'displayCount':len(records)}
 # Exact shared poses at semantic boundaries, retaining generated alternatives in source sheets.
 for label in ('前冲','后撤','胜利'):
  for k in ('frames','sourceFrames'):bank[label][k][0]=bank['待机'][k][0];bank[label][k][-1]=bank['待机'][k][0]
 for k in ('frames','sourceFrames'):
  bank['起身'][k][0]=bank['受击与倒地'][k][-1];bank['起身'][k][-1]=bank['待机'][k][0];bank['被投'][k][-1]=bank['受击与倒地'][k][-1]
 for key,label in [('pillarFx','E · 地心'),('meteorFx','Q · 天星')]:
  src=OUT/f'sources/{key}.png'; sheet=Image.open(src).convert('RGBA'); n=4 if key=='pillarFx' else 3; cols=2 if n==4 else 3; rows=2 if n==4 else 1; records=[{'roi':[i%cols*sheet.width//cols,i//cols*sheet.height//rows,(i%cols+1)*sheet.width//cols,(i//cols+1)*sheet.height//rows]} for i in range(n)]; imgs=[sheet.crop(r['roi']) for r in records]; pal=artlib.build_palette([artlib.downscale(im,.18) for im in imgs],16,seed=11)+[[46,31,20]]; originals=[]; fits=[]
  for i,im in enumerate(imgs):
   name=f'frames/{key}-{i}.png';im.save(OUT/name); sc=.64 if key=='pillarFx' else .7; anchor=[im.width*.5,im.height-1] if key=='pillarFx' else [im.width*.5,im.height*.65]
   originals.append({'file':name,'anchor':anchor,'scale':sc,'source':f'sources/{key}.png'});f,rects=fit(im,sc,pal,False); fn=f'fitted/{key}-{i}.png';f.save(OUT/fn);fa=[v*sc/4 for v in anchor];fits.append({'file':fn,'anchor':fa,'scale':4,'source':f'sources/{key}.png'})
   write(OUT/f'rects/{key}-{i}.json',{'palette':pal,'width':f.width,'height':f.height,'rects':rects,'anchor':fa,'scale':4,'sourceROI':records[i]['roi'],'sourceSHA256':sha(src),'fittedSHA256':sha(OUT/fn)})
  bank[label]['effects']={'sourceFrames':originals,'frames':fits,'fitFrames':fits,'startTick':14 if key=='pillarFx' else 44,'duration':80 if key=='pillarFx' else 35,'worldOffset':[205,0],'followActor':False,'independent':True}
 portrait=ROOT/'assets/roster-v2/zhongli-official-head.png';shutil.copy(portrait,OUT/'ultimate-portrait.png');p=Image.open(portrait).convert('RGBA');pal=artlib.build_palette([p],20)+[[40,29,27]];f,rects=fit(p,.9,pal,True);f.save(OUT/'ultimate-portrait-fit.png');write(OUT/'rects/portrait.json',{'palette':pal,'width':f.width,'height':f.height,'rects':rects,'sourceSHA256':sha(portrait),'fittedSHA256':sha(OUT/'ultimate-portrait-fit.png')})
 write(OUT/'actions.json',bank);flat=[n for a in report['actions'].values() for n in a['rectangles']];report['bodyRectangles']={'max':max(flat),'mean':sum(flat)/len(flat)};write(OUT/'制作检查.json',report)
 print(json.dumps({'groups':len(bank),'poses':sum(len(v['frames']) for v in bank.values()),'rectangles':report['bodyRectangles']},ensure_ascii=False))

if __name__=='__main__':main()
