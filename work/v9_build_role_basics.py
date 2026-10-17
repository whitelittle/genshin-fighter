"""Independent V9 previews: preserved upstream pixels plus explicitly new poses."""
from pathlib import Path
import json,shutil,sys,hashlib,re
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import clorinde_assets as ca
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013';U=O/'upstream'
def sole(im):
 a=np.asarray(im.convert('RGBA'));yy,xx=np.where(a[:,:,3]>=250)
 return int(yy.max())+1
def templates(folder,title,count,states):
 for file in ['player.css','player.html','player.js']:
  s=(O/'neuvillette'/file).read_text(encoding='utf-8')
  if file=='player.html':
   s=s.replace('那维莱特',title).replace('12组/61',f'{count}组/{states}').replace('体型返修对照','动作记录').replace('evidence/mother-world-light-dark.jpg','current-status.json')
  if file=='player.js':
   s=s.replace("fx=window.NEUVILLETTE_FX","fx=window.NEUVILLETTE_FX||{}")
   s=s.replace("selected==='light1'&&$('fx').checked","selected==='light1'&&fx.lightwave&&$('fx').checked")
   s=s.replace('轻1 · 短掌波','轻1').replace('站重 · 洪流小样','站重')
   # Keep the actor independent; this generic review does not synthesize effects.
  (folder/file).write_text(s,encoding='utf-8')
M=O/'mavuika';A=U/'mavuika-v10/dist/assets';M.mkdir(exist_ok=True)
for name in ['source','frames','fit','evidence']: (M/name).mkdir(exist_ok=True)
ca.O=M;rig=json.loads((A/'neutral-rig-v6.json').read_text(encoding='utf-8'));palette=rig['palette'];bank={};checks=[]
for key,g in rig['groups'].items():
 source=Image.open(A/g['source']).convert('RGBA');optimized=Image.open(A/g['optimized']).convert('RGBA')
 shutil.copy2(A/g['source'],M/'source'/g['source'])
 rects=json.loads((A/f'{key}-optimized-rects-v6.json').read_text(encoding='utf-8'));ss=[];fs=[]
 for i,p in enumerate(g['poses']):
  x,y,w,h=p['sourceRect'];im=source.crop((x,y,x+w,y+h));sf=f'frames/{key}-{i}-source.png';im.save(M/sf)
  ax,ay,rw,rh=p['atlasRect'];fit=optimized.crop((ax,ay,ax+rw,ay+rh));fn=f'fit/{key}-{i}.png';fit.save(M/fn)
  original=rects['poses'][i];rebuild=np.zeros((rh,rw,4),dtype='uint8')
  for xx,yy,ww,hh,c in original['rects']:rebuild[yy:yy+hh,xx:xx+ww]=rects['palette'][c][:3]+[255]
  assert np.array_equal(np.asarray(fit),rebuild),(key,i)
  sy=sole(im);fy=sole(fit)
  ss.append({'file':sf,'source':'source/'+g['source'],'anchor':[p['sourceAnchor'][0],sy],'scale':g['displayScale'],'roi':p['sourceRect']})
  fs.append({'file':fn,'anchor':[p['anchor'][0],fy],'scale':4,'rectangles':len(original['rects'])})
  (M/Path(fn).with_suffix('.json')).write_text(json.dumps({'palette':rects['palette'],'rects':original['rects']},ensure_ascii=False),encoding='utf-8')
  checks.append({'group':key,'frame':i,'upstreamPixelsExact':True,'oldSourceAnchorY':p['sourceAnchor'][1],'sourceSoleY':sy,'oldFitAnchorY':p['anchor'][1],'fitSoleY':fy})
 ds=[30,30] if key=='idle' else [7]*6 if key=='walk' else [8]*6 if key=='backwalk' else [4,4,3,13]
 bank[key]={'frames':fs,'sourceFrames':ss,'durations':ds,'phases':[f'姿势{i+1}' for i in range(len(fs))],'events':[],'status':'上游v6基础动作；V9保留像素、修正实际鞋底锚点，人体/步态仍待美术复验'}
 if key in ['walk','backwalk']:bank[key]['motion']={'kind':'walk','direction':1 if key=='walk' else -1,'distance':70}
