from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageFilter,ImageDraw
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'game/tools'));import artlib
for path in sorted((R/'V4/assets/skill-candidates').glob('*.png')):
 out=R/'V4/evidence'/path.stem;out.mkdir(exist_ok=True)
 im=Image.open(path).convert('RGBA');w,h=im.size;cw,ch=w//2,h//2
 frames=[artlib.downscale(im.crop((x*cw,y*ch,(x+1)*cw,(y+1)*ch)),80/ch) for y in range(2) for x in range(2)]
 pal=artlib.build_palette(frames,24);pal.append((15,19,36)); indices=[];counts=[];plays=[];feet=[]
 for n,f in enumerate(frames):
  idx=artlib.apply_palette(f,pal[:-1]);mask=Image.fromarray((idx>=0).astype('uint8')*255);dil=np.asarray(mask.filter(ImageFilter.MaxFilter(3)))>0;idx[dil&(idx<0)]=len(pal)-1
  ys,xs=np.where(idx>=0);feet.append(int(ys.max()) if len(ys) else None)
  rects=artlib.painter(idx);counts.append(len(rects));rgba=np.zeros((*idx.shape,4),dtype='uint8');m=idx>=0;rgba[m,:3]=np.asarray(pal,dtype='uint8')[idx[m]];rgba[m,3]=255;fr=Image.fromarray(rgba);fr.save(out/f'frame-{n}.png');indices.append({'frame':n,'rects':rects})
  for bg in [(32,35,46),(221,219,208)]:
   canvas=Image.new('RGB',fr.size,bg);canvas.paste(fr,mask=fr.getchannel('A'));plays.append(canvas.resize((fr.width*4,320),Image.Resampling.NEAREST))
 dark=plays[::2];light=plays[1::2];seq=[]
 for a,b in zip(dark,light):
  c=Image.new('RGB',(a.width*2,320));c.paste(a,(0,0));c.paste(b,(a.width,0));seq.append(c)
 seq[0].save(out/'playback.gif',save_all=True,append_images=seq[1:],duration=[300,100,100,400],loop=0)
 report={'source':str(path.relative_to(R)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'method':'固定2x2格，不逐帧裁切居中；premult alpha BOX；加权OKLab共享24色；外侧1px深色轮廓','frame_size':list(frames[0].size),'fixed_anchor':[frames[0].width//2,79],'foot_y':feet,'rectangles':counts,'mean':sum(counts)/4,'max':max(counts),'status':'拟合与播放证据已生成；未做模拟器/真机验证；源图脚底及外描边待复核','palette':pal,'frames':indices}
 (out/'fit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(path.stem,counts,feet)
