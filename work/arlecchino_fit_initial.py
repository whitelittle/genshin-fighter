from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw,ImageFont
import json,hashlib,numpy as np
import clorinde_assets as ca
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';ca.O=o
# Reuse the verified fitting method, never the other character's output/data.
palette=ca.artlib.build_palette([ca.artlib.downscale(Image.open(o/'frames/mother-extracted-v6.png'),.06)],16,seed=31)+[[245,213,200],[240,240,248],[19,21,30]]
(o/'palette.json').write_text(json.dumps(palette),encoding='utf-8');data={};audit=[]
calibrations=json.loads((o/'source-calibration.json').read_text(encoding='utf-8')) if (o/'source-calibration.json').exists() else {}
def isolate(file,n,group,unit,hips):
 im=Image.open(o/file).convert('RGBA');a=np.array(im);core=a[:,:,3]>=250;allgs=ca.components(core);gs=allgs[:n]
 assert len(gs)==n and min(ca.area(g) for g in gs)>10000,(file,len(gs),n)
 bodyBounds={id(g):ca.bounds(g) for g in gs}
 bodyRuns={id(g):np.asarray(g,dtype=float) for g in gs}
 def coreDistance(g,x,y):
  runs=bodyRuns[id(g)];dx=np.maximum(np.maximum(runs[:,1]-x,x-(runs[:,2]-1)),0);dy=runs[:,0]-y
  return float(np.min(dx*dx+dy*dy))
 cal=calibrations.get(group,{})
 # White trim/hair may have detached opaque islands; preserve source fragments
 # with their nearest genuine body rather than discarding them as extra actors.
 for fragment in allgs[n:]:
  if ca.area(fragment)<10:continue
  fb=ca.bounds(fragment);cx=(fb[0]+fb[2])/2;cy=(fb[1]+fb[3])/2
  def distance(g):
   return coreDistance(g,cx,cy)
  nearest=min(gs,key=distance)
  bladeHints=cal.get('bladeCenters',[(440,365),(928,303),(493,718),(948,742),(457,1322),(934,1360)])
  bladeNear=min((x-cx)**2+(y-cy)**2 for x,y in bladeHints)<150**2
  colors=np.concatenate([a[y,x0:x1,:3] for y,x0,x1 in fragment]);redFraction=float(((colors[:,0]>70)&(colors[:,0]>colors[:,1]*1.4)&(colors[:,0]>colors[:,2]*1.4)).mean())
  shaftPart=None
  if cal.get('shaftHints') and (redFraction>.08 or float(colors.max(axis=1).mean())<120):
   def lineDistance(line):
    (ax,ay),(bx,by)=line;dx=bx-ax;dy=by-ay;u=max(0,min(1,((cx-ax)*dx+(cy-ay)*dy)/max(1,dx*dx+dy*dy)));return (cx-ax-u*dx)**2+(cy-ay-u*dy)**2
   candidate=min(range(len(cal['shaftHints'])),key=lambda j:lineDistance(cal['shaftHints'][j]))
   if lineDistance(cal['shaftHints'][candidate])<24**2:shaftPart=candidate
  if shaftPart is not None or (((group=='light2-sweep-v2' and ca.area(fragment)>2000) or (cal.get('bladeCenters') and ca.area(fragment)>cal.get('minBladeArea',6000))) and bladeNear and redFraction>.08):
   bladeCenters=cal.get('bladeCenters',[(440,365),(928,303),(493,718),(948,742),(457,1322),(934,1360)])
   bodySeeds=cal.get('bodySeeds',[(220,270),(740,300),(310,800),(760,820),(280,1280),(740,1290)])
   part=shaftPart if shaftPart is not None else min(range(len(bladeCenters)),key=lambda j:(bladeCenters[j][0]-cx)**2+(bladeCenters[j][1]-cy)**2)
   px,py=bodySeeds[part]
   def bodyDistance(g):
    return coreDistance(g,px,py)
   nearest=min(gs,key=bodyDistance);nearest.extend(fragment)
  elif group=='light2-sweep-v2' or cal.get('bladeCenters') or distance(nearest)<1600:nearest.extend(fragment)
  bodyRuns[id(nearest)]=np.asarray(nearest,dtype=float)
 gs.sort(key=lambda g:(ca.bounds(g)[1]+ca.bounds(g)[3])/2)
 rows={};row=0;last=None;height=float(np.median([ca.bounds(g)[3]-ca.bounds(g)[1] for g in gs]))
 for g in gs:
  center=(ca.bounds(g)[1]+ca.bounds(g)[3])/2
  if last is not None and center-last>height*.35:row+=1
  rows[id(g)]=row;last=center
 gs.sort(key=lambda g:(rows[id(g)],ca.bounds(g)[0]))
 sf=[];ff=[]
 for i,g in enumerate(gs):
  mask=np.zeros(core.shape,dtype='uint8')
  for y,x0,x1 in g:mask[y,x0:x1]=255
  keep=np.asarray(Image.fromarray(mask).filter(ImageFilter.MaxFilter(5)))>0
  outside=Image.fromarray(mask.copy());ImageDraw.floodfill(outside,(0,0),128)
  # Enclosed lower-alpha garment shading is still original subject material.
  # Restore it from source RGBA; alpha0 cutout holes remain alpha0.
  holes=(np.asarray(outside)==0)&(mask==0)
  for hole in ca.components(holes):
   # A loop of arms/shaft can enclose another atlas pose. Never restore that
   # pose as 'interior shading' merely because it lies inside the loop.
   if any(np.any(core[y,x0:x1]) for y,x0,x1 in hole):continue
   for y,x0,x1 in hole:keep[y,x0:x1]|=a[y,x0:x1,3]>=128
  shaftHints={
   'light1-pole-v2':[((215,110),(720,275)),((1000,165),(1490,275)),((228,659),(813,663)),((977,629),(1455,765))],
   'light2-sweep-v2':[((48,213),(443,323)),((540,208),(925,305)),((38,680),(500,699)),((535,624),(938,710)),((60,1155),(450,1320)),((540,1198),(944,1348))]}
  if cal.get('shaftHints'):shaftHints[group]=cal['shaftHints']
  if group in shaftHints:
   # Source-local thin rigid weapon support has lower alpha than the clothing
   # core. Preserve its ORIGINAL RGBA along a reviewed corridor, not paint a
   # replacement line and not discard it as transparent background.
   hint=Image.new('L',im.size);ImageDraw.Draw(hint).line(shaftHints[group][i],fill=255,width=48)
   shaftAlpha=(a[:,:,3]>=128)|((a[:,:,3]>=64)&(a[:,:,:3].max(axis=2)<140))
   keep|=(np.asarray(hint)>0)&shaftAlpha
  for x0,y0,x1,y1 in cal.get('excludedSourceRects',[]):keep[y0:y1,x0:x1]=False
  rgba=a.copy();rgba[~keep]=0;b=ca.bounds(g);roi=[max(0,b[0]-5),max(0,b[1]-5),min(im.width,b[2]+5),min(im.height,b[3]+5)];obj=Image.fromarray(rgba).crop(roi)
  fn=f'frames/{group}-{i}.png';obj.save(o/fn);anchor=[hips[i]-roi[0],b[3]-1-roi[1]]
  if cal.get('supportY'):anchor[1]=cal['supportY'][i]-roi[1]
  if group=='jump-v1' and i in [2,3,4]:
   anchor[1]=[330,230,755,746,1260,1350][i]+175/unit-roi[1]
  f={'file':fn,'source':file,'sourceOrigin':roi[:2],'roi':roi,'anchor':anchor,'scale':unit,'fullCanvasContact':b[0]<=1 or b[1]<=1 or b[2]>=im.width-1 or b[3]>=im.height-1,'sourceHash':hashlib.sha256((o/fn).read_bytes()).hexdigest(),'extraction':'alpha250 core plus two source-pixel original RGBA fringe','calibration':'manual declared uniform source unit; visual candidate'}
  fit,_=ca.canonical_fit(obj,anchor,unit,palette,f'{group}-{i}');sf.append(f);ff.append(fit)
  audit.append({'file':fn,'opaqueCorePixels':ca.area(g),'canvasContact':f['fullCanvasContact'],'rectangles':fit['rectangles']})
 return sf,ff
