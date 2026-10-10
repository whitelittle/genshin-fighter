"""Attack/guard/skill review extension, preserving existing noncombat sources."""
from pathlib import Path
import json,runpy,shutil,hashlib
import numpy as np
from PIL import Image
from build_ayaka_attacks import extract
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
V=R/'work/v4-handoff-20261009-partial/V4';E=V/'evidence'
ns=runpy.run_path(str(R/'work/build_furina_sample.py'))
pair=ns['save_pair'];pal=ns['ref']['palette'];fxpal=ns['fxpal']
data=json.loads((O/'actions.json').read_text(encoding='utf-8'));reports={}
specs={
 'crouchlight':('蹲轻',.40,[3,3,2,1,5,5],[50,10,190,70],'low'),
 'crouchheavy':('蹲重',.51,[5,5,2,2,10,12],[50,0,240,80],'low'),
 'airlight':('空轻',.48,[3,3,3,3,4,4],[45,-50,180,120],'high'),
 'airheavy':('空重',.50,[4,5,3,3,6,6],[35,-100,190,180],'high'),
 'standguard':('站立格挡',.61,[6,8,16,8,16,8],None,None),
 'crouchguard':('蹲防',.43,[6,8,16,8,16,8],None,None),
 'skillE':('E · 孤心沙龙',.61,[8,10,3,3,12,12],[70,100,280,150],'mid'),
 'skillQ':('Q · 万众狂欢',.61,[12,30,14,22,22,22,16,20],None,None),
 'throw':('投技',.62,[8,12,10,8,12,22],None,None),
 'victim':('被投',.56,[8,12,10,8,12,22],None,None),
}
revisions={'crouchlight':('crouchlight-sword',.40),'airlight':('airlight-sword',.50),'crouchheavy':('crouchheavy-seahorse',.43),'standguard':('standguard-crab',.61),'crouchguard':('crouchguard-crab',.43)}
for key,(label,scale,dur,box,level) in specs.items():
 sourcekey=key
 if key in revisions and (O/(revisions[key][0]+'-source-v1.png')).exists():sourcekey,scale=revisions[key]
 path=O/(sourcekey+'-source-v2.png') if (O/(sourcekey+'-source-v2.png')).exists() else O/(sourcekey+'-source-v1.png');rows=extract(path);srcs=[];fits=[];rois=[]
 if path.name=='crouchlight-sword-source-v2.png':
  oldref=extract(O/'crouchlight-sword-source-v1.png')[0][0];newref=rows[0][0]
  scale*= (oldref[3]-oldref[1])/(newref[3]-newref[1])
 if key=='victim':rows=[rows[i] for i in [0,1,1,3,4,5]]
 for i,(roi,im,xs,ys) in enumerate(rows):
  if key.startswith('air') or key=='victim' and i in [1,2,3]:anchor=[im.width*.55,im.height*.65]
  elif key=='victim':anchor=[im.width/2,im.height-1]
  else:
   raw=np.asarray(Image.open(path).convert('RGBA'));colors=raw[ys,xs,:3].astype(float)
   feet=(ys>=ys.max()-35)&(colors[:,2]>colors[:,0]*1.08)&(colors[:,2]>45)
   xx=xs[feet] if feet.any() else xs[ys>=ys.max()-10];yy=ys[feet].max() if feet.any() else ys.max()
   anchor=[float((xx.min()+xx.max())/2)-roi[0],float(yy)-roi[1]]
  usepal=pal
  if sourcekey.endswith('crab') or sourcekey.endswith('seahorse'):
   member='crabaletta' if sourcekey.endswith('crab') else 'chevalmarin'
   hp=json.loads((E/'furina-salon-side-v3'/member/'fit.json').read_text(encoding='utf-8'))['palette']
   usepal=pal+[c[:3] for c in hp if c[:3] not in pal]
  s,f=pair(im,anchor,scale,sourcekey+'-'+str(i),usepal,path.name);s['roi']=list(roi);f['roi']=list(roi);srcs.append(s);fits.append(f);rois.append(list(roi))
 if key=='skillQ':
  srcs=[srcs[i] for i in [0,0,1,2,3,4,5,0]];fits=[fits[i] for i in [0,0,1,2,3,4,5,0]]
 phases=['准备','出手','有效','随动','回收','恢复']
 if 'guard' in key:phases=['进入','防护','保持','受力','回位','恢复']
 if key=='skillE':phases=['提腕','邀请','合击','命中','回收','恢复']
 if key=='skillQ':phases=['水泡确认','头像切入','舞台展开','章鱼 · 第一幕','海马 · 第二幕','蟹 · 终幕','谢幕','恢复']
 if key=='throw':phases=['抓取','水带控制','牵引','蟹撞','释放','恢复']
 if key=='victim':phases=['失衡','受控','牵引','击飞','落地','倒地']
 d={'sourceFrames':srcs,'frames':fits,'durations':dur,'phases':phases,'previewOnly':True,'status':'本地动作/分层演出；未接战斗模拟'}
 if box:
  d['combatDesign']={'startup':sum(dur[:2]),'active':sum(dur[2:4]),'recovery':sum(dur[4:]),'box':box,'level':level,'lunge':0,'damage':'待调','status':'design-only'}
  d['events']=[{'tick':sum(dur[:2]),'hitId':'furina.'+key+'.0','damageSegments':1}]
 if key=='skillQ':
  d['events']=[{'tick':t,'hitId':'furina.Q.'+str(i),'damageSegments':1} for i,t in enumerate([56,78,100])]
  d['cinematic']={'confirmTick':12,'hitTicks':[56,78,100],'previewBranch':'confirmed','unimplementedBranches':['whiff','blocked'],'endTick':sum(dur)}
 if key in ['throw','victim']:
  d['events']=[{'tick':30,'hitId':'furina.throw.0','damageSegments':1}];d['pairedTimeline']='furina-throw'
 if sourcekey.endswith('crab') or sourcekey.endswith('seahorse'):d['heldCompanion']='one embedded contact sprite; do not draw another copy'
 data[label]=d;reports[key]={'source':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'scale':scale,'rois':rois,'notUsedSourceFrames':[2] if key=='victim' else []}

