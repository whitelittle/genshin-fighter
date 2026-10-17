"""Rebuild only the independent Neuvillette first-batch candidate from saved sources."""
from pathlib import Path
import json, hashlib, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import clorinde_assets as ca

R=Path(__file__).resolve().parents[1]
O=R/'outputs/neuvillette-actions-20261012'
ca.O=O
audit=[]
palette=ca.artlib.build_palette([ca.artlib.downscale(Image.open(O/'source/mother-v2.png').convert('RGBA'),.06)],16,seed=31)+[[246,213,197],[239,237,245],[16,22,37]]
fxpalette=ca.artlib.build_palette([ca.artlib.downscale(Image.open(O/'source/torrent-fx-v1.png').convert('RGBA'),.04)],7,seed=21)+[[21,108,182]]
(O/'palette.json').write_text(json.dumps(palette),encoding='utf-8')

def extract(file,n,base,scale,roots,pal):
    items,fragments=ca.extract(O/file,n)
    sources=[];fits=[]
    for i,(im,info) in enumerate(items):
        ox,oy=info['sourceOrigin'];ax,ay=roots[i]
        # Padding changes storage only, never the drawing unit or source anatomy.
        padded=Image.new('RGBA',(im.width+64,im.height+64));padded.alpha_composite(im,(32,32))
        fn=f'frames/{base}-{i}.png';padded.save(O/fn)
        anchor=[ax-ox+32,ay-oy+32]
        source={'file':fn,'source':file,'sourceOrigin':[ox-32,oy-32],'roi':info['roi'],'anchor':anchor,'scale':scale,'extraction':info['extractionMethod'],'sourceHash':hashlib.sha256((O/file).read_bytes()).hexdigest()}
        fitted,meta=ca.canonical_fit(padded,anchor,scale,pal,f'{base}-{i}')
        a=np.array(padded);raw=np.array(Image.open(O/file).convert('RGBA'))
        # Every retained source pixel has unchanged RGBA. No hole recovery from adjacent poses.
        crop=raw[info['roi'][1]:info['roi'][3],info['roi'][0]:info['roi'][2]]
        inner=a[32:-32,32:-32];m=inner[:,:,3]>0
        assert np.array_equal(inner[m],crop[m])
        assert not np.any(a[[0,-1],:,3]) and not np.any(a[:,[0,-1],3])
        audit.append({'file':fn,'rectangles':fitted['rectangles'],'originalRetainedRGBA':True,'storageBorderClear':True,'sourceCanvasContact':info['fullCanvasContact'],'fragments':fragments})
        sources.append(source);fits.append(fitted)
    return sources,fits

sf,ff=extract('source/mother-v2.png',1,'idle-open',.25,[[835,979]],palette)
si,fi=extract('source/idle-inhale-v1.png',1,'idle-inhale',.25,[[835,979]],palette)
hs,hf=extract('source/heavy-held-cane-v1.png',4,'heavy',.47,[[520,510],[1110,516],[520,1000],[1110,1008]],palette)
actions={
 'idle':{'label':'待机','sourceFrames':sf+si,'frames':ff+fi,'durations':[48,12],'phases':['呼吸保持','半眨眼吸气'],'events':[],'status':'两姿候选；脚底/杖尖/体型与循环需用户复核'},
 'heavy':{'label':'站重 · 洪流小样','sourceFrames':[sf[0]]+hs+[sf[0]],'frames':[ff[0]]+hf+[ff[0]],'durations':[4,10,8,18,16,8],'phases':['待机连接','收杖聚势','举掌聚流','推流保持','收掌回杖','回待机'],'events':[{'tick':22+i*6,'kind':'torrent-hit','hitId':f'heavy-{i+1}','status':'design only'} for i in range(3)],'status':'持杖单掌候选；不同于双手收杖版本，尚未动作/逻辑验收','palmBinding':{'frameIndex':3,'point':[708-hs[2]['sourceOrigin'][0],625-hs[2]['sourceOrigin'][1]],'coordinateSpace':'extracted source pixels'},'activeTicks':[22,40]}
}
es,ef=extract('source/torrent-fx-v1.png',3,'torrent',.17,[[75,170],[75,425],[75,675]],fxpalette)
effects={f'torrent{i}':{'source':s,'fit':f} for i,(s,f) in enumerate(zip(es,ef))}
if (O/'source/walk-v1.png').exists():
 ws,wf=extract('source/walk-v1.png',6,'walk',.47,[[305,500],[790,506],[1250,504],[325,1001],[805,1007],[1265,1005]],palette)
 bs,bf=extract('source/backwalk-v2.png',6,'backwalk',.54,[[315,476],[785,480],[325,968],[815,966],[325,1457],[815,1461]],palette)
 ls,lf=extract('source/light1-v1.png',4,'light1',.46,[[500,510],[1100,511],[480,1015],[1100,1015]],palette)
 actions['walk']={'label':'前走','sourceFrames':ws,'frames':wf,'durations':[7]*6,'phases':['前脚接触','承重下降','收腿经过','交替接触','交替承重','交替经过'],'events':[],'motion':{'kind':'walk','direction':1,'distance':76},'status':'六相新候选；前后腿支撑身份、落脚滑动与循环待美术复核'}
 actions['backwalk']={'label':'后退','sourceFrames':bs,'frames':bf,'durations':[8]*6,'phases':['向后探步','转移承重','收脚经过','交替探步','交替承重','交替经过'],'events':[],'motion':{'kind':'walk','direction':-1,'distance':62},'status':'独立后退六相v2；顶部边距已返修；向后落脚/支撑和循环仍待复核'}
 actions['light1']={'label':'轻1 · 短掌波','sourceFrames':ls+[sf[0]],'frames':lf+[ff[0]],'durations':[4,4,3,13,4],'phases':['回腕准备','送掌出手','短掌波有效','收肘回杖','回待机'],'events':[{'tick':8,'kind':'palmwave-hit','hitId':'light1-1','status':'design only'}],'activeTicks':[8,11],'palmBinding':{'frameIndex':2,'point':[668-ls[2]['sourceOrigin'][0],618-ls[2]['sourceOrigin'][1]],'coordinateSpace':'extracted source pixels'},'status':'轻1身体四姿与独立短掌波候选；握点/收势/手部与判定未验收'}
 wavePalette=ca.artlib.build_palette([ca.artlib.downscale(Image.open(O/'source/lightwave-v1.png').convert('RGBA'),.04)],7,seed=21)+[[21,108,182]]
 waveS,waveF=extract('source/lightwave-v1.png',1,'lightwave',.075,[[326,451]],wavePalette)
 effects['lightwave']={'source':waveS[0],'fit':waveF[0]}