# Breath v1/v2 form one new matching pair; mother is only the identity/proportion reference.
a,b=isolate('source/idle-inhale-v1.png',1,'idle-open',.23,[615]);c,d=isolate('source/idle-inhale-v2.png',1,'idle-blink',.23,[615])
data['idle']={'label':'待机','sourceFrames':a+c,'frames':b+d,'durations':[48,12],'phases':['呼吸保持','眨眼吸气'],'status':'新待机候选；脚底与循环接缝仍待播放核对','events':[]}
a,b=isolate('source/walk-passing-v2.png',6,'walk-passing-v2',.60,[303,803,306,816,305,807])
data['walk']={'label':'前走','sourceFrames':a,'frames':b,'durations':[6]*6,'phases':['左接触','左承重','右经过','右接触','右承重','左经过'],'status':'经过姿源图已重画；左右支撑身份、脚底与循环仍待精校','events':[],'motion':{'kind':'walk','direction':1,'distance':80}}
a,b=isolate('source/backwalk-v1.png',6,'backwalk',.70,[337,811,337,823,338,812])
data['backwalk']={'label':'后退','sourceFrames':a,'frames':b,'durations':[7]*6,'phases':['后脚探落','后脚承重','前脚收近','交替蹬退','交替承重','收脚恢复'],'status':'新后退候选；保持右朝向，支撑与循环待精校','events':[],'motion':{'kind':'walk','direction':-1,'distance':70}}
a,b=isolate('source/light1-pole-v2.png',4,'light1-pole-v2',.70,[478,1240,463,1240])
data['light1']={'label':'轻1 · 枪尾短击','sourceFrames':a,'frames':b,'durations':[4,3,3,12],'phases':['持柄准备','前踏送柄','枪尾有效','撤肘收势'],'status':'杆轴弯曲源图已修；身体与持武器合成候选，握点/连接仍待复核','events':[{'tick':7,'kind':'pole-butt-hit','hitId':'light1-1','status':'design only'}],'weaponLayer':'held actual weapon composite; independent slash/impact not baked'}
a,b=isolate('source/light2-sweep-v2.png',6,'light2-sweep-v2',.75,[234,748,274,746,270,741])
data['light2']={'label':'轻2 · 镰扫','sourceFrames':a,'frames':b,'durations':[4,4,3,4,4,12],'phases':['低位持镰','屈膝蓄势','镰刃有效','横扫随势','屈肘制动','低位恢复'],'status':'镰刃在前横扫候选；武器一致性、握点、尺度与连接待复核','events':[{'tick':8,'kind':'scythe-sweep-hit','hitId':'light2-1','status':'design only'}],'weaponLayer':'held weapon composite, no baked attack FX'}
for key,label,n,unit,hips,durations,phases in [
 ('crouch','蹲下',4,.39,[383,833,365,839],[3,3,8,18],['屈膝','下沉','低位稳身','保持']),
 ('standguard','站防',4,.44,[310,825,310,817],[4,10,8,6],['抬臂','前臂防护','承压','复位']),
 ('crouchguard','蹲防',4,.45,[435,1140,465,1175],[4,10,8,6],['下沉抬臂','低位防护','低位承压','回蹲']),
 ('jump','跳跃',6,.56,[335,787,324,806,337,793],[6,4,7,10,7,8],['预蹲','蹬地','上升','顶点','下降','落地'])]:
 a,b=isolate(f'source/{key}-v1.png',n,f'{key}-v1',unit,hips)
 data[key]={'label':label,'sourceFrames':a,'frames':b,'durations':durations,'phases':phases,'events':[],'status':'新基础动作候选；体型、支撑与衔接待复核'}
 if key=='jump':data[key]['motion']={'kind':'jump','height':120,'takeoffTick':6,'landingTick':34,'anchorPolicy':'air poses virtual support below hip; landing actual foot support'}