# Open actual existing noncombat source frames only; never invent missing poses.
legacy={'前走':E/'furina-walk-review','后退':E/'codex-batch-20261009/furina-backwalk-body-v1','跳跃':E/'codex-batch-20261009/furina-jump-body-v1','蹲下':E/'codex-batch-20261009/furina-crouch-body-v1','受击与倒地':E/'codex-batch-20261009/furina-hit_knockdown-body-v1'}
for label,folder in legacy.items():
 paths=sorted(folder.glob('source-cell-[0-9]*.png')) or sorted(folder.glob('source-[0-9]*.png'))
 srcs=[];fits=[];scale=None
 for i,path in enumerate(paths):
  im=Image.open(path).convert('RGBA');ar=np.asarray(im);ys,xs=np.where(ar[:,:,3]>=128)
  fitpath=folder/f'optimized-{i}.png' if (folder/f'optimized-{i}.png').exists() else folder/f'fit-{i}.png'
  if scale is None:scale=4.5*Image.open(fitpath).height/im.height
  feet=xs[ys>=ys.max()-10];anchor=[float((feet.min()+feet.max())/2),float(ys.max())]
  name='legacy-'+str(list(legacy).index(label))+'-'+str(i);shutil.copy2(path,O/(name+'.png'));shutil.copy2(fitpath,O/(name+'-fit.png'))
  s={'file':name+'.png','anchor':anchor,'scale':scale};f={'file':name+'-fit.png','anchor':[a*scale/4.5 for a in anchor],'scale':4.5};srcs.append(s);fits.append(f)
 if paths:data[label]={'sourceFrames':srcs,'frames':fits,'durations':[8 if label in ['前走','后退'] else 10]*len(paths),'phases':['姿势 '+str(i+1) for i in range(len(paths))],'status':'复用原有动作，不是本轮重画','legacyReuse':True}
