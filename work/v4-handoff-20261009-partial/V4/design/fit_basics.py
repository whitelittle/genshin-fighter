from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageFilter
V=Path(__file__).resolve().parents[1];R=V.parent;sys.path.insert(0,str(R/'game/tools'));import artlib
jobs=json.load(open(V/'design/ROSTER_JOBS.json'))['jobs'];src=R.parent/'recovered-v4-originals/原神格斗';manifest=json.load(open(R.parent/'recovered-v4-originals/manifest.json'));times={m['original_name']:m['created_at'] for m in manifest}; reports=[]
def process(key,kind,path,cols,rows):
 out=V/'evidence'/f'{key}-{kind}-review';out.mkdir(exist_ok=True);im=Image.open(path).convert('RGBA');w,h=im.size;cw,ch=w//cols,h//rows;cells=[im.crop((x*cw,y*ch,(x+1)*cw,(y+1)*ch)) for y in range(rows) for x in range(cols)];alpha=np.asarray(im)[:,:,3]
 def fit(height,k):
  frames=[artlib.downscale(c,height/ch) for c in cells];pal=artlib.build_palette(frames,k);outline=(18,32,27) if key in ['venti'] else ((37,18,34) if key in ['yaemiko','arlecchino'] else (16,22,37));pal.append(outline);result=[]
  for f in frames:
   idx=artlib.apply_palette(f,pal[:-1]);mask=Image.fromarray((idx>=0).astype('uint8')*255);d=np.asarray(mask.filter(ImageFilter.MaxFilter(3)))>0;idx[d&(idx<0)]=len(pal)-1;rr=artlib.painter(idx);a=np.zeros((*idx.shape,4),dtype='uint8');m=idx>=0;a[m,:3]=np.asarray(pal,dtype='uint8')[idx[m]];a[m,3]=255;result.append((Image.fromarray(a),rr))
  return result,pal
 initial,ip=fit(80,24);height=80
 while True:
  optimized,pal=fit(height,18)
  if max(len(r) for _,r in optimized)<=760 or height<=32:break
  height-=4
 counts=[len(r) for _,r in optimized];seq=[];contact=Image.new('RGB',(960,320*len(cells)),'#30323a');edges=[];sil=[]
 for i,(c,(ini,_),(opt,rr)) in enumerate(zip(cells,initial,optimized)):
  c.save(out/f'source-cell-{i}.png');ini.save(out/f'initial-{i}.png');opt.save(out/f'optimized-{i}.png');
  for n,img in enumerate([artlib.downscale(c,80/ch),ini,opt]):
   canvas=Image.new('RGB',(240,160),'#ddd9cd');img=img.resize((round(img.width*160/img.height),160),Image.Resampling.NEAREST);canvas.paste(img,((240-img.width)//2,0),img);contact.paste(canvas.resize((320,320)),(n*320,i*320))
  pair=Image.new('RGB',(640,320));f=opt.resize((round(opt.width*320/opt.height),320),Image.Resampling.NEAREST)
  for n,bg in enumerate(['#242936','#dfdbcd']):
   b=Image.new('RGB',(320,320),bg);b.paste(f,((320-f.width)//2,0),f);pair.paste(b,(n*320,0))
  seq.append(pair);a=np.asarray(opt)[:,:,3];ys,xs=np.where(a>0);sil.append(int(ys.max()) if len(ys) else None);edges.append(bool(a[0].any() or a[-1].any() or a[:,0].any() or a[:,-1].any()))
 seq[0].save(out/'playback.gif',save_all=True,append_images=seq[1:],duration=350 if kind=='idle' else 120,loop=0);contact.save(out/'source-initial-optimized.png')
 report={'character':key,'group':kind,'source':str(path),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'original_prompt':'not_recovered' if 'recovered-v4' in str(path) else 'V4/design/mavuika-idle-no-glasses-v2.prompt.txt','grid':[cols,rows],'initial_height':80,'optimized_height':height,'palette':pal,'rect_counts':counts,'mean_rects':sum(counts)/len(counts),'max_rects':max(counts),'budget760':max(counts)<=760,'source_alpha_min':int(alpha.min()),'transparent_fraction':float((alpha==0).mean()),'silhouette_bottom_y':sil,'edge_contact':edges,'anchor_policy':'固定原格锚点，不裁切居中；脚底/握点尚须人工定位；空中动作不套脚锚','status':'离线拟合/比较图/播放证据已生成；动作语义、风格与足底尚未全套验收；非逻辑/模拟器/真机','frames':[{'rects':rr} for _,rr in optimized]}
 (out/'fit.json').write_text(json.dumps(report,ensure_ascii=False));reports.append({k:report[k] for k in ['character','group','source_sha256','optimized_height','rect_counts','mean_rects','max_rects','budget760','silhouette_bottom_y','edge_contact','status']});print(key,kind,counts,flush=True)
for j in jobs:
 key=j['character'];idle=Path(j.get('corrected_master',j['reference']));idle=R/idle if not idle.is_absolute() else idle;process(key,'idle',idle,2,1)
 name={'furina':'芙宁娜','zhongli':'钟离','mavuika':'玛薇卡','venti':'温迪','kamisatoayaka':'神里绫华','tartaglia':'达达利亚','aratakiitto':'荒泷一斗','yaemiko':'八重神子','arlecchino':'阿蕾奇诺','wanderer':'流浪者','neuvillette':'那维莱特','clorinde':'克洛琳德','navia':'娜维娅','skirk':'丝柯克'}[key]
 cand=[p for p in src.glob('*.png') if name in p.name and ('行走' in p.name or '步态' in p.name or '前行' in p.name)];cand.sort(key=lambda p:times.get(p.name,''),reverse=True)
 if cand:process(key,'walk',cand[0],3,2)
(V/'evidence/basics-fit-summary.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2))
