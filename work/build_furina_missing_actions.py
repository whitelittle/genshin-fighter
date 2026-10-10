"""Extract reviewed action candidates and rebuild the original Furina review page.

Only offline image/preview production. No combat integration or device acceptance.
"""
from pathlib import Path
import argparse, json, math, shutil, hashlib, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from build_ayaka_attacks import extract
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
sys.path.insert(0,str(R/'game/tools'));import artlib
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
SOURCE_VERSIONS={'forwarddash':3,'backdash':5,'jump':3,'defeat':3}

def prepare():
 for key in ['forwarddash','backdash','jump','defeat']:
  source=O/f'{key}-source-v{SOURCE_VERSIONS[key]}.png'
  if not source.exists():continue
  count=6 if key=='jump' else 4
  records=extract(source,count)
  rois=[]
  for i,(roi,im,xs,ys) in enumerate(records):
   assert roi[0]>0 and roi[1]>0 and roi[2]<Image.open(source).width and roi[3]<Image.open(source).height,('atlas edge',key,i,roi)
   im.save(O/f'{key}-review-{i}.png');rois.append(list(roi))
  (O/f'{key}-extraction.json').write_text(json.dumps({'source':source.name,'sourceSha256':hashlib.sha256(source.read_bytes()).hexdigest(),'rois':rois,'poses':count,'anatomicalAcceptance':False},indent=2),encoding='utf-8')
  # Unscaled crops with coordinate guides, for manual landmark annotation.
  w=max(x[1].width for x in records)+20;h=max(x[1].height for x in records)+40
  sheet=Image.new('RGBA',(2*w,math.ceil(count/2)*h),'#777780');draw=ImageDraw.Draw(sheet)
  for i,(_,im,_,_) in enumerate(records):
   ox=(i%2)*w;oy=(i//2)*h+25;sheet.alpha_composite(im,(ox,oy));draw.text((ox,oy-23),f'{key} {i}: {im.width}×{im.height}',font=FONT,fill='white')
   for y in range(0,im.height,100):draw.line((ox,oy+y,ox+im.width,oy+y),fill='#ffffff55');draw.text((ox,oy+y),str(y),font=FONT,fill='white')
   for x in range(0,im.width,100):draw.line((ox+x,oy,ox+x,oy+im.height),fill='#ffffff55');draw.text((ox+x,oy+2),str(x),font=FONT,fill='white')
  sheet.convert('RGB').save(O/f'{key}-coordinate-review.jpg')
  print(key,rois)

def fitted(f,palette,name):
 im=Image.open(O/f['file']).convert('RGBA');ratio=f['scale']/4.5
 # Padding permits a one-cell outer contour without clipping hat or boots.
 small=artlib.downscale(im,ratio);idx=artlib.apply_palette(small,palette[:-1]);idx=np.pad(idx,1,constant_values=-1)
 mask=idx>=0;expanded=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
 edge=expanded&~mask;idx[edge]=len(palette)-1
 rects=artlib.painter(idx);pix=np.zeros((*idx.shape,4),dtype=np.uint8)
 for x,y,w,h,c in rects:pix[y:y+h,x:x+w]=palette[c][:3]+[255]
 expected=np.zeros_like(pix)
 for c,color in enumerate(palette):expected[idx==c]=color[:3]+[255]
 assert np.array_equal(expected,pix)
 Image.fromarray(pix).save(O/name)
 rx=small.width/im.width;ry=small.height/im.height
 fit={**f,'file':name,'anchor':[f['anchor'][0]*rx+1,f['anchor'][1]*ry+1],'scale':4.5,'scaleX':f['scale']/rx,'scaleY':f['scale']/ry}
 record={'palette':palette,'rects':rects,'anchor':fit['anchor'],'scale':4.5,'scaleX':fit['scaleX'],'scaleY':fit['scaleY'],'source':f['file'],'outline':'external one logical cell with padded canvas','reconstruction':'quantized target exact','runtimeIntegrated':False}
 (O/(Path(name).stem+'-rects.json')).write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
 return fit,len(rects)

def marker_from_contact(f,xy):
 im=Image.open(O/f['file']).convert('RGBA');b=im.getbbox();ratio=min(210/(b[2]-b[0]),240/(b[3]-b[1]))
 return [(xy[0]-10)/ratio+b[0],(xy[1]-35)/ratio+b[1]]

def build():
 cfg=json.loads((O/'missing-action-landmarks.json').read_text(encoding='utf-8'))
 baseline=O/'actions-before-missing-20261011.json'
 if not baseline.exists():shutil.copy2(O/'actions.json',baseline)
 data=json.loads(baseline.read_text(encoding='utf-8'))
 idle_source=data['待机']['sourceFrames'][0];idle_fit=data['待机']['frames'][0]
 target_head=math.dist(*cfg['mother']['head'])*idle_source['scale'];target_torso=math.dist(*cfg['mother']['torso'])*idle_source['scale']
 ref=json.loads((R/'work/v4-handoff-20261009-partial/V4/evidence/furina-idle-review/fit.json').read_text(encoding='utf-8'))
 palette=ref['palette'];report={'targetHeadWorld':target_head,'targetTorsoWorld':target_torso,'actions':{},'simulation':'not run','device':'not observed','userAcceptance':'pending'}
 specs={
  'forwarddash':('前冲',[1,2,3,3,4,1],['原待机','压重心','蹬地','前进步','制动','原待机'],[[0,0],[0,0],[16,0],[80,0],[145,0],[160,0]]),
  'backdash':('后撤',[1,3,4,4,5,1],['原待机','后移承重','蹬退','探地','收步','原待机'],[[0,0],[0,0],[-12,0],[-70,-8],[-120,0],[-140,0]]),
  'jump':('跳跃',[4,3,7,5,9,4],['预蹲','蹬地','上升','顶点','下降','落地'],[[0,0],[0,0],[0,-105],[0,-160],[0,-100],[0,0]]),
  'defeat':('败北',[12,16,20,40],['失力','跪落','侧撑','侧卧'],[[0,0],[0,0],[0,0],[0,0]])
 }
 for key,(label,durations,phases,motion) in specs.items():
  sources=[];fits=[];checks=[]
  for i,m in enumerate(cfg[key]):
   im=Image.open(O/f'{key}-review-{i}.png').convert('RGBA')
   head=math.dist(*m['head']);torso=math.dist(*m['torso']);scale=math.sqrt(target_head/head*target_torso/torso)
   root=list(m['root'])
   if key in ['forwarddash','backdash']:
    root[0]=m['torso'][1][0]-cfg['mother']['hipOffsetWorldX']/scale
   f={'file':f'{key}-review-{i}.png','anchor':root,'scale':scale,'source':f'{key}-source-v{SOURCE_VERSIONS[key]}.png','previewOnly':True,
      'anatomy':{'headPoints':m['head'],'torsoPoints':m['torso'],'headWorld':head*scale,'torsoWorld':torso*scale}}
   # Airborne poses share a virtual floor pivot based on the same pelvis height.
   if key=='jump' and i in [1,2,3,4]:
    hip=m['torso'][1];f['anchor']=[hip[0],hip[1]+cfg['mother']['hipHeightWorld']/scale]
   fitted_frame,n=fitted(f,palette,f'{key}-review-fit-{i}.png')
   sources.append(f);fits.append(fitted_frame)
   checks.append({'source':f['file'],'scale':scale,'headWorld':head*scale,'headDeviation':head*scale/target_head-1,'torsoWorld':torso*scale,'torsoDeviation':torso*scale/target_torso-1,'rectangles':n,'face':'right; side-lying defeat changes head tilt','limbs':'source-chain review candidate; not user acceptance','sourceTouchOuterAtlas':False})
  if key in ['forwarddash','backdash']:
   sources=[dict(idle_source)]+sources+[dict(idle_source)];fits=[dict(idle_fit)]+fits+[dict(idle_fit)]
  data[label]={'sourceFrames':sources,'frames':fits,'durations':durations,'phases':phases,'motion':motion,'previewOnly':True,'status':'新动作候选：尺度／轮廓／逐姿检查，待用户播放验收','displayCalibration':{'method':'explicit head and torso source landmarks','targetHeadWorld':target_head,'targetTorsoWorld':target_torso,'bboxNormalization':False},'endContinuation':'待机' if key!='defeat' else 'KO hold'}
  report['actions'][key]={'checks':checks,'displayPoses':len(sources),'newUniquePoses':len(cfg[key]),'totalTicks':sum(durations),'firstLastIdleReused':key in ['forwarddash','backdash']}
 # Populate source-coordinate markers consumed by the corrected effect renderer.
 d=data['空轻'];points=[[[82,155],[175,216]],[[130,150],[10,63]],[[100,130],[210,218]],[[150,82],[211,75]],[[130,145],[200,150]],[[115,160],[210,216]]]
 d['swordMarkers']=[{'wrist':marker_from_contact(f,q[0]),'tip':marker_from_contact(f,q[1])} for f,q in zip(d['sourceFrames'],points)]
 d['effects']['status']='preview water trail follows reviewed wrist/tip source points; not combat'
 d=data['投技'];points=[[180,111],[130,142],[125,155],[175,135],[130,130],[100,130]]
 d['handMarkers']=[marker_from_contact(f,p) for f,p in zip(d['sourceFrames'],points)]
 # Original victim faces right in five poses, final side-lying source faces left.
 # Normalize the visual face toward the caster; no mid-animation whole-body flip.
 d=data['被投']
 for group in [d['sourceFrames'],d['frames']]:
  for i,f in enumerate(group):f['facingCorrection']=-1 if i<5 else 1
 d['status']='被投朝向逐姿归一至投方；根位置只应用一次；配对播放候选待验收'
 for label in ['前走','后退','蹲轻']:data[label]['status']+='；人体尺度校准候选，待播放复核'
 (O/'actions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
 (O/'missing-action-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 shutil.copy2(R/'work/furina_review_app.js',O/'app.js')
 # Prevent old browser caches from showing the pre-repair bank or renderer.
 html=(O/'index.html').read_text(encoding='utf-8').replace('app.js?v=full1','app.js?v=repair20261011')
 (O/'index.html').write_text(html,encoding='utf-8')
 served=R/'work/github-review-20261009/V3/assets/action-reference/furina'
 for p in O.iterdir():
  if p.suffix in ['.png','.json','.html','.js','.css']:shutil.copy2(p,served/p.name)
 print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
 prepare() if args.prepare else build()