# Existing wakeup is a free 1x4 atlas, not 2x2; manually retain chronological ROIs.
source=V/'assets/codex-batch-20261009/furina-wakeup-body-v1.png'
im=Image.open(source).convert('RGBA');boxes=[(0,545,590,950),(510,390,915,945),(875,190,1245,945),(1210,110,1536,945)]
srcs=[];fits=[]
for i,b in enumerate(boxes):
 cell=im.crop(b);s,f=pair(cell,[cell.width*.62,cell.height-20],.39,'legacy-wakeup-'+str(i),pal,source.name);srcs.append(s);fits.append(f)
data['起身']={'sourceFrames':srcs,'frames':fits,'durations':[12,8,8,10],'phases':['侧撑','单膝','站起','站稳'],'status':'复用原起身；粗ROI，不重画','legacyReuse':True}
for key,label,dur,ph in [('wakeup-clean','起身',[12,8,8,10],['侧撑','单膝','站起','站稳']),('victory-curtaincall','胜利',[16,18,30,40],['站定','提帽','谢幕','收势'])]:
 path=O/(key+'-source-v1.png')
 if not path.exists():continue
 rows=extract(path,4);reference=rows[-1] if key=='wakeup-clean' else rows[0]
 scale=310/(reference[0][3]-reference[0][1]);srcs=[];fits=[]
 for i,(roi,im,xs,ys) in enumerate(rows):
  feet=xs[ys>=ys.max()-10];anchor=[float((feet.min()+feet.max())/2)-roi[0],im.height-1]
  s,f=pair(im,anchor,scale,key+'-'+str(i),pal,path.name);s['roi']=list(roi);f['roi']=list(roi);srcs.append(s);fits.append(f)
 data[label]={'sourceFrames':srcs,'frames':fits,'durations':dur,'phases':ph,'previewOnly':True,'status':'起身清理分离' if key=='wakeup-clean' else '新增提帽谢幕胜利'}

helpers={}
for key,height in [('usher',95),('chevalmarin',85),('crabaletta',65)]:
 folder=E/'furina-salon-side-v3'/key;hp=json.loads((folder/'fit.json').read_text(encoding='utf-8'))['palette'];hp=[c[:3] for c in hp]
 srcs=[];fits=[];scale=None
 for i in range(4):
  path=folder/f'source-cell-{i}.png';im=Image.open(path).convert('RGBA');mask=im.getchannel('A').point(lambda a:255 if a>=128 else 0);b=mask.getbbox();im=im.crop(b)
  if scale is None:scale=height/im.height
  s,f=pair(im,[im.width/2,im.height-1],scale,'helper-'+key+'-'+str(i),hp,path.name);srcs.append(s);fits.append(f)
 helpers[key]={'sourceFrames':srcs,'fitFrames':fits,'uniqueInstance':True}
(O/'helpers.json').write_text(json.dumps(helpers,ensure_ascii=False,indent=2),encoding='utf-8')

comboSrc=[];comboFit=[]
for i in range(4):
 path=E/f'furina-E-fx-review/source-cell-{i}.png';im=Image.open(path).convert('RGBA');b=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox();im=im.crop(b)
 s,f=pair(im,[im.width/2,im.height/2],.65,'combo-effect-'+str(i),ns['fxpal'],path.name);comboSrc.append(s);comboFit.append(f)
