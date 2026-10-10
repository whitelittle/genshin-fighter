"""Furina held-seahorse contact sample, shared existing preview and fitting."""
from pathlib import Path
import json,shutil,sys,hashlib
import numpy as np
from PIL import Image
from build_ayaka_attacks import extract
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
A=R/'outputs/v4-one-character-20261010/ayaka-armed-v2'
sys.path.insert(0,str(R/'game/tools'));import artlib
ref=json.loads((R/'work/v4-handoff-20261009-partial/V4/evidence/furina-idle-review/fit.json').read_text(encoding='utf-8'))
helper=json.loads((R/'work/v4-handoff-20261009-partial/V4/evidence/furina-salon-side-v3/chevalmarin/fit.json').read_text(encoding='utf-8'))
palette=ref['palette'][:-1]
for c in helper['palette']:
 if c[:3] not in palette:palette.append(c[:3])
counts=[]
def save_pair(im,anchor,scale,name,pal,source):
 source_name=name+'.png';im.save(O/source_name)
 small=artlib.downscale(im,scale/4.5);idx=artlib.apply_palette(small,pal)
 rects=artlib.painter(idx);pixels=np.zeros((small.height,small.width,4),dtype=np.uint8)
 for x,y,w,h,c in rects:pixels[y:y+h,x:x+w]=pal[c][:3]+[255]
 expected=np.zeros_like(pixels)
 for c,color in enumerate(pal):expected[idx==c]=color[:3]+[255]
 assert np.array_equal(pixels,expected)
 fit_name=name+'-fit.png';Image.fromarray(pixels).save(O/fit_name)
 fitanchor=[anchor[0]*scale/4.5,anchor[1]*scale/4.5]
 (O/(name+'-rects.json')).write_text(json.dumps({'palette':pal,'rects':rects,'anchor':fitanchor,'scale':4.5,'runtimeIntegrated':False}),encoding='utf-8')
 counts.append(len(rects))
 return ({'file':source_name,'anchor':anchor,'scale':scale,'source':source}, {'file':fit_name,'anchor':fitanchor,'scale':4.5,'source':source})

originals=[];fits=[];rois=[];nozzles=[]
mouths=[(383,176),(907,146),(1420,163),(398,682),(880,740),(1378,682)]
for i,(roi,im,xs,ys) in enumerate(extract(O/'light1-contact-source-v1.png')):
 foot=xs[ys>=ys.max()-10];rootx=float((foot.min()+foot.max())/2);rooty=roi[3]-1
 anchor=[rootx-roi[0],rooty-roi[1]];src,fit=save_pair(im,anchor,.61,f'light1-contact-{i}',palette,'light1-contact-source-v1.png')
 src['roi']=list(roi);fit['roi']=list(roi);originals.append(src);fits.append(fit);rois.append(list(roi))
 nozzles.append([(mouths[i][0]-rootx)*.61,(mouths[i][1]-rooty)*.61])
water=Image.open(O/'light1-water-source-v1.png').convert('RGBA');fxsources=[];fxfits=[]
fxpal=[[241,253,255],[200,244,255],[142,229,255],[90,207,249],[43,170,228],[24,124,197],[12,79,155],[10,45,102],[255,255,255],[103,163,220],[172,213,239],[53,102,170]]
for i in range(3):
 # Narrow sheet divider pixels are not part of the authored water effect.
 cw=water.width//3;im=water.crop((i*cw+5,0,(i+1)*cw-5,water.height))
 src,fit=save_pair(im,[30-5,water.height*.50],.44,f'water-{i}',fxpal,'light1-water-source-v1.png');fxsources.append(src);fxfits.append(fit)
idle=[];idlefit=[]
for i in range(2):
 path=R/f'work/v4-handoff-20261009-partial/V4/evidence/furina-idle-review/source-cell-{i}.png'
 im=Image.open(path).convert('RGBA');ar=np.asarray(im);ys,xs=np.where(ar[:,:,3]>=128);foot=xs[ys>=ys.max()-10]
 anchor=[float((foot.min()+foot.max())/2),float(ys.max())]
 scale=.325
 s,f=save_pair(im,anchor,scale,f'idle-{i}',ref['palette'],'idle-'+str(i)+'.png');idle.append(s);idlefit.append(f)
