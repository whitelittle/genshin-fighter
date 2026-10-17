"""Keep the approved first pose, initialize parts by pose landmarks, refit HD."""
import copy,json,math,time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
code=Path('work/optimize_nahida_primitives_20261015.py').read_text(encoding='utf-8')
exec(code[:code.index('baseline=actual_measure')],globals())
ROOT=Path('outputs/nahida-quality-frames-20261015');ROOT.mkdir(parents=True,exist_ok=True)
REF=Path('outputs/nahida-independent-actions-20261015')
seed=json.loads(Path('outputs/nahida-native-budget1000-20261015/collage.json').read_text(encoding='utf-8'))['elements']
W,H=384,512;yy,xx=np.mgrid[:H,:W].astype(np.float32);xx+=.5;yy+=.5
# Explicit pose guides initialize geometry only; every non-base pose is then
# independently scored and optimized against its own original HD reference.
guides=[
 dict(head=(235,112),torso=((230,175),(230,295)),arms=(((205,195),(162,290)),((257,195),(298,287))),legs=(((215,310),(202,385),(200,448),(228,467)),((240,310),(241,385),(241,447),(261,463)))),
 dict(head=(234,114),torso=((230,175),(228,295)),arms=(((205,195),(121,287)),((257,195),(318,262))),legs=(((210,315),(162,379),(132,445),(165,468)),((250,315),(263,381),(285,451),(324,465)))),
 dict(head=(239,112),torso=((235,175),(231,293)),arms=(((210,195),(169,289)),((261,188),(322,251))),legs=(((211,310),(168,380),(131,445),(157,470)),((250,310),(278,380),(293,445),(330,457)))),
 dict(head=(240,110),torso=((233,175),(232,295)),arms=(((210,195),(169,287)),((264,198),(288,292))),legs=(((213,310),(198,370),(154,419),(169,457)),((246,310),(245,385),(242,449),(273,470)))),
 dict(head=(330,237),torso=((281,272),(223,330)),arms=(((257,278),(140,280)),((300,278),(325,330))),legs=(((240,350),(158,390),(70,420),(83,450)),((275,350),(260,390),(225,433),(270,450)))),
 dict(head=(292,181),torso=((256,230),(202,305)),arms=(((233,235),(143,267)),((270,233),(342,246))),legs=(((200,325),(139,365),(56,400),(54,435)),((245,335),(280,360),(318,419),(366,430)))),
 dict(head=(292,192),torso=((259,242),(224,320)),arms=(((239,249),(140,283)),((277,248),(300,297))),legs=(((230,350),(235,387),(218,438),(249,449)),((267,350),(290,354),(265,400),(300,448)))),
 dict(head=(318,143),torso=((276,193),(247,271)),arms=(((254,201),(156,211)),((295,207),(313,251))),legs=(((252,280),(240,315),(214,346),(216,362)),((277,281),(310,285),(289,350),(284,430))))]
base=guides[0]
def line_map(p,a,b):
 a,b=np.array(a,float),np.array(b,float);v=a[1]-a[0];q=b[1]-b[0];scale=np.linalg.norm(q)/max(np.linalg.norm(v),1)
 angle=math.atan2(q[1],q[0])-math.atan2(v[1],v[0]);c,s=math.cos(angle),math.sin(angle);M=np.array([[c,-s],[s,c]])*scale
 return b[0]+M@(p-a[0]),M
def mapping(p,part,g):
 x,y=p
 if y<170 or part in ('head','head-ornament','face','eyes','front-hair','back-hair'):
  # Face and fine hair contours remain recognizable in the initial pose.
  shift=np.array(g['head'])-np.array(base['head'])
  if g['head'][1]>140 and x<190:
   M=np.array([[1.65,0],[.5,.55]])
   return np.array(g['head'])+M@(p-np.array(base['head'])),M
  return p+shift,np.eye(2)
 if y>315:
  side=0 if x<226 else 1;a=base['legs'][side];b=g['legs'][side]
  k=0 if y<385 else (1 if y<447 else 2)
  return line_map(p,a[k:k+2],b[k:k+2])
 if part in ('front-arm','rear-arm') or (x>265 and y>190) or (x<185 and y>230 and x>145):
  side=0 if x<232 else 1;return line_map(p,base['arms'][side],g['arms'][side])
 return line_map(p,base['torso'],g['torso'])
def sparse_mask(e):
 # Same native primitive equations, evaluated only in its bounding patch.
 global xx,yy,W,H
 if e.get('removed'):return np.zeros((H,W),np.uint8)
 rad=math.hypot(e['width'],e['height'])/2+2
 x0=max(0,int(e['x']-rad));x1=min(W,int(e['x']+rad+1));y0=max(0,int(e['y']-rad));y1=min(H,int(e['y']+rad+1))
 result=np.zeros((H,W),np.uint8)
 if x1<=x0 or y1<=y0:return result
 fullx,fully,fw,fh=xx,yy,W,H
 xx,yy=xx[y0:y1,x0:x1],yy[y0:y1,x0:x1];W,H=x1-x0,y1-y0
 try:result[y0:y1,x0:x1]=original_mask(e)
 finally:xx,yy,W,H=fullx,fully,fw,fh
 return result
