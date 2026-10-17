"""Independent RGBA effect palette; non-overlapping rectangles preserve alpha blending."""
from pathlib import Path
import sys,json,hashlib
from PIL import Image,ImageDraw
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent/'tools'))
import artlib
root=Path(__file__).resolve().parents[1];a=root/'dist/assets';source=a/'mavuika-light1-fx-source-v7.png';sheet=Image.open(source).convert('RGBA')
spec=[('prepare',[50,120,260,160],[110,75],.12),('release',[320,120,370,160],[27,80],.32),('slash',[690,110,490,180],[18,85],.30),('residue',[1180,115,355,190],[24,85],.30),('hit-start',[50,350,275,300],[110,137],.17),('hit-peak',[380,330,375,310],[130,157],.17),('hit-fragments',[780,330,365,320],[130,157],.17),('hit-fade',[1180,340,355,300],[130,147],.17),('block-start',[60,655,255,330],[100,135],.17),('block-peak',[370,655,350,330],[100,135],.17),('block-fragments',[780,655,365,330],[130,135],.17),('block-fade',[1180,655,355,330],[130,135],.17)]
pixel=2;smalls=[]
for name,r,anchor,scale in spec:
 crop=sheet.crop((r[0],r[1],r[0]+r[2],r[1]+r[3]));smalls.append(artlib.downscale(crop,scale/pixel))
stack=Image.new('RGBA',(max(i.width for i in smalls),sum(i.height for i in smalls)));y=0
for im in smalls:stack.paste(im,(0,y));y+=im.height
q=stack.quantize(colors=48,method=Image.Quantize.FASTOCTREE);raw=q.getpalette('RGBA');palette=[raw[i:i+4] for i in range(0,48*4,4) if raw[i+3]>=8]
P=np.array(palette);PL=artlib.rgb_to_oklab(P[:,:3]);records=[];atlas=Image.new('RGBA',(512,192));sourcehash=hashlib.sha256(source.read_bytes()).hexdigest()
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
 ox,oy=i%4*128,i//4*64;assert im.width<=128 and im.height<=64;atlas.paste(image,(ox,oy))
 record={'id':name,'index':i,'sourceRect':r,'sourceAnchor':anchor,'sourceScale':scale,'rect':[ox,oy,im.width,im.height],'anchor':[v*scale/pixel for v in anchor],'scale':pixel,'rectangles':len(rects),'alphaLevels':sorted(set(int(x) for x in encoded[:,:,3].ravel())),'status':'independent FX candidate; grip and visual acceptance pending'};records.append(record)
 (a/f'light1-fx-{name}-rects-v7.json').write_text(json.dumps({'paletteRGBA':palette,'width':im.width,'height':im.height,'rects':rects,'anchor':record['anchor'],'scale':pixel,'sourceSHA256':sourcehash,'overlap':False},separators=(',',':'))+'\n')
atlas.save(a/'mavuika-light1-fx-fit-v7.png')
report={'source':source.name,'sourceSHA256':sourcehash,'sourceAlphaZeroFraction':float((np.array(sheet)[:,:,3]==0).mean()),'fit':'mavuika-light1-fx-fit-v7.png','paletteRGBA':palette,'frames':records,'pipeline':'premultiplied BOX / independent 48-slot RGBA palette / OKLab+alpha nearest mapping / non-overlapping merged runs; body alpha128 threshold not used','rectanglesMax':max(x['rectangles'] for x in records),'status':'12 independent FX stages; model/visual/device validation separate'}
(a/'light1-fx-rig-v7.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');(root/'production/fx-fit-report-v7.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
# Use exact current V3 loaded body records, not historical PNG sheet scales.
data=json.loads((a/'v3-target-data.json').read_text());atlas=Image.new('RGBA',(2048,512));target={}
for i,(pose,p) in enumerate(data['poses'].items()):
 im=Image.new('RGBA',(round(p['w']),round(p['h'])));d=ImageDraw.Draw(im);b=p['bytes']
 for j in range(0,len(b),5):
  x,y,w,h,c=b[j:j+5];col=p['palette'][int(c)];col=col if len(col)==4 else col+[255];d.rectangle((round(x),round(y),round(x+w)-1,round(y+h)-1),fill=tuple(col))
 atlas.paste(im,(i*512,0));target[pose]={'rect':[i*512,0,im.width,im.height],'anchor':[p['ax'],p['ay']],'offsetX':p['ox'],'scale':.55,'rectangles':p['rectangles']}
atlas.save(a/'v3-target-atlas-v7.png');(a/'v3-target-rig-v7.json').write_text(json.dumps({'file':'v3-target-atlas-v7.png','character':'raidenshogun','poses':target,'previewScale':.55,'provenance':'V3 gf_fview:image / gf_art loaded lo records; whole opponent uniformly scaled 0.55 for the ~200-unit Mavuika preview; formal fighter sizes unchanged; CPU only'},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'fxFrames':len(records),'fxMaxRectangles':report['rectanglesMax'],'alphaLevels':len(set(v for r in records for v in r['alphaLevels'])),'targetPoses':len(target),'scope':'offline encoding/export only'}))