actions={
 '待机':{'frames':idlefit,'sourceFrames':idle,'durations':[40,40],'phases':['呼吸','呼吸'],'status':'复用既有空手待机'},
 '站重':{'frames':fits,'sourceFrames':originals,'durations':[10,8,3,3,10,12],'phases':['托抱','蓄势','喷水','受力','收回','恢复'],'events':[{'tick':18,'hitId':'furina.heavy.0','damageSegments':1}],
 'combatDesign':{'startup':18,'active':6,'recovery':22,'box':[80,190,300,85],'level':'mid','lunge':0,'status':'design-only'},
 'effects':{'frames':fxsources,'sourceFrames':fxsources,'fitFrames':fxfits,'startTick':18,'duration':10,'worldOffset':[0,0],'followActor':True,'nozzles':nozzles},
 'status':'人物与被抱海马接触合成小样；水效独立；未接游戏','previewOnly':True,'heldCompanion':'one embedded contact sprite, independent free-flight companion not implemented'}
}
for key,label,durations,box,lunge in [
 ('sword-light1','轻攻一',[3,3,2,1,5,6],[55,140,190,65],18),
 ('sword-light2','轻攻二',[3,4,2,2,6,7],[55,135,200,110],20),
 ('sword-light3','轻攻三',[4,4,3,2,7,9],[55,90,215,150],30)]:
 path=O/(key+'-source-v1.png')
 if not path.exists():continue
 rows=extract(path);srcs=[];fitted=[]
 # One reference-pose calibration per source, never each frame's changing bbox.
 scale=310/(rows[0][0][3]-rows[0][0][1])
 for i,(roi,im,xs,ys) in enumerate(rows):
  raw=np.asarray(Image.open(path).convert('RGBA'));colors=raw[ys,xs,:3].astype(float)
  boot=(ys>=ys.max()-35)&(colors[:,2]>colors[:,0]*1.08)&(colors[:,2]>45)
  fx=xs[boot] if boot.any() else xs[ys>=ys.max()-10]
  fy=ys[boot].max() if boot.any() else ys.max()
  anchor=[float((fx.min()+fx.max())/2)-roi[0],float(fy)-roi[1]]
  s,f=save_pair(im,anchor,scale,key+'-'+str(i),ref['palette'],path.name)
  s['roi']=list(roi);f['roi']=list(roi);srcs.append(s);fitted.append(f)
 actions[label]={'sourceFrames':srcs,'frames':fitted,'durations':durations,'phases':['准备','出手','有效','随挥','回收','恢复'],
  'events':[{'tick':sum(durations[:2]),'hitId':'furina.'+key,'damageSegments':1}],
  'combatDesign':{'startup':sum(durations[:2]),'active':sum(durations[2:4]),'recovery':sum(durations[4:]),'box':box,'lunge':lunge,'level':'mid','status':'design-only'},'previewOnly':True,'status':'新持剑轻攻关键帧，未接游戏判定'}
 slashpath=O/'sword-watertrail-source-v1.png'
 if slashpath.exists():
  atlas=Image.open(slashpath).convert('RGBA');row=int(key[-1])-1;sfx=[];ffx=[]
  for i in range(3):
   cell=atlas.crop((i*atlas.width//3,row*atlas.height//3,(i+1)*atlas.width//3,(row+1)*atlas.height//3))
   ax=cell.width*.12 if row==0 else cell.width/2
   s,f=save_pair(cell,[ax,cell.height/2],.52,key+'-effect-'+str(i),fxpal,slashpath.name);sfx.append(s);ffx.append(f)
  actions[label]['effects']={'sourceFrames':sfx,'fitFrames':ffx,'frames':sfx,'startTick':sum(durations[:2]),'duration':sum(durations[2:4])+4,'worldOffset':[100,-165] if row==0 else [160,-165],'followActor':True}
(O/'actions.json').write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf-8')
html=(A/'index.html').read_text(encoding='utf-8').replace('神里绫华 · 持械动作重制','芙宁娜 · 动作展示').replace('神里绫华 · 动作展示','芙宁娜 · 动作展示').replace('app.js?v=attacks2','app.js?v=sword1')
html=html.replace('<option value="source" selected>源图</option><option value="fit">拟合图</option>','<option value="source">源图</option><option value="fit" selected>拟合图</option>')
html=html.replace('<option value="#171625">深色</option><option value="#ffffff">白色</option>','<option value="#171625">深色</option><option value="#ffffff" selected>白色</option>')
(O/'index.html').write_text(html,encoding='utf-8');shutil.copy2(A/'action-wrap.css',O/'action-wrap.css')
app=(A/'app.js').read_text(encoding='utf-8')
app=app.replace("const groups={'移动与防御':['待机','前走','后退','跳跃','前冲','后撤','蹲下','站立格挡','蹲防'],'攻击':['轻攻一','轻攻二','轻攻三','站重','蹲轻','蹲重','空轻','空重'],'技能与投技':['E · 冰华','Q · 霜灭','投技','被投'],'受击与结算':['受击与倒地','起身','胜利','败北']};","const groups={'基础':['待机'],'攻击':['轻攻一','轻攻二','轻攻三','站重']};")
app=app.replace('ayaka-display-config','furina-display-config')
start=app.index('function drawEffects(');end=app.index('\nfunction drawBoxes(',start)
app=app[:start]+"""function drawEffects(x,y){const e=bank[selected]?.effects;if(!$('fx').checked||!e||time<e.startTick||time>=e.startTick+e.duration)return;const age=time-e.startTick,i=Math.min(2,Math.floor(age/e.duration*3)),list=$('material').value==='fit'?e.fitFrames:e.sourceFrames,f=list[i],im=effectImages[i],n=e.nozzles?e.nozzles[phase()]:e.worldOffset;if(!im||!n)return;ctx.save();ctx.imageSmoothingEnabled=false;ctx.globalAlpha=Math.min(1,(e.duration-age)/3);ctx.drawImage(im,x+n[0]-f.anchor[0]*f.scale,y+n[1]-f.anchor[1]*f.scale,im.naturalWidth*f.scale,im.naturalHeight*f.scale);ctx.restore()}"""+app[end:]
app=app.replace("const sheet=foeAtlas[key]","const sheet=foeAtlas[key]")
point=" const sheet=foeAtlas[key]"
fittedpoint=" if($('material').value==='fit')"
pos=app.index(fittedpoint,app.index('function drawFoe'))
app=app[:pos]+" const cd=bank[selected]?.combatDesign;if(cd){x=selected==='站重'?790:660;const hit=cd.startup;if(time>=hit&&time<hit+cd.active+10){key='hurt';index=0;x+=Math.min(18,(time-hit)*2)}}\n"+app[pos:]
(O/'app.js').write_text(app,encoding='utf-8')
for p in A.glob('foe-fit-*.png'):shutil.copy2(p,O/p.name)
shutil.copy2(A/'foe-fitted.json',O/'foe-fitted.json')
save_pair(Image.open(R/'assets/roster-v2/furina-official-head.png').convert('RGBA'),[0,0],1,'ultimate-portrait',ref['palette'],'furina-official-head.png')
served=R/'work/github-review-20261009/V3/assets/action-reference/furina';served.mkdir(exist_ok=True)
for p in O.iterdir():
 if p.suffix in ['.png','.json','.html','.js','.css']:shutil.copy2(p,served/p.name)
report={'sourceROI':rois,'mouthsSource':mouths,'mouthOffsetsWorld':nozzles,'bodyScale':.61,'rectangleCounts':counts,'reconstruction':'quantized target exact','scope':'held contact composite + independent water effect; not independent companion entity','game':'not integrated','device':'not observed','sources':{n:hashlib.sha256((O/n).read_bytes()).hexdigest() for n in ['light1-contact-source-v1.png','light1-water-source-v1.png']}}
(O/'小样检查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
