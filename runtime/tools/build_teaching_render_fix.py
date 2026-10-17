"""Preserve input v15 and repair interrupted body prefetch and backdash scheduling."""
from pathlib import Path
import hashlib,json,shutil,sys,base64,struct
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-input-v15-20261016'
OUT=ROOT/'outputs/tutorial-render-v16-20261017'
PATCHES={
 'source/render/gf_gfx.lua':[(
  '    local order\n    if reuseRuns then',
  '    -- A partially overwritten buffer no longer contains its last complete image.\n    self.key = nil\n    local order\n    if reuseRuns then')],
 'source/render/gf_fview.lua':[(
  "if st=='dash' and provider and provider.nextDashPose then",
  "if (st=='dash' or st=='backdash') and provider and provider.nextDashPose then"),(
  "local dashBudget=self.f.state=='dash' and provider and provider.dashPrefetchBudget",
  "local dashBudget=(self.f.state=='dash' or self.f.state=='backdash') and provider and provider.dashPrefetchBudget")],
 'source/teaching/gf_character_lumine_training.lua':[(
  'local g=D.groups.dash;local t=view.f.t',
  'local g=D.groups[view.f.state];local t=view.f.t\n if not g then return D.groups.idle.frames[1] end'),(
  "g.frames[i+1] or 'idle_0'",'g.frames[i+1] or D.groups.idle.frames[1]'),(
  "return 'idle_0'\nend\nfunction P.nextAttackPose",'return D.groups.idle.frames[1]\nend\nfunction P.nextAttackPose')]
}

def clean_backdash():
 # Correct object extraction from the existing sheet; retain original pixels,
 # palette, scale, anchor and timing instead of redrawing or recolouring.
 import numpy as np
 from PIL import Image,ImageFilter
 sys.path.insert(0,str(ROOT/'runtime/tools'))
 sys.path.insert(0,str(ROOT/'work'))
 from compact_assets import LuaRuntime,python_table
 from export_furina import lua
 from build_lumine_training import painter,render
 sheet=Image.open(ROOT/'outputs/lumine-basic-20261015/source/backstep-v1.png').convert('RGBA')
 arr=np.asarray(sheet);active=arr[:,:,3]>=128
 # Label scanline runs, retaining actual component membership, not just boxes.
 parent=[];runs=[];prev=[]
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
  return i
 for y,row in enumerate(active):
  changes=np.flatnonzero(np.diff(np.r_[False,row,False].astype(np.int8)))
  cur=[]
  for a,b in zip(changes[::2],changes[1::2]):
   near=[i for x,z,i in prev if x<b and z>a]
   i=len(parent);parent.append(i)
   for j in near:parent[find(j)]=find(i)
   cur.append((int(a),int(b),i));runs.append((y,int(a),int(b),i))
  prev=cur
 area={};bounds={}
 for y,a,b,i in runs:
  k=find(i);area[k]=area.get(k,0)+b-a
  if k not in bounds:bounds[k]=[a,y,b,y+1]
  else:
   q=bounds[k];q[:]=[min(a,q[0]),min(y,q[1]),max(b,q[2]),max(y+1,q[3])]
 ids=sorted(sorted(area,key=area.get,reverse=True)[:4],key=lambda k:bounds[k][0])
 meta=json.loads((ROOT/'outputs/lumine-training-20261015/import.json').read_text(encoding='utf-8'))
 module=OUT/'source/teaching/gf_lumine_training_data.lua'
 rt=LuaRuntime();rt.execute('__loaders={};'+module.read_text(encoding='utf-8'))
 data=python_table(rt.globals().__loaders['gf_lumine_training_data']())
 before=json.loads(json.dumps(data))
 fitdir=OUT/'extraction';fitdir.mkdir(exist_ok=True)
 report=[]
 for index,k in enumerate(ids):
  key=f'backdash_{index}';f=data['frames'][key]
  mask=np.zeros(active.shape,dtype=np.uint8)
  for y,a,b,i in runs:
   if find(i)==k:mask[y,a:b]=255
  # Preserve a two-source-pixel alpha fringe belonging to this silhouette.
  owned=Image.fromarray(mask).filter(ImageFilter.MaxFilter(5))
  roi=meta['lumine'][key]['roi']
  owned=owned.crop(roi).resize((f['w'],f['h']),Image.Resampling.NEAREST)
  keep=np.asarray(owned)>0
  raw=base64.b64decode(f['d'])[:f['n']*10];values=struct.unpack('<'+'H'*(f['n']*5),raw)
  idx=np.full((f['h'],f['w']),-1,dtype=np.int16)
  for i in range(f['n']):
   x,y,w,h,c=values[i*5:i*5+5];idx[y:y+h,x:x+w]=c
  removed=int(np.sum((idx>=0)&~keep));idx[~keep]=-1
  rects=painter(idx)
  encoded=struct.pack('<'+'H'*(len(rects)*5),*(v for r in rects for v in r));encoded+=b'\0'*((-len(encoded))%3)
  oldn=f['n'];f['n']=len(rects);f['d']=base64.b64encode(encoded).decode()
  target=render(rects,[c[:3] for c in f['pal']],f['w'],f['h']);target.save(fitdir/f'{key}.png')
  expected=np.zeros((f['h'],f['w'],4),dtype=np.uint8)
  for i,col in enumerate(f['pal']):expected[idx==i]=col
  assert np.array_equal(np.asarray(target),expected)
  report.append({'key':key,'removedForeignPixels':removed,'beforeRectangles':oldn,'afterRectangles':f['n'],'sourceComponentArea':area[k],'sourceRoi':roi,'originalPaletteScaleAnchorPreserved':True})
 changed_keys={f'backdash_{i}' for i in range(4)}
 for key,frame in before['frames'].items():
  if key not in changed_keys:assert data['frames'][key]==frame,key
  else:
   for field,value in frame.items():
    if field not in ('d','n'):assert data['frames'][key][field]==value,(key,field)
 assert data['groups']==before['groups'] and data['aliases']==before['aliases']
 module.write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 (fitdir/'ownership.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 for rel,replacements in PATCHES.items():
  p=OUT/rel;code=p.read_text(encoding='utf-8')
  for old,new in replacements:
   assert code.count(old)==1,(rel,old,code.count(old))
   code=code.replace(old,new)
  p.write_text(code,encoding='utf-8')
 clean_backdash()
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert set(changed)==set(PATCHES)|{'source/teaching/gf_lumine_training_data.lua'},changed
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8') for p in order),encoding='utf-8')
 (OUT/'verification').mkdir(exist_ok=True)
 manifest={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'sourceFiles':{p:sha(OUT/p) for p in order}}
 (OUT/'build-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in manifest.items() if k!='sourceFiles'}))

if __name__=='__main__':build()
