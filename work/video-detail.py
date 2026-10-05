from pathlib import Path
import sys,json
sys.path.insert(0,str(Path('work/video-deps')))
import cv2
from PIL import Image,ImageDraw
out=Path('outputs/video-check')
meta=json.loads((out/'metadata.json').read_text(encoding='utf-8'))
specs={0:(1050,310,1390,510),1:(1290,265,1730,460),2:(1610,275,1920,470),3:(1200,200,1510,350),4:(1640,225,1900,410)}
canvas=Image.new('RGB',(1600,5*300),'#222');d=ImageDraw.Draw(canvas)
for m in meta:
 for j,s in enumerate(m['samples']):
  im=Image.open(s['path']);crop=im.crop(specs[m['id']]);crop.thumbnail((390,270));crop=crop.resize((390,int(crop.height*390/crop.width)))
  canvas.paste(crop,(j*400,m['id']*300+30));d.text((j*400+5,m['id']*300+5),'v%d %.2fs'%(m['id'],s['seconds']),fill='white')
canvas.save(out/'debug-crops.png')
cap=cv2.VideoCapture(meta[3]['file']);canvas=Image.new('RGB',(1500,6*300),'#222');d=ImageDraw.Draw(canvas)
for j in range(12):
 t=19+j*.5;cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
 if not ok:continue
 im=Image.fromarray(cv2.cvtColor(f,cv2.COLOR_BGR2RGB));im.save(out/f'v3-detail-{t:.1f}s.png')
 a=im.crop((1200,200,1510,350)).resize((500,242));b=im.crop((770,510,950,592)).resize((250,114))
 x=(j%2)*750;y=(j//2)*300;canvas.paste(a,(x,y+30));canvas.paste(b,(x+500,y+80));d.text((x+5,y+5),'%.1fs PC / phone'%t,fill='white')
canvas.save(out/'v3-detail-debug.png')
cap.release()
canvas=Image.new('RGB',(1000,4*260),'#222');d=ImageDraw.Draw(canvas)
for j,s in enumerate(meta[3]['samples']):
 im=Image.open(s['path']);canvas.paste(im.crop((1200,200,1510,350)).resize((500,242)),(0,j*260+18));canvas.paste(im.crop((770,510,950,592)).resize((500,228)),(500,j*260+18));d.text((5,j*260),'%.2fs PC / phone'%s['seconds'],fill='white')
canvas.save(out/'v3-paired-debug.png')
for m in meta:
 cap=cv2.VideoCapture(m['file'])
 for s in m['samples']:
  cap.set(cv2.CAP_PROP_POS_MSEC,s['seconds']*1000);ok,f=cap.read();s['actual_seconds']=cap.get(cv2.CAP_PROP_POS_MSEC)/1000
 cap.release()
(out/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
print([(m['id'],[(round(s['seconds'],2),round(s['actual_seconds'],2))for s in m['samples']])for m in meta])
