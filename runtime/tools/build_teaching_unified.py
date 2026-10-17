"""Explicit, reviewable teaching asset manifest: approved walk family plus new attacks."""
from pathlib import Path
import json,hashlib,shutil,sys,struct,base64,copy
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-render-v16-20261017'
OUT=ROOT/'outputs/tutorial-unified-v17-20261017'
ART=ROOT/'outputs/lumine-unified-20261017'
sys.path[:0]=[str(ROOT/'runtime/tools'),str(ROOT/'work')]
from compact_assets import LuaRuntime,python_table
from export_furina import lua
from build_lumine_training import components
import clorinde_assets as ca

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bank():
 rt=LuaRuntime();rt.execute('__loaders={};'+(BASE/'source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
 return python_table(rt.globals().__loaders['gf_lumine_training_data']())

def fit(im,anchor,unit,key,calibration,contrast):
 ca.O=ART
 info,meta=ca.canonical_fit(im,anchor,unit,calibration['palette'],key)
 size=Image.open(ART/info['file']).size
 target=ca.artlib.render(meta['rects'],contrast,*size)
 target.save(ART/info['file'])
 meta['palette']=contrast
 (ART/'fit'/f'{key}.json').write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')
 raw=struct.pack('<'+'H'*(len(meta['rects'])*5),*(v for rect in meta['rects'] for v in rect));raw+=b'\0'*((-len(raw))%3)
 data={'n':len(meta['rects']),'d':base64.b64encode(raw).decode(),'pal':[c+[255] for c in contrast],'ax':info['anchor'][0],'ay':info['anchor'][1],'u':info['scale'],'w':target.width,'h':target.height}
 return data,{**info,'sourceAnchor':anchor,'sourceUnit':unit,'sameQuantizationAndContrastAsApprovedWalk':True}

def attack(group,calibration,contrast):
 path=ART/'source'/f'{group}.png';im=Image.open(path).convert('RGBA')
 alpha=np.asarray(im)[:,:,3];mask=alpha>=128
 # Keep membership, not only bounding boxes: a long sword may cross the
 # neighbouring cell's box without touching that neighbouring silhouette.
 parent=[];runs=[];previous=[]
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for y,row in enumerate(mask):
  edges=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)));current=[]
  for a,b in zip(edges[::2],edges[1::2]):
   n=len(parent);parent.append(n)
   for x,z,k in previous:
    if x<b and z>a:parent[find(k)]=find(n)
   current.append((int(a),int(b),n));runs.append((y,int(a),int(b),n))
  previous=current
 areas={};bounds={}
 for y,a,b,n in runs:
  k=find(n);areas[k]=areas.get(k,0)+b-a
  if k not in bounds:bounds[k]=[a,y,b,y+1]
  else:
   q=bounds[k];q[:]=[min(q[0],a),min(q[1],y),max(q[2],b),max(q[3],y+1)]
 ids=sorted(areas,key=areas.get,reverse=True)[:5]
 comps=[(areas[k],bounds[k],k)for k in ids]
 assert len(comps)==5 and min(n for n,b,k in comps)>5000,(group,comps)
 # Layout sorts objects; actual silhouettes, not fixed cells, define extraction.
 comps.sort(key=lambda v:(int((v[1][1]+v[1][3])/2//(im.height/2)),(v[1][0]+v[1][2])/2))
 neutral=comps[0][1];unit=320/(neutral[3]-neutral[1])
 data={};rows={}
 ownedHigh=np.zeros(mask.shape,dtype=np.uint8)
 for index,(area,bb,k) in enumerate(comps):
  for y,a,b,n in runs:
   if find(n)==k:ownedHigh[y,a:b]+=1
 assert ownedHigh.max()==1,'source ownership overlap'
 for i,(area,bb,k) in enumerate(comps[1:]):
  own=np.zeros(mask.shape,dtype=np.uint8)
  for y,a,b,n in runs:
   if find(n)==k:own[y,a:b]=255
  fringe=np.asarray(Image.fromarray(own).filter(ImageFilter.MaxFilter(3)))>0
  rgba=np.asarray(im).copy();rgba[:,:,3]=np.where(fringe,alpha,0)
  crop=Image.fromarray(rgba).crop(bb);a=np.asarray(crop);ys,xs=np.nonzero(a[:,:,3]>=128)
  bottom=int(ys.max()+1);foot=xs[ys>=bottom-4]
  anchor=[float((foot.min()+foot.max())/2),bottom]
  key=f'{group}_{i}';data[key],rows[key]=fit(crop,anchor,unit,key,calibration,contrast)
  rows[key].update(source=f'source/{group}.png',sourceSha256=digest(path),sourceRoi=bb,area=area,neutralCalibrationBounds=neutral,independentScalePerPose=False,sourceOwnership='actual connected silhouette plus 1-source-pixel alpha fringe; no overlapping major objects')
  (ART/'extracted').mkdir(exist_ok=True);crop.save(ART/'extracted'/f'{key}.png')
 return data,rows

def build():
 (ART/'fit').mkdir(parents=True,exist_ok=True)
 data=bank();old=copy.deepcopy(data)
 calibration=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/report.json').read_text(encoding='utf-8'))
 contrast=json.loads((ROOT/'outputs/lumine-rebuild-20261016/canonical-v4/fit/master-contrast.json').read_text(encoding='utf-8'))['palette']
 rows={}
 # Latest explicit request: backward travel uses the approved forward-walk bank.
 # It is reused in reverse phase order, not claimed as newly drawn backward art.
 data['groups']['back']={'frames':['walk_00','walk_06','walk_04','walk_02'],'durations':[14]*4}
 for i in range(4):
  key=f'dash_{i}';p=ROOT/f'outputs/lumine-rebuild-20261016/source/dash_{i}-selected.png'
  im=Image.open(p).convert('RGBA')
  data['frames'][key],rows[key]=fit(im,[520,1430],calibration['sourceUnit'],key,calibration,contrast)
  rows[key].update(source=p.relative_to(ROOT).as_posix(),sourceSha256=digest(p),reason='previous16-color/no-canonical-outline bank replaced by approved19-color canonical fitting')
 for group in ['light1','light2','light3','heavy']:
  frames,details=attack(group,calibration,contrast);data['frames'].update(frames);rows.update(details)
  assert data['groups'][group]['frames']==[f'{group}_{i}'for i in range(4)]
 assert data['frames']['teaching_master']==old['frames']['teaching_master']
 assert data['groups']['walk']==old['groups']['walk']
 for key in data['groups']['walk']['frames']:assert data['frames'][key]==old['frames'][key]
 for key in [*data['groups']['walk']['frames'],*[f'dash_{i}'for i in range(4)],*[f'{g}_{i}'for g in ['light1','light2','light3','heavy']for i in range(4)]]:
  assert data['frames'][key]['pal']==data['frames']['teaching_master']['pal'],key
 data['bodyPeak']=max(f['n']for f in data['frames'].values())
 unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()};mean=sum(f['n']for f in unique.values())/len(unique)
 assert mean<1000,mean
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 (OUT/'source/teaching/gf_lumine_training_data.lua').write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 p=OUT/'source/render/gf_ui.lua';code=p.read_text(encoding='utf-8')
 code=code.replace('function Menu:pick()\n','function Menu:pick()\n    if self.freed then return end\n')
 code=code.replace('function Menu:free() self.L:free() end',"""function Menu:free()
    if self.freed then return end
    self.freed=true
    for _,b in ipairs(self.areas)do
        if b and b.node and b.node.handlers==b.handlers then b.node.handlers=nil;b.node:on(false) end
    end
    self.L:free()
end""")
 p.write_text(code,encoding='utf-8')
 p=OUT/'source/teaching/gf_training_lesson.lua';code=p.read_text(encoding='utf-8')
 before='else self.completeMenu:free();self.completeMenu=nil;self.briefTicks=0;self.scene:touchControls() end'
 after='else local menu=self.completeMenu;if not menu then return end;self.completeMenu=nil;menu:free();app.input:clearUI();self.briefTicks=0;self.scene:touchControls() end'
 assert code.count(before)==1;code=code.replace(before,after);p.write_text(code,encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 changed=[p for p in order if digest(BASE/p)!=digest(OUT/p)]
 assert set(changed)=={'source/teaching/gf_lumine_training_data.lua','source/teaching/gf_training_lesson.lua','source/render/gf_ui.lua'},changed
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8') for p in order),encoding='utf-8')
 (OUT/'verification').mkdir(exist_ok=True)
 manifest={'clientSha256':digest(OUT/'genshin_fighter.lua'),'baselineSha256':digest(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'sourceFiles':{p:digest(OUT/p)for p in order},'bodyUniqueMean':mean,'bodyPeak':data['bodyPeak'],'newPeak':max(data['frames'][k]['n']for k in rows),'frames':rows,'groups':{g:data['groups'][g]for g in ['idle','walk','back','dash','light1','light2','light3','heavy']},'backwalk':'explicit approved-forward-bank reuse; not independently drawn','remainingLegacy':['backdash','jump','guard','crouchAttack','airAttack','skill','burst','hurt','throw']}
 (OUT/'build-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 (ART/'import.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 reviewkeys={key for group in manifest['groups'].values()for key in group['frames']}
 (ART/'review-data.json').write_text(json.dumps({'frames':{k:data['frames'][k]for k in reviewkeys},'groups':manifest['groups']},ensure_ascii=False),encoding='utf-8')
 # Each review cell is drawn from the exact runtime rectangles at one common
 # world scale and foot root, never resized to match its silhouette bounds.
 for group in ['dash','light1','light2','light3','heavy']:
  board=Image.new('RGB',(2600,430),'#263454');draw=ImageDraw.Draw(board)
  for i,key in enumerate(['teaching_master']+data['groups'][group]['frames']):
   f=data['frames'][key];raw=base64.b64decode(f['d'])[:f['n']*10];rects=struct.unpack('<'+'H'*(f['n']*5),raw)
   draw.line((i*520,375,(i+1)*520,375),fill='#a2b5d2',width=1)
   draw.text((i*520+12,12),key,fill='white')
   for j in range(f['n']):
    x,y,w,h,c=rects[j*5:j*5+5];px=i*520+170+(x-f['ax'])*f['u'];py=375+(y-f['ay'])*f['u']
    draw.rectangle((px,py,px+w*f['u']-.01,py+h*f['u']-.01),fill=tuple(f['pal'][c][:3]))
  board.save(ART/f'{group}-runtime-review.png')
 print(json.dumps({k:v for k,v in manifest.items()if k not in ['frames','sourceFiles','groups']},ensure_ascii=False))

if __name__=='__main__':build()