if (O/'source/crouchguard-v2.png').exists():
 plans=[
  ('light2','light2-v1',.47,[[490,505],[1100,505],[500,1010],[1095,1010]],[4,6,3,15,4],['托掌准备','上托聚珠','前送释放','收臂回杖','回待机']),
  ('light3','light3-v2',.47,[[480,504],[1170,507],[475,1005],[1160,1005]],[6,6,4,18,4],['回臂蓄势','重心跟进','压掌有效','制动收臂','回待机']),
  ('crouch','crouch-v2',.40,[[490,585],[1110,585],[475,1006],[1130,1003]],[4,4,6,18],['屈膝','下沉','低位稳身','蹲姿保持']),
  ('standguard','standguard-v1',.45,[[520,528],[1125,527],[515,997],[1110,1006]],[4,10,8,6,4],['抬臂','站立防护','承压','收臂回杖','回待机']),
  ('crouchguard','crouchguard-v2',.34,[[515,504],[1160,505],[495,990],[1150,990]],[4,10,8,6,6],['低位抬臂','低位防护','低位承压','回收前臂','回蹲姿'])]
 for key,base,unit,roots,durations,phases in plans:
  ss,fs=extract(f'source/{base}.png',4,base,unit,roots,palette)
  if key!='crouch':
   end=actions['crouch'] if key=='crouchguard' else actions['idle'];ei=3 if key=='crouchguard' else 0
   ss.append(end['sourceFrames'][ei]);fs.append(end['frames'][ei])
  actions[key]={'label':key,'sourceFrames':ss,'frames':fs,'durations':durations,'phases':phases,'events':[],'status':'第三批新候选；体型/握点/支撑/衔接待复核，未接正式判定'}
 for key,ticks,point in [('light2',[10,20],[700,608]),('light3',[12,16],[718,640])]:
  f=actions[key]['sourceFrames'][2]
  actions[key].update({'activeTicks':ticks,'palmBinding':{'frameIndex':2,'point':[point[0]-f['sourceOrigin'][0],point[1]-f['sourceOrigin'][1]]},'events':[{'tick':ticks[0],'kind':key+'-hit','hitId':key+'-1','status':'design only'}]})
 for key,points in [('standguard',[[636,109],[1200,112],[610,612],[1170,714]]),('crouchguard',[[588,237],[1240,146],[583,662],[1250,735]])]:
  actions[key]['guardBindings']=[{'point':[p[0]-f['sourceOrigin'][0],p[1]-f['sourceOrigin'][1]]} for p,f in zip(points,actions[key]['sourceFrames'])]
  actions[key]['guardTicks']=[4,22]
 newPal=ca.artlib.build_palette([ca.artlib.downscale(Image.open(O/'source/orb-guard-fx-v1.png').convert('RGBA'),.04)],8,seed=21)+[[21,108,182]]
 ns,nf=extract('source/orb-guard-fx-v1.png',2,'orb-guard',.10,[[510,320],[430,1095]],newPal)
 for key,s,f in zip(['orb','guard'],ns,nf):effects[key]={'source':s,'fit':f}
for name,value in [('actions',actions),('effects',effects)]:
 (O/f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/f'{"action" if name=="actions" else "effect"}-data.js').write_text(f'window.NEUVILLETTE_{"ACTIONS" if name=="actions" else "FX"}='+json.dumps(value,ensure_ascii=False)+';',encoding='utf-8')
