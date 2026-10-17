"""Reuse recorded body fitting method and exact V3 opponent exports."""
from pathlib import Path
import json,sys,shutil
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[1];O=R/'outputs/v4-one-character-20261010/ayaka-armed-v2'
sys.path.insert(0,str(R/'game/tools'));import artlib
ref=json.loads((R/'work/v4-handoff-20261009-partial/V4/evidence/kamisatoayaka-idle-review/fit.json').read_text(encoding='utf-8'))
data=json.loads((O/'actions.json').read_text(encoding='utf-8'))
data['站立格挡']['sourceFrames']=json.loads((O/'frames.json').read_text(encoding='utf-8'))['frames']

# Cinematic structure uses the existing ice-ball/ice-wind, not a new effect design.
q=data['Q · 霜灭']
if len(q['frames'])==6:
 for field in ['frames','sourceFrames']:
  q[field]=[dict(q[field][i]) for i in [0,1,2,3,3,4,4,5]]
q['durations']=[12,30,10,18,24,24,14,20]
q['phases']=['聚霜','切入蓄势','拔刀','冰球释放','冰风 · 第一击','冰风 · 第二击','冰风 · 收束','收刀恢复']
q['events']=[{'tick':t,'kind':'cinematic-hit','hitId':'Q-'+str(i+1)} for i,t in enumerate([70,94,118])]
q['combatDesign']['confirmedHits']=[70,94,118]
q['combatDesign'].update(startup=52,active=80,recovery=20)
q['cinematic']={'cutin':[12,42],'releaseTick':52,'hitTicks':[70,94,118],'endTick':152,'effect':'existing ice-ball / ice-wind','previewOnly':True}
q['effects']['startTick']=52;q['effects']['duration']=80

def fitted(f,palette,name,outline=True):
 im=Image.open(O/f['file']).convert('RGBA');ratio=f['scale']/4.5
 sm=artlib.downscale(im,ratio);idx=artlib.apply_palette(sm,palette[:-1] if outline else palette)
 if outline:
  mask=idx>=0;edge=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0;idx[edge&~mask]=len(palette)-1
 rects=artlib.painter(idx);rebuilt=Image.new('RGBA',sm.size);pixels=np.zeros((sm.height,sm.width,4),dtype=np.uint8)
 for x,y,w,h,c in rects:pixels[y:y+h,x:x+w]=palette[c][:3]+[255]
 Image.fromarray(pixels).save(O/name)
 (O/(Path(name).stem+'-rects.json')).write_text(json.dumps({'palette':palette,'rects':rects,'anchor':[f['anchor'][0]*ratio,f['anchor'][1]*ratio],'scale':4.5,'reconstructionTarget':'quantized image','runtimeIntegrated':False},ensure_ascii=False),encoding='utf-8')
 return {**f,'file':name,'anchor':[f['anchor'][0]*ratio,f['anchor'][1]*ratio],'scale':4.5}

shutil.copy2(R/'assets/roster-v2/kamisatoayaka-official-head.png',O/'ultimate-portrait.png')
fitted({'file':'ultimate-portrait.png','anchor':[0,0],'scale':1},ref['palette'],'ultimate-portrait-fit.png',outline=False)

# Source/fit switch must affect every body, including recently remade defenses.
for label,d in data.items():
 if d.get('combatDesign'):continue
 source=d.get('sourceFrames') or d['frames']
 d['frames']=[fitted(f,ref['palette'],f'body-shared-{list(data).index(label)}-{i}.png',outline=label!='站立格挡') for i,f in enumerate(source)]

fxpal=[[231,251,255],[187,232,250],[142,216,249],[93,185,236],[65,137,204],[34,94,165],[24,64,129],[16,36,79],[255,255,255],[186,208,236],[109,160,210],[75,115,172]]
slash=O/'slashFx-attack-source-v1.png'
if slash.exists():
 im=Image.open(slash).convert('RGBA')
 mapping={'轻攻一':(0,[110,-150],.54),'轻攻二':(1,[115,-155],.58),'轻攻三':(2,[120,-145],.62),'站重':(1,[125,-145],.68),'蹲轻':(0,[160,-100],.70),'蹲重':(3,[125,-55],.75),'空轻':(2,[115,0],.52),'空重':(2,[125,20],.65)}
 for label,(row,offset,scale) in mapping.items():
  frames=[]
  for i in range(3):
   box=(i*im.width//3,row*im.height//4,(i+1)*im.width//3,(row+1)*im.height//4);cell=im.crop(box);name=f'slash-{row}-{i}.png';cell.save(O/name)
   frames.append({'file':name,'anchor':[cell.width/2,cell.height*.78 if row==3 else cell.height/2],'scale':scale,'source':slash.name})
  s=data[label]['combatDesign']['startup'];data[label]['effects']={'frames':frames,'startTick':max(0,s-1),'duration':data[label]['combatDesign']['active']+6,'worldOffset':offset,'followActor':True,'independent':True}
for label,d in data.items():
 e=d.get('effects')
 if not e:continue
 e['sourceFrames']=e['frames']
 e['fitFrames']=[fitted(f,fxpal,f'effect-fit-{list(data).index(label)}-{i}.png',False) for i,f in enumerate(e['frames'])]
(O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

baseline=R/'outputs/v4-one-character-20261010/baseline-actions'
params=json.loads((baseline/'parameters.json').read_text(encoding='utf-8'));opponent={}
for p in params['characters']['raidenshogun']['poses']:
 if p['origin']!='keyframes' or not any(p['pose'].startswith(k+'_') for k in ['basic','hurt','victim','throw']):continue
 name='foe-fit-'+p['pose']+'.png';shutil.copy2(baseline/p['file'],O/name)
 opponent[p['pose']]={'file':name,'ax':p['ax'],'ay':p['ay'],'scale':p['u']*330/336,'rects':p['rects'],'source':'actual V3 decoded rectangles'}
(O/'foe-fitted.json').write_text(json.dumps(opponent,ensure_ascii=False,indent=2),encoding='utf-8')
served=R/'work/github-review-20261009/V3/assets/action-reference/ayaka'
for p in O.iterdir():
 if p.suffix in ['.png','.json','.js','.html','.css']:shutil.copy2(p,served/p.name)
print(json.dumps({'fittedActions':len(data),'opponentPoses':len(opponent),'palette':ref['palette_sha256'],'method':'recorded palette, premultiplied BOX, external 1px outline, artlib painter'},ensure_ascii=False))
