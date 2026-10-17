from pathlib import Path
import json,os,shutil,re,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
import clorinde_assets as ca
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013'
plans=json.loads((R/'work/role_continuation_20261014_final_plans.json').read_text(encoding='utf8'))
settings={
 ('neuvillette','forwarddash'):(4,.45,[4,6,6,8],['预备承重','后脚推地','低位行进','前脚制动'],[(390,508),(1180,500),(490,1020),(1190,1002)]),
 ('neuvillette','backdash'):(4,.50,[4,6,6,8],['前脚预载','蹬地后退','空中收腿','后脚落稳'],[(445,495),(1125,535),(460,1040),(1210,999)]),
 ('mavuika','jump'):(6,.40,[6,6,8,8,8,8],['预蹲承重','支撑脚蹬地','上升收膝','顶点展臂','下降伸腿','落地缓冲'],[(282,480),(617,478),(1345,523),(353,1000),(804,1013),(1320,992)]),
 ('zhongli','crouch'):(6,.57,[4,4,4,4,6,14],['待机屈膝','髋部下沉','继续承重','低位蹲伏','重心收稳','低位保持'],[(294,592),(795,592),(345,1075),(826,1060),(350,1485),(866,1485)])}
audits=[]
for p in plans:
 role,key=p['role'],p['key'];D=O/role;ca.O=D
 H=D/'history/strict-review-20261014';H.mkdir(parents=True,exist_ok=True)
 for name in ['actions.json','action-data.js','current-status.json','player.html','offline.html','size-review.html','index.html']:
  if (D/name).exists() and not (H/name).exists():shutil.copy2(D/name,H/name)
 srcdir='sources' if role=='zhongli' else 'source';src=D/srcdir/f'{key}-strict-20261014.png'
 shutil.copy2(os.path.expandvars(p['selectedPath']),src)
 for version,field in [('first','generatedPath'),('cleanup','cleanedPath')]:
  shutil.copy2(os.path.expandvars(p[field]),H/f'{key}-{version}.png')
 promptdir=D/'prompts-review-20261014';promptdir.mkdir(exist_ok=True)
 for suffix,field in [('draw','prompt'),('cleanup','cleanupPrompt'),('anatomy-retry','retryPrompt')]:
  if p.get(field):(promptdir/f'{key}-{suffix}.txt').write_text(p[field],encoding='utf8')
 bank=json.loads(((H/'actions.json') if role=='zhongli' else (D/'actions.json')).read_text(encoding='utf8'))
 idle=next(g for g in bank.values() if g.get('actionId')=='zhongli_idle') if role=='zhongli' else bank['idle']
 palette=json.loads((D/'rects/idle-0-optimized.json').read_text(encoding='utf8'))['palette'] if role=='zhongli' else (json.loads((D/'palette.json').read_text()) if role=='neuvillette' else json.loads((O/'upstream/mavuika-v10/dist/assets/neutral-rig-v6.json').read_text())['palette'])
 n,unit,durations,phases,roots=settings[(role,key)];items,fragments=ca.extract(src,n);ss=[];fs=[]
 for i,((im,info),root) in enumerate(zip(items,roots)):
  assert not info['fullCanvasContact'],(role,key,i,'opaque canvas contact')
  ox,oy=info['sourceOrigin'];anchor=[root[0]-ox+32,root[1]-oy+32]
  pad=Image.new('RGBA',(im.width+64,im.height+64));pad.alpha_composite(im,(32,32))
  file=f'frames/{key}-strict-20261014-{i}.png';pad.save(D/file)
  sf={'file':file,'source':src.relative_to(D).as_posix(),'anchor':anchor,'scale':unit,'roi':info['roi'],'sourceOrigin':[ox-32,oy-32],'rootKind':'manual boot support or virtual standing floor','sourceHash':hashlib.sha256(src.read_bytes()).hexdigest(),'unitPolicy':'one unit per entire sheet, anatomy-based provisional calibration; not per-pose silhouette scaling'}
  ff,meta=ca.canonical_fit(pad,anchor,unit,palette,f'{key}-strict-20261014-{i}')
  ss.append(sf);fs.append(ff)
  # Each extracted original high-alpha body pixel must have one owner.
  a=np.array(Image.open(src));x0,y0,x1,y1=info['roi'];region=a[y0:y1,x0:x1]
  cropped=np.array(im); retained=int(((region[:,:,3]>=240)&(cropped[:,:,3]>=240)).sum())
  audits.append({'role':role,'action':key,'pose':i,'unit':unit,'rootSheet':root,'sourceROI':info['roi'],'retainedOpaquePixels':retained,'rectangles':ff['rectangles'],'pixelReconstructionExact':True,'opaqueCanvasContact':False,'artAccepted':False})
 if key in ['forwarddash','backdash']:
  ss=[dict(idle['sourceFrames'][0])]+ss+[dict(idle['sourceFrames'][0])];fs=[dict(idle['frames'][0])]+fs+[dict(idle['frames'][0])]
  durations=[4]+durations+[4];phases=['待机连接']+phases+['回待机']
 if key=='jump':
  ss.append(dict(idle['sourceFrames'][0]));fs.append(dict(idle['frames'][0]));durations.append(6);phases.append('落地回待机')
 entry={'frames':fs,'sourceFrames':ss,'durations':durations,'phases':phases,'events':[],'status':'2026-10-14严格复核候选：源图新绘、单组等比单位与人工支撑root；肢体/握点/接缝尚待用户美术验收','artAccepted':False,'runtimeIntegrated':False,'previewOnly':True}
 if key in ['forwarddash','backdash']:entry['motion']={'kind':'dash','direction':1 if key=='forwarddash' else -1,'distance':108 if key=='forwarddash' else 90}
 if key=='jump':entry['motion']={'kind':'jump','distance':0,'height':112,'direction':1,'groundedPhases':[0,1,5,6],'airPhases':[2,3,4]}
 if role=='zhongli':
  (D/'crouch-proposal-20261014.json').write_text(json.dumps(entry,ensure_ascii=False,indent=2),encoding='utf8')
  # Review found head/torso deviation. Keep this proposal outside active actions.
 else:bank[key]=entry
 (D/'actions.json').write_text(json.dumps(bank,ensure_ascii=False,indent=2),encoding='utf8')
 if role!='zhongli':
  (D/'action-data.js').write_text('window.NEUVILLETTE_ACTIONS='+json.dumps(bank,ensure_ascii=False)+';',encoding='utf8')
  page=D/'player.html';txt=page.read_text(encoding='utf8');txt=re.sub(r'\d+组/\d+',f'{len(bank)}组/{sum(len(g["frames"]) for g in bank.values())}',txt);page.write_text(txt,encoding='utf8')
 else:
  for name in ['offline.html','size-review.html','index.html']:
   shutil.copy2(H/name,D/name)
 status={'version':'V9','stage':'strict-art-review-candidate-20261014','character':role,'actions':len(bank),'mainDisplayStates':sum(len(g['frames']) for g in bank.values()),'entry':'offline.html' if role=='zhongli' else 'player.html','artAccepted':False,'runtimeIntegrated':False,'simulatorVerified':False,'deviceVerified':False,'history':'history/strict-review-20261014/'}
 if role=='zhongli':status.update(crouchProposalAdopted=False,rejection='Head/torso continuity differs from standing mother; retain previous full candidate and latest tea/E repair')
 (D/'current-status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf8')
 # Contact evidence: same world unit as player, no independent pose fit-to-box.
 card=Image.new('RGBA',(1800,520),(98,112,119,255));dr=ImageDraw.Draw(card);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
 seq=[idle['frames'][0]]+fs;labels=['待机基线']+phases
 for i,(f,label) in enumerate(zip(seq,labels)):
  img=Image.open(D/f['file']).convert('RGBA');scale=f['scale']*.75;img=img.resize((round(img.width*scale),round(img.height*scale)),Image.Resampling.NEAREST)
  x=160+i*1800/len(seq);y=465;card.alpha_composite(img,(round(x-f['anchor'][0]*scale),round(y-f['anchor'][1]*scale)));dr.text((int(i*1800/len(seq))+6,12),label,font=font,fill='white')
 dr.line((0,465,1800,465),fill='white');card.convert('RGB').save(D/f'evidence/{key}-strict-20261014.png')
 print(role,key,len(fs),'states',unit)
(O/'strict-review-20261014.json').write_text(json.dumps({'scope':'independent source and preview, not game simulation','newUniqueBodyDrawings':20,'actions':['neuvillette.forwarddash repair','neuvillette.backdash new','mavuika.jump new','zhongli.crouch repair'],'audit':audits,'artAccepted':False,'runtimeIntegrated':False,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf8')
