"""Complete a one-cell exterior contour; preserve original interior RGBA and anchors."""
from pathlib import Path
from collections import deque
import sys,json,base64,struct,hashlib
import numpy as np
from PIL import Image,ImageFilter
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'work/optimization-test-deps'))
sys.path.insert(0,str(R/'game/tools'))
from lupa.lua53 import LuaRuntime
import artlib
from export_furina import lua
O=R/'outputs/six-character-size-20261013/ayaka-outline';O.mkdir(parents=True,exist_ok=True)
p=R/'runtime/source/assets/gf_ayaka_data.lua';original=p.read_text(encoding='utf-8')
backup=O/'original-gf_ayaka_data.lua'
if not backup.exists():backup.write_text(original,encoding='utf-8')
rt=LuaRuntime(unpack_returned_tuples=True);rt.execute('__loaders={};'+backup.read_text(encoding='utf-8'))
def native(v):
 if not hasattr(v,'items'):return v
 d={k:native(x) for k,x in v.items()}
 return [d[i] for i in range(1,len(d)+1)] if d and set(d)==set(range(1,len(d)+1)) else d
data=native(rt.globals().__loaders.gf_ayaka_data())
body={pose for g in data['groups'].values() for pose in g['frames']}
receiptPath=R/'runtime/ayaka-import.json';originalReceipt=O/'original-ayaka-import.json'
if not originalReceipt.exists():originalReceipt.write_bytes(receiptPath.read_bytes())
receipt=json.loads(originalReceipt.read_text(encoding='utf-8'));checks=[]
sourceByPose={r['pose']:r for r in receipt['sources'] if r['pose'] in body}
for pose in sorted(body):
 row=sourceByPose[pose];im=np.array(Image.open(R/row['file']).convert('RGBA'));h,w=im.shape[:2]
 padded=np.pad(im,((1,1),(1,1),(0,0)));mask=padded[:,:,3]>0
 outside=np.zeros(mask.shape,bool);q=deque([(0,0)]);outside[0,0]=True
 while q:
  x,y=q.popleft()
  for nx,ny in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if 0<=nx<w+2 and 0<=ny<h+2 and not mask[ny,nx] and not outside[ny,nx]:outside[ny,nx]=True;q.append((nx,ny))
 expanded=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
 edge=outside&expanded
 padded[edge]=[22,29,58,255]
 assert np.array_equal(padded[1:-1,1:-1],np.where(im[:,:,3,None]>0,im,padded[1:-1,1:-1]))
 # Encode the exact native-pixel target. Original rectangles keep their order;
 # non-overlapping outside stroke rectangles follow them.
 img=data['frames'][pose];raw=base64.b64decode(img['d']);values=struct.unpack('<'+'H'*(img['n']*5),raw[:img['n']*10]);rects=[list(values[i:i+5]) for i in range(0,len(values),5)]
 for r in rects:r[0]+=1;r[1]+=1
 pal=img['pal'];stroke=[22,29,58,255]
 if stroke not in pal:pal.append(stroke)
 index=pal.index(stroke);idx=np.where(edge,index,-1)
 rects.extend(artlib.painter(idx))
 rebuilt=np.zeros_like(padded)
 for x,y,rw,rh,c in rects:rebuilt[y:y+rh,x:x+rw]=pal[c]
 assert np.array_equal(rebuilt,padded),(pose,'outline reconstruct')
 raw=struct.pack('<'+'H'*(len(rects)*5),*(v for r in rects for v in r));raw+=b'\0'*((-len(raw))%3)
 img.update(n=len(rects),d=base64.b64encode(raw).decode(),ax=img['ax']+1,ay=img['ay']+1,w=w+2,h=h+2)
 path=O/(pose+'.png');Image.fromarray(padded).save(path)
 meta=O/(pose+'.rects.json');meta.write_text(json.dumps({'rects':rects,'palette':pal,'originalFile':row['file'],'contour':'1-cell exterior only','interiorPreserved':True},ensure_ascii=False),encoding='utf-8')
 checks.append({'pose':pose,'originalRects':len(values)//5,'outlinedRects':len(rects),'addedPixels':int(edge.sum()),'interiorRgbaIdentical':True})
 for record in receipt['sources']:
  if record['pose']==pose:
   record.update(file=path.relative_to(R).as_posix(),rectsFile=meta.relative_to(R).as_posix(),imageSha256=hashlib.sha256(path.read_bytes()).hexdigest(),rectsSha256=hashlib.sha256(meta.read_bytes()).hexdigest(),anchor=[img['ax'],img['ay']],originalFile=row['file'])
data['bodyPeak']=max(data['frames'][pose]['n'] for pose in body)
p.write_text("__loaders['gf_ayaka_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
receipt.update(bodyPeak=data['bodyPeak'],outlineRevision='20261013 exterior 1-cell; original interior exact')
receiptPath.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'verification.json').write_text(json.dumps({'checks':checks,'bodyPeak':data['bodyPeak'],'nativeTested':False},indent=2),encoding='utf-8')
print('outlined bodies',len(body),'peak',data['bodyPeak'])
