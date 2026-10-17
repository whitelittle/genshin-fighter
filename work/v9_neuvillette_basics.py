"""Add two movement source sheets to an independent V9 candidate; keep old assets."""
from pathlib import Path
import json,sys,hashlib,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import clorinde_assets as ca
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013/neuvillette';ca.O=O
palette=json.loads((O/'palette.json').read_text(encoding='utf-8'));bank=json.loads((O/'actions.json').read_text(encoding='utf-8'));audit=[]
plans=[('jump',6,.43,[6,8,8,8,8,8],['屈膝预蹲','蹬地起跳','上升收腿','顶点稳身','下降伸腿','双脚落地']),('forwarddash',4,.40,[4,6,6,8],['前倾准备','后脚推地','低位行进','前脚制动'])]
for key,n,unit,durations,phases in plans:
 source=O/f'source/{key}-v1-20261013.png';items,fragments=ca.extract(source,n);sources=[];fits=[]
 for i,(im,info) in enumerate(items):
  # Grounded pivot uses boot support; flight uses the same virtual standing root.
  a=np.asarray(im);ys,xs=np.where(a[:,:,3]>=250);bottom=int(ys.max());support=xs[ys>=bottom-3]
  ax=float(np.median(support));ay=float(bottom)
  if key=='jump' and i in [1,2,3,4]:
   face=ca.face_box(im)
   # Explicit body-relative virtual floor for preview; not a fitted box bottom.
   ax=(face[0]+face[2])/2-12/unit;ay=(face[1]+face[3])/2+204/unit
  padded=Image.new('RGBA',(im.width+64,im.height+64));padded.alpha_composite(im,(32,32));anchor=[ax+32,ay+32]
  file=f'frames/{key}-v9-{i}.png';padded.save(O/file)
  sf={'file':file,'source':source.relative_to(O).as_posix(),'sourceOrigin':[info['sourceOrigin'][0]-32,info['sourceOrigin'][1]-32],'anchor':anchor,'scale':unit,'roi':info['roi'],'sourceHash':hashlib.sha256(source.read_bytes()).hexdigest(),'anchorStatus':'manual provisional boot support / virtual standing root; preview only'}
  ff,meta=ca.canonical_fit(padded,anchor,unit,palette,f'{key}-v9-{i}')
  sources.append(sf);fits.append(ff);audit.append({'action':key,'frame':i,'rectangles':ff['rectangles'],'sourceRGBAUnchanged':True,'pixelReconstruction':True,'unit':unit,'anchor':anchor,'sourceCanvasContact':info['fullCanvasContact']})
 if key=='forwarddash':
  for target in [sources,fits]:target.insert(0,dict(bank['idle']['sourceFrames' if target is sources else 'frames'][0]));target.append(dict(target[0]))
  durations=[4]+durations+[4];phases=['待机连接']+phases+['回待机']
 bank[key]={'label':'跳跃' if key=='jump' else '前冲','frames':fits,'sourceFrames':sources,'durations':durations,'phases':phases,'events':[],'motion':{'kind':'jump' if key=='jump' else 'dash','distance':0 if key=='jump' else 108,'direction':1,'height':112 if key=='jump' else 0},'status':'V9新增源板与拟合候选；人体/杖长/握点/支撑/动作衔接待美术复验，未接正式战斗'}
(O/'actions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'action-data.js').write_text('window.NEUVILLETTE_ACTIONS='+json.dumps(bank,ensure_ascii=False)+';',encoding='utf-8')
(O/'v9-basics-verification.json').write_text(json.dumps({'version':'V9','candidate':True,'newGroups':2,'newBodySources':10,'actions':len(bank),'displayStates':sum(len(g['frames']) for g in bank.values()),'audit':audit,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf-8')
page=O/'player.html';s=page.read_text(encoding='utf-8').replace('第三批累计10组/49显示状态候选','V9累计12组/61显示状态候选');page.write_text(s,encoding='utf-8')
print('V9 Neuvillette',len(bank),'groups',sum(len(g['frames']) for g in bank.values()),'states,',max(x['rectangles'] for x in audit),'new frame peak')
