"""Independent RGBA effect palette; non-overlapping rectangles preserve alpha blending."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
import artlib
root=Path(__file__).resolve().parents[1];a=root/'dist/assets';source=a/'mavuika-q-fx-source-v8.png';sheet=Image.open(source).convert('RGBA')
spec=[('sun-open', [55, 25, 310, 305], [150, 165], 0.42), ('sun-full', [403, 0, 365, 345], [185, 180], 0.42), ('sun-fade', [790, 15, 350, 325], [175, 160], 0.42), ('charge', [1230, 0, 300, 340], [125, 183], 0.14), ('wheel-trail', [0, 375, 449, 248], [433, 180], 0.34), ('blade-prepare', [459, 365, 340, 315], [30, 20], 0.6), ('slash', [779, 345, 415, 346], [10, 10], 0.7), ('slash-residue', [1189, 355, 347, 329], [10, 10], 0.7), ('brake-sparks', [0, 741, 449, 234], [402, 183], 0.34), ('skid-residue', [449, 768, 365, 210], [335, 163], 0.34), ('impact', [824, 701, 315, 300], [175, 160], 0.38), ('impact-fade', [1181, 695, 350, 312], [175, 170], 0.38)]
pixel=2;smalls=[]
for name,r,anchor,scale in spec:
 crop=sheet.crop((r[0],r[1],r[0]+r[2],r[1]+r[3]));smalls.append(artlib.downscale(crop,scale/pixel))
stack=Image.new('RGBA',(max(i.width for i in smalls),sum(i.height for i in smalls)));y=0
for im in smalls:stack.paste(im,(0,y));y+=im.height
q=stack.quantize(colors=48,method=Image.Quantize.FASTOCTREE);raw=q.getpalette('RGBA');palette=[raw[i:i+4] for i in range(0,48*4,4) if raw[i+3]>=8]
P=np.array(palette);PL=artlib.rgb_to_oklab(P[:,:3]);records=[];atlas=Image.new('RGBA',(768,384));sourcehash=hashlib.sha256(source.read_bytes()).hexdigest()
def runs(idx):
 result=[];prior={}
 for y,row in enumerate(idx):
  current={};x=0
  while x<len(row):
   c=int(row[x]);end=x+1
   while end<len(row) and int(row[end])==c:end+=1
   if c>=0:
    key=(x,end-x,c)
    if key in prior:r=prior[key];r[3]+=1
    else:r=[x,y,end-x,1,c];result.append(r)
    current[key]=r
   x=end
  prior=current
 return result
for i,(im,(name,r,anchor,scale)) in enumerate(zip(smalls,spec)):
 rgba=np.array(im);L=artlib.rgb_to_oklab(rgba[:,:,:3]);dist=((L[:,:,None,:]-PL[None,None,:,:])**2).sum(3)+((rgba[:,:,None,3].astype(float)-P[None,None,:,3])/255*.35)**2
 idx=dist.argmin(2);idx[rgba[:,:,3]<8]=-1;rects=runs(idx);restored=np.full(idx.shape,-1);cover=np.zeros(idx.shape,dtype=int)
 for x,y,w,h,c in rects:restored[y:y+h,x:x+w]=c;cover[y:y+h,x:x+w]+=1
 assert np.array_equal(restored,idx) and cover.max()<=1,'RGBA painter overlap or reconstruction mismatch'
 encoded=np.zeros((*idx.shape,4),dtype=np.uint8);mask=idx>=0;encoded[mask]=P[idx[mask]];image=Image.fromarray(encoded,'RGBA')
 ox,oy=i%4*192,i//4*128;assert im.width<=192 and im.height<=128;atlas.paste(image,(ox,oy))
 record={'id':name,'index':i,'sourceRect':r,'sourceAnchor':anchor,'sourceScale':scale,'rect':[ox,oy,im.width,im.height],'anchor':[v*scale/pixel for v in anchor],'scale':pixel,'rectangles':len(rects),'alphaLevels':sorted(set(int(x) for x in encoded[:,:,3].ravel())),'status':'independent FX candidate; grip and visual acceptance pending'};records.append(record)
 (a/f'q-fx-{name}-rects-v8.json').write_text(json.dumps({'paletteRGBA':palette,'width':im.width,'height':im.height,'rects':rects,'anchor':record['anchor'],'scale':pixel,'sourceSHA256':sourcehash,'overlap':False},separators=(',',':'))+'\n')
atlas.save(a/'mavuika-q-fx-fit-v8.png')
report={'source':source.name,'sourceSHA256':sourcehash,'sourceAlphaZeroFraction':float((np.array(sheet)[:,:,3]==0).mean()),'fit':'mavuika-q-fx-fit-v8.png','paletteRGBA':palette,'frames':records,'pipeline':'premultiplied BOX / independent 48-slot RGBA palette / OKLab+alpha nearest mapping / non-overlapping merged runs; body alpha128 threshold not used','rectanglesMax':max(x['rectangles'] for x in records),'status':'12 independent FX stages; model/visual/device validation separate'}
(a/'q-fx-rig-v8.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(root/'production/fx-fit-report-v8.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

print(json.dumps({"frames":len(records),"maxRectangles":report["rectanglesMax"],"transparent":report["sourceAlphaZeroFraction"]}))