fxfiles={v['source']['file'] for v in effects.values()}
body=[a['rectangles'] for a in audit if a['file'] not in fxfiles]
report={'candidate':True,'actions':len(actions),'uniqueBodyImages':len(body),'mainDisplayStates':sum(len(d['frames']) for d in actions.values()),'uniqueEffectImages':len(effects),'rectReconstruction':'exact quantized target; asserted during fitting','bodyPeak':max(body),'effectPeak':max(a['rectangles'] for a in audit if a['file'] in fxfiles),'artAccepted':False,'runtimeIntegrated':False,'simulatorVerified':False,'deviceVerified':False,'audit':audit}
if (O/'browser-initial.json').exists():
 browser=json.loads((O/'browser-initial.json').read_text(encoding='utf-8'))
 assert len(browser['checks'])==16 and all(c['ready'] for c in browser['checks'])
 report['browserEvidence']='browser-initial.json; 16 pose-material states and mirrored full torrent at tick28; independent preview only'
if (O/'browser-batch2.json').exists():
 browser=json.loads((O/'browser-batch2.json').read_text(encoding='utf-8'))
 assert len(browser['checks'])==50 and all(c['ready'] for c in browser['checks'])
 for c in browser['fxBoundary']:
  assert (c['effect']=='lightwave')==(8<=c['time']<11)
 extra=browser['extra'];assert extra[1]['root'][0]==460 and extra[2]['root'][0]>460
 assert extra[3]['root'][0]==460 and extra[4]['root'][0]<460
 report['browserBatch2']='50 current pose-material states; 10 lightwave boundary states; mirror and walk/backwalk movement switches; independent browser only'
if (O/'browser-batch3.json').exists():
 browser=json.loads((O/'browser-batch3.json').read_text(encoding='utf-8'))
 assert len(browser['checks'])==48 and all(c['ready'] for c in browser['checks'])
 assert len(browser['boundaries'])==32
 for c in browser['boundaries']:
  begin,end={'light2':(10,20),'light3':(12,16),'standguard':(4,22),'crouchguard':(4,22)}[c['selected']]
  assert (c['effect'] is not None)==(begin<=c['time']<end)
 report['browserBatch3']='48 new pose-material states; 32 attack/guard effect boundary states; mirrored FX-off silhouette observed; independent browser only'
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

# World-space evidence uses the declared units, never per-pose bbox normalization.
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
board=Image.new('RGBA',(1600,600),(245,247,250,255));d=ImageDraw.Draw(board)
for col,bg in enumerate([(245,247,250,255),(30,33,48,255)]):
 panel=Image.new('RGBA',(800,600),bg);pd=ImageDraw.Draw(panel)
 pd.line((20,520,780,520),fill=(130,145,165),width=1)
 for k,f in enumerate([sf[0],ff[0]]):
  im=Image.open(O/f['file']).convert('RGBA');s=f['scale']*1.65
  im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.LANCZOS if k==0 else Image.Resampling.NEAREST)
  panel.alpha_composite(im,(round(250+k*380-f['anchor'][0]*s),round(520-f['anchor'][1]*s)))
 pd.text((20,20),'母版源图 / 拟合：同世界尺度，候选',font=font,fill=(90,100,115) if col==0 else (235,240,250));board.alpha_composite(panel,(col*800,0))
board.convert('RGB').save(O/'evidence/mother-world-light-dark.jpg')
frames=[]
for i in [0,1,2,3,3,3,4,5]:
 c=Image.new('RGBA',(1000,500),(245,247,250,255));ImageDraw.Draw(c).line((20,430,980,430),fill=(170,180,195))
 f=actions['heavy']['frames'][i];im=Image.open(O/f['file']).convert('RGBA');s=f['scale']*1.4
 c.alpha_composite(im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST),(round(350-f['anchor'][0]*s),round(430-f['anchor'][1]*s)))
 if i==3:
  f=effects['torrent1']['fit'];im=Image.open(O/f['file']).convert('RGBA');s=f['scale']*1.4
  b=actions['heavy']['palmBinding'];src=actions['heavy']['sourceFrames'][3]
  px=350+(b['point'][0]-src['anchor'][0])*src['scale']*1.4;py=430+(b['point'][1]-src['anchor'][1])*src['scale']*1.4
  c.alpha_composite(im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST),(round(px-f['anchor'][0]*s),round(py-f['anchor'][1]*s)))
 frames.append(c.convert('RGB'))
frames[0].save(O/'evidence/heavy-fit-preview.gif',save_all=True,append_images=frames[1:],duration=[120,200,150,120,120,120,250,200],loop=0)
manifest={'candidate':True,'tool':'built-in image_gen; local extraction/fitting only','files':[]}
for p in sorted(O.rglob('*')):
 if p.is_file() and p.name!='manifest.json':manifest['files'].append({'path':p.relative_to(O).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='audit'},ensure_ascii=False))