original_mask=mask;mask=sparse_mask
actions=[];report=[]
cached=json.loads((ROOT/'progress.json').read_text(encoding='utf-8')) if (ROOT/'progress.json').exists() else []
for ai,action in enumerate(('idle','move')):
 frames=[]
 for index in range(4):
  OUT=ROOT/action/str(index);OUT.mkdir(parents=True,exist_ok=True)
  done=next((r for r in cached if r['action']==action and r['frame']==index),None)
  if done and (OUT/'collage.json').exists():
   elements=json.loads((OUT/'collage.json').read_text(encoding='utf-8'))['elements']
   frames.append({'index':index,'durationMs':180,'elements':elements,'reference':f'{action}/{index}/reference.png','svg':f'{action}/{index}/fitted.svg'})
   report.append(done);print('REUSE_COMPLETED_FRAME '+action+' '+str(index),flush=True);continue
  source=Image.open(REF/action/str(index)/'reference.png').convert('RGBA');source.save(OUT/'reference.png')
  raw=np.array(source);targetA=(raw[:,:,3]>=48).astype(np.float32);target=raw[:,:,:3].astype(np.float32)/255;target[targetA==0]=1
  gy,gx=np.gradient(target.mean(axis=2));weights=1+np.clip(np.hypot(gx,gy)*8,0,2)
  g=guides[ai*4+index];hx,hy=g['head'];weights[max(0,int(hy-55)):min(H,int(hy+45)),max(0,int(hx-55)):min(W,int(hx+50))]*=2
  elements=copy.deepcopy(seed)
  for e in elements:
   p=np.array([e['x']+59,e['y']+19]);center,M=mapping(p,e.get('part'),g)
   r=math.radians(-e['rotation']);u=M@np.array([math.cos(r),math.sin(r)]);v=M@np.array([-math.sin(r),math.cos(r)])
   e.update(x=float(center[0]),y=float(center[1]),width=e['width']*np.linalg.norm(u),height=e['height']*np.linalg.norm(v),rotation=-math.degrees(math.atan2(u[1],u[0])))
  unchanged=ai==0 and index==0
  if unchanged:
   elements=copy.deepcopy(seed)
   for e in elements:e['x']+=59;e['y']+=19
  initial=copy.deepcopy(elements);baseline=actual_measure(elements,'initial');history=[]
  if not unchanged:
   masks=[mask(e) for e in elements]
   loop=code[code.index('for sweep,step in enumerate'):code.index('# Select by actual rendered SVG')]
   loop=loop.replace('[4,2,1,.5]','[6,3,1]').replace('if delete_loss<=bestloss+.2:','if False:').replace('>30:','>65:')
   exec(loop,globals())
  final=actual_measure(elements,'fitted')
  for i,e in enumerate(elements):e['poolId']=i
  (OUT/'collage.json').write_text(json.dumps({'w':W,'h':H,'elements':elements},ensure_ascii=False,separators=(',',':')),encoding='utf-8')
  frames.append({'index':index,'durationMs':180,'elements':elements,'reference':f'{action}/{index}/reference.png','svg':f'{action}/{index}/fitted.svg'})
  row={'action':action,'frame':index,'approvedStaticGeometryPreserved':unchanged,'baseline':baseline,'final':final,'passes':history};report.append(row)
  (ROOT/'progress.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('QUALITY_FRAME '+json.dumps(row),flush=True)
 actions.append({'key':action,'name':'基础姿势组' if ai==0 else '移动姿势组','frames':frames,'loop':True})
manifest={'w':W,'h':H,'imagePoolSize':994,'actions':actions,'background':'transparent','transition':'discrete frames','deviceVerified':False}
(ROOT/'animation.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
for action in ('idle','move'):
 panel=Image.new('RGB',(1200,300),'#eef2f5');d=ImageDraw.Draw(panel)
 for i in range(4):
  d.text((i*300+8,8),f'{action} {i+1}  原图 / 混合图元',font=font,fill='#354139')
  for name,x in [('reference.png',i*300+3),('fitted.png',i*300+153)]:
   pic=Image.open(ROOT/action/str(i)/name).convert('RGBA').resize((144,192),Image.Resampling.LANCZOS);panel.paste(pic,(x,47),pic)
 panel.save(ROOT/(action+'-contact.png'))
print('QUALITY_FRAMES_COMPLETE',flush=True)