data['E · 孤心沙龙']['effects']={'sourceFrames':comboSrc,'fitFrames':comboFit,'frames':comboSrc,'startTick':12,'duration':26,'worldOffset':[210,-165],'followActor':True}
data['Q · 万众狂欢']['effects']={'sourceFrames':comboSrc+ns['fxsources'],'fitFrames':comboFit+ns['fxfits'],'frames':comboSrc+ns['fxsources'],'startTick':6,'duration':136,'worldOffset':[370,-170],'followActor':True}
data['空重']['effects']=dict(data['站重']['effects'],startTick=9,duration=12,nozzles=None,worldOffset=[170,30],rotation=.38)
for label in ['蹲轻','蹲重','空轻']:
 data[label]['effects']={'sourceFrames':comboSrc,'fitFrames':comboFit,'frames':comboSrc,'startTick':data[label]['combatDesign']['startup'],'duration':7,'worldOffset':[210,-20] if label.startswith('蹲') else [205,95],'followActor':True,'impactOnly':True}
if (O/'crouchlight-sword-source-v1.png').exists():
 data['蹲轻']['effects']=dict(data['轻攻一']['effects'],startTick=6,duration=7,worldOffset=[90,-100])
 data['蹲轻']['combatDesign']['box']=[50,40,200,65]
if (O/'airlight-sword-source-v1.png').exists():
 data['空轻']['effects']=dict(data['轻攻三']['effects'],startTick=6,duration=10,worldOffset=[150,0])
 data['空轻']['combatDesign']['box']=[45,40,200,120]
if (O/'crouchheavy-seahorse-source-v1.png').exists():
 d=data['蹲重'];d['durations']=[10,8,3,3,10,12];d['phases']=['托抱','蓄势','喷水','受力','收回','恢复']
 d['events']=[{'tick':18,'hitId':'furina.crouchheavy.0','damageSegments':1}]
 d['combatDesign'].update(startup=18,active=6,recovery=22,box=[80,100,300,85],level='mid')
 mouths=[(379,230),(985,172),(1510,175),(463,655),(884,768),(1480,766)]
 nozzles=[[(m[0]-f['roi'][0]-f['anchor'][0])*f['scale'],(m[1]-f['roi'][1]-f['anchor'][1])*f['scale']] for m,f in zip(mouths,d['sourceFrames'])]
 d['effects']=dict(data['站重']['effects'],startTick=18,nozzles=nozzles)
 d['mouthsSource']=mouths
(O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
baseline=R/'outputs/v4-one-character-20261010/baseline-actions'
foes=json.loads((O/'foe-fitted.json').read_text(encoding='utf-8'))
for p in json.loads((baseline/'parameters.json').read_text(encoding='utf-8'))['characters']['raidenshogun']['poses']:
 if p['origin']!='keyframes' or not any(p['pose'].startswith(k+'_') for k in ['light','heavy','air']):continue
 name='foe-fit-'+p['pose']+'.png';shutil.copy2(baseline/p['file'],O/name)
 foes[p['pose']]={'file':name,'ax':p['ax'],'ay':p['ay'],'scale':p['u']*330/336,'rects':p['rects']}
(O/'foe-fitted.json').write_text(json.dumps(foes,ensure_ascii=False,indent=2),encoding='utf-8')
missing=[k for k in ['前冲','后撤','胜利','败北'] if k not in data]
(O/'攻击防御技能检查.json').write_text(json.dumps({'newSources':reports,'available':list(data),'missingUnchanged':missing,'excluded':'victim source frame2: extra hand','validation':'source/fit reconstruction only; preview not combat','simulation':'not run','device':'not observed'},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'available':len(data),'missingUnchanged':missing,'newBodyGroups':len(specs)},ensure_ascii=False))
shutil.copy2(R/'work/furina_review_app.js',O/'app.js')
html=(O/'index.html').read_text(encoding='utf-8').replace('app.js?v=sword1','app.js?v=full1')
html=html.replace('<label><input id="fx"','<label><input id="companions" type="checkbox" checked>伙伴</label><label><input id="fx"',1)
(O/'index.html').write_text(html,encoding='utf-8')
served=R/'work/github-review-20261009/V3/assets/action-reference/furina'
for p in O.iterdir():
 if p.suffix in ['.png','.json','.html','.js','.css']:shutil.copy2(p,served/p.name)