for plan in json.loads((o/'additional-body-plans.json').read_text(encoding='utf-8')) if (o/'additional-body-plans.json').exists() else []:
 a,b=isolate(plan['source'],plan['n'],plan['group'],plan['unit'],plan['hips'])
 data[plan['key']]={'label':plan['label'],'sourceFrames':a,'frames':b,'durations':plan['durations'],'phases':plan['phases'],'events':[{'tick':plan['hitTick'],'kind':'weapon-hit','hitId':plan['key']+'-1','status':'design only'}] if 'hitTick' in plan else [],'status':plan.get('status','新攻击合成候选；使用靴底支撑而非刀尖，握点/尺度/连接待复核'),'weaponLayer':plan.get('weaponLayer','held weapon composite; independent effects pending')}
 current=data[plan['key']]
 if plan.get('motion'):current['motion']=plan['motion']
 if plan.get('appendIdlePrefix'):
  for field in ['sourceFrames','frames']:current[field].insert(0,data['idle'][field][0])
  current['durations'].insert(0,4);current['phases'].insert(0,'待机起势')
 for flag,key,index,duration,label in [('appendJumpDescent','jump',4,4,'下降衔接'),('appendLanding','jump',5,8,'落地缓冲'),('appendIdle','idle',0,4,'恢复待机')]:
  if not plan.get(flag):continue
  for field in ['sourceFrames','frames']:current[field].append(data[key][field][index])
  current['durations'].append(duration);current['phases'].append(label)
if 'heavy' in data and (o/'source/heavy-effective-single-v4.png').exists():
 a,b=isolate('source/heavy-effective-single-v4.png',1,'heavy-effective-single-v4',.30,[810])
 data['heavy']['sourceFrames'][3]=a[0];data['heavy']['frames'][3]=b[0]
 data['heavy']['status']='有效姿改用独立完整源图；镰尖不再低于靴底，握点/尺度/连接待复核'
