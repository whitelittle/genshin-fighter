from pathlib import Path
import json,re,shutil
import numpy as np
from PIL import Image
import clorinde_assets as ca
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013/zhongli';ca.O=O
H=O/'history/feedback-20261014';H.mkdir(parents=True,exist_ok=True)
for name in ['actions.json','app.js','offline.html','size-review.html']:
 if not (H/name).exists():shutil.copy2(O/name,H/name)
src=O/'sources/victory-tea-v9-20261014.png'
shutil.copy2(Path.home()/'.codex/generated_images/01a13432-9c6c-75f3-b290-4337bd1d9e7b/exec-f327912b-5ca0-4180-8c58-98959848834f.png',src)
bank=json.loads((H/'actions.json').read_text(encoding='utf8'))
palette=json.loads((O/'rects/idle-0-optimized.json').read_text(encoding='utf8'))['palette']
palette=palette[:-1]+[[252,246,233],[204,171,98],palette[-1]]
audit=[]
def make(source,n,key,unit,items=None):
 ss=[];fs=[]
 for i,(im,info) in enumerate(items if items is not None else ca.extract(source,n)[0]):
  assert not info['fullCanvasContact'],(key,i)
  a=np.asarray(im);ys,xs=np.where(a[:,:,3]>=240);bottom=int(ys.max())+1
  # Ground each complete object on its physical bottom; actor X uses boot support.
  ax=float(np.median(xs[ys>=bottom-4]));anchor=[ax+24,bottom+24]
  padded=Image.new('RGBA',(im.width+48,im.height+48));padded.alpha_composite(im,(24,24))
  file=f'frames/{key}-{i}.png';padded.save(O/file)
  sf={'file':file,'source':source.relative_to(O).as_posix(),'anchor':anchor,'scale':unit,'roi':info['roi'],'rootKind':'actual boot / stone base support'}
  ff,meta=ca.canonical_fit(padded,anchor,unit,palette,f'{key}-{i}')
  fit=Image.open(O/ff['file']);ff['anchor'][1]=fit.getbbox()[3]
  ss.append(sf);fs.append(ff);audit.append({'key':key,'frame':i,'sourceCanvasContact':False,'rectangles':ff['rectangles'],'reconstructionExact':True,'sourceAnchor':anchor,'fitAnchor':ff['anchor']})
 return ss,fs
tea=ca.extract(src,6)[0];unit=315/float(np.median([im.height-8 for im,_ in tea]))
ss,fs=make(src,6,'victory-tea-v9',unit)
v=bank['胜利'];v.update(sourceFrames=ss,frames=fs,initialFrames=fs,durations=[14,12,22,22,14,24],phases=['端杯与托碟','举杯至唇边','入口饮茶','停留品茶','放下茶杯','持杯胜利'],status='V9用户反馈修订：明确茶杯、托碟与入口动作；候选待美术验收')
pillar=Image.open(O/'sources/pillarFx.png').convert('RGBA')
# Visually verified source-local regions include detached stone fragments and
# the complete lower-left top above the old equal-row boundary.
boxes=[(240,295,580,435),(975,140,1270,435),(250,480,630,955),(930,525,1330,965)]
items=[(pillar.crop(box),{'roi':list(box),'fullCanvasContact':False}) for box in boxes]
ss,fs=make(O/'sources/pillarFx.png',4,'pillar-ground-v9',.64,items)
e=bank['E · 地心']['effects'];e.update(sourceFrames=ss,fitFrames=fs,frames=fs,worldOffset=[205,0],groundAnchorFixed=True)
# Calibrate E body too: old frame 2 X was the extreme right edge, not support feet.
for mode in ['sourceFrames','initialFrames','frames']:
 for f in bank['E · 地心'][mode]:
  im=Image.open(O/f['file']);a=np.asarray(im);ys,xs=np.where(a[:,:,3]>=240);bottom=int(ys.max())+1
  f['anchor']=[float(np.median(xs[ys>=bottom-4])),bottom]
bank['E · 地心']['status']='V9岩脊完整轮廓提取与地面锚点修订；E身体支撑脚校准，时序与判定设计保留'
(O/'actions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf8')
s=(H/'app.js').read_text(encoding='utf8').replace('let xx=410+e.worldOffset[0],yy=550+e.worldOffset[1];','let xx=x+e.worldOffset[0],yy=550+e.worldOffset[1];')
(O/'app.js').write_text(s,encoding='utf8')
for name,ident in [('offline.html','actionData'),('size-review.html','data')]:
 s=(H/name).read_text(encoding='utf8');s=re.sub(r'(<script[^>]*id="'+ident+r'"[^>]*>).*?(</script>)',lambda m:m[1]+json.dumps(bank,ensure_ascii=False)+m[2],s,flags=re.S)
 if name=='offline.html':s=re.sub(r'(<script>).*?(</script>)',lambda m:m[1]+(O/'app.js').read_text(encoding='utf8')+m[2],s,flags=re.S)
 (O/name).write_text(s,encoding='utf8')
(O/'feedback-fix-20261014.json').write_text(json.dumps({'version':'V9','scope':'independent preview candidate','audit':audit,'victoryStates':6,'pillarStates':4,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf8')
print('Updated tea 6, pillar 4; unit',unit)