new=[]
for key,path,unit,ds,phases in [('crouch','crouch-v9-2.png',.34,[4,6,8,18],['屈膝准备','重心下沉','低位防守','蹲姿保持']),('standguard','standguard-v9-2.png',.42,[4,12,8,8],['抬臂准备','站立防护','承压回收','收臂恢复'])]:
 items,fr=ca.extract(M/'source'/path,4);ss=[];fs=[]
 for i,(im,info) in enumerate(items):
  assert not info['fullCanvasContact'],(key,i,'source edge contact')
  a=np.asarray(im);yy,xx=np.where(a[:,:,3]>=250);y=yy.max()+1;x=float(np.median(xx[yy>=yy.max()-3]))
  padded=Image.new('RGBA',(im.width+64,im.height+64));padded.alpha_composite(im,(32,32));anchor=[x+32,float(y+32)];fn=f'frames/{key}-v9-{i}.png';padded.save(M/fn)
  ff,meta=ca.canonical_fit(padded,anchor,unit,palette,f'{key}-v9-{i}')
  # Ground the quantized perimeter at its actual sole, matching the reference.
  fitted=Image.open(M/ff['file']);ff['anchor'][1]=sole(fitted)
  ss.append({'file':fn,'source':'source/'+path,'anchor':anchor,'scale':unit,'sourceOrigin':[info['sourceOrigin'][0]-32,info['sourceOrigin'][1]-32],'roi':info['roi']});fs.append(ff)
  new.append({'group':key,'frame':i,'sourceCanvasContact':False,'rectangles':ff['rectangles'],'pixelReconstruction':True})
 if key=='standguard':
  ss.append(dict(bank['idle']['sourceFrames'][0]));fs.append(dict(bank['idle']['frames'][0]));ds.append(4);phases.append('回待机')
 bank[key]={'frames':fs,'sourceFrames':ss,'durations':ds,'phases':phases,'events':[],'status':'V9新增身体姿势候选；首稿裁边已返修，轮廓/体型/支持脚/首尾待美术复验'}
(M/'actions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf-8')
(M/'action-data.js').write_text('window.NEUVILLETTE_ACTIONS='+json.dumps(bank,ensure_ascii=False)+';',encoding='utf-8');(M/'effect-data.js').write_text('window.NEUVILLETTE_FX={};',encoding='utf-8')
(M/'current-status.json').write_text(json.dumps({'version':'V9','actions':len(bank),'displayStates':sum(len(g['frames']) for g in bank.values()),'upstreamNeutralGroups':4,'newGroups':['crouch','standguard'],'newBodySources':8,'sourceCommit':'f0ab595f216b627014ce7e0170a12412792d71e2','artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False,'soleChecks':checks,'newPoseChecks':new},ensure_ascii=False,indent=2),encoding='utf-8')
templates(M,'玛薇卡',len(bank),sum(len(g['frames']) for g in bank.values()))
Z=O/'zhongli'
if not Z.exists():shutil.copytree(U/'zhongli/full-actions',Z)
zbank=json.loads((Z/'actions.json').read_text(encoding='utf-8'));changes=[]
ground={'zhongli_idle','zhongli_walk','zhongli_backwalk','zhongli_crouch','zhongli_standguard','zhongli_crouchguard'}
for name,g in zbank.items():
 if g['actionId'] not in ground:continue
 for material in ['sourceFrames','initialFrames','frames']:
  for i,f in enumerate(g[material]):
   im=Image.open(Z/f['file']);old=f['anchor'][1];newY=sole(im);f['anchor'][1]=newY
   changes.append({'group':g['actionId'],'material':material,'frame':i,'oldY':old,'soleY':newY})
(Z/'actions.json').write_text(json.dumps(zbank,ensure_ascii=False,indent=2),encoding='utf-8')
p=Z/'app.js';app=p.read_text(encoding='utf-8');app=app.replace('shadow(x,550);if(',"shadow(x,550);if($('baseline').checked&&neutralFrames.length){const f=neutralFrames[0],im=neutralImages[0];ctx.imageSmoothingEnabled=false;ctx.drawImage(im,105-f.anchor[0]*f.scale,550-f.anchor[1]*f.scale,im.naturalWidth*f.scale,im.naturalHeight*f.scale)}if(")
app=app.replace("['body','fx'","['baseline','body','fx'")
p.write_text(app,encoding='utf-8')
p=Z/'offline.html';html=p.read_text(encoding='utf-8');html=html.replace('<label><input id="body"','<label><input id="baseline" type="checkbox" checked>待机对照</label><label><input id="body"')
html=re.sub(r'(<script[^>]*id="data"[^>]*>).*?(</script>)',lambda m:m[1]+json.dumps(zbank,ensure_ascii=False)+m[2],html,flags=re.S)
html=re.sub(r'<script>.*?</script>',lambda m:'<script>'+app+'</script>',html,flags=re.S)
p.write_text(html,encoding='utf-8')
(Z/'v9-basics-verification.json').write_text(json.dumps({'version':'V9','groups':25,'displayStates':sum(len(g['frames']) for g in zbank.values()),'sourcePixelsChanged':False,'groundAnchorChanges':changes,'EBody36TickTailPreserved':'function isNeutralTail' in app,'runtimeIntegrated':False,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('Mavuika',len(bank),'groups',sum(len(g['frames']) for g in bank.values()),'states; Zhongli',len(zbank),'groups,',len(changes),'ground anchor checks')