if all(key in data for key in ['Q','throw','victim','hit_knockdown','wakeup']):
 q=data['Q'];base={field:q[field][:] for field in ['frames','sourceFrames']}
 for field in base:q[field]=[base[field][i] for i in [0,1,1,2,3,3,4,4,5]]+[data['idle'][field][0]]
 q['durations']=[6,6,30,10,18,24,24,14,10,20];q['phases']=['短切确认','确认收势','头像切入','蓄势','释放','持续冲击一','持续冲击二','持续冲击三','收束','恢复待机']
 q['cinematic']={'confirmationTick':6,'cutin':[12,42],'charge':[42,52],'releaseTick':52,'hitTicks':[70,94,118],'fade':[132,142],'recover':[142,162],'fullRequires':'confirmed hit'}
 q['events']=[{'tick':6,'kind':'confirm','damage':0}]+[{'tick':t,'kind':'bloodfire-hit','hitId':'Q-'+str(i+1),'requiresConfirmedHit':True} for i,t in enumerate([70,94,118])]
 q['shortBranch']={'indices':[0,1,9],'durations':[6,6,12],'events':[{'tick':6,'kind':'confirm','damage':0}]}
 for field in ['sourceFrames','frames']:
  data['wakeup'][field]=[data['hit_knockdown'][field][-1]]+data['wakeup'][field]+[data['idle'][field][0]]
  data['victim'][field]+=[data['hit_knockdown'][field][-1],data['wakeup'][field][1]]
  data['throw'][field]+=[data['idle'][field][0]]
 data['wakeup']['durations']=[6,8,10,8,4];data['wakeup']['phases']=['落地共用','侧撑','单膝','站稳','恢复待机']
 data['victim']['durations']=data['throw']['durations']=[4,4,8,16,6,12]
 data['victim']['phases']=['接触','牵引','离地','侧落','落地共用','侧撑共用'];data['throw']['phases']=['接近','伸手','控制','前送','释放','恢复']
 data['throw']['events']=[{'tick':8,'kind':'grab'},{'tick':32,'kind':'release'}]
 lowSF,lowFF=isolate('source/throw-low-push-v2.png',4,'throw-low-push-v2',.46,[350,830,360,820])
 low={field:[data['idle'][field][0],arr[0],arr[0],arr[2],arr[3],data['idle'][field][0]] for field,arr in [('sourceFrames',lowSF),('frames',lowFF)]}
 data['throw']['variants']={'nahida':low};data['throw']['motion']={'kind':'dash','distance':60,'beginTick':0,'endTick':8,'height':0}
 data['throw']['motion']['beginTick']=4
 data['victim']['variants']={'nahida':{field:[arr[0],arr[2]]+data['victim'][field][2:] for field,arr in [('sourceFrames',lowSF),('frames',lowFF)]}}
 data['victim']['variantNote']='low contact reuses own crouched forearm poses; same flight/landing chain; opponent artwork unchanged'
 for field in ['sourceFrames','frames']:
  old=data['victim'][field][:];data['victim'][field]=[old[0],old[0],old[1],old[2],old[3],data['hit_knockdown'][field][-1]]
  arr=lowSF if field=='sourceFrames' else lowFF
  data['victim']['variants']['nahida'][field]=[arr[0],arr[0],arr[2],old[2],old[3],data['hit_knockdown'][field][-1]]
 data['victim']['durations']=[4,4,24,6,4,8];data['victim']['phases']=['准备接触','接触','受控牵引','释放离地','侧落','落地共用']
 for key in ['hit_knockdown','victim','wakeup']:data[key]['directionPolicy']='head-left, boots-right; shared landing/support; whole-world mirror only'
(o/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');(o/'action-data.js').write_text('window.ARLECCHINO_ACTIONS='+json.dumps(data,ensure_ascii=False)+';',encoding='utf-8')
(o/'fitting-verification.json').write_text(json.dumps({'actions':len(data),'displayPoses':sum(len(d['frames']) for d in data.values()),'audit':audit,'pixelRoundtrip':'canonical_fit asserts exact quantized outlined target','sourceProportions':'not deformed; no independent XY scale','artAccepted':False,'browser':'not yet checked for current four-group version','runtimeIntegrated':False,'simulator':'not run','device':'not observed'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'activeDisplayPoses':sum(len(d['frames']) for d in data.values()),'fittedIncludingInactiveTrials':len(audit),'sourceContact':sum(a['canvasContact'] for a in audit),'peakActiveRectangles':max(f['rectangles'] for d in data.values() for f in d['frames'])},ensure_ascii=False))
