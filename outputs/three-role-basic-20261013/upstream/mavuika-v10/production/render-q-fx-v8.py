from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont,ImageOps
r=Path(__file__).resolve().parents[1];a=r/'dist/assets';out=r/'dist/review';out.mkdir(exist_ok=True)
rig=json.loads((a/'rig.json').read_text());fx=json.loads((a/'q-fx-rig-v8.json').read_text());lfx=json.loads((a/'light1-fx-rig-v7.json').read_text());target=json.loads((a/'v3-target-rig-v7.json').read_text());states=json.loads((r/'production/q-fx-playback-v8.json').read_text());images={}
def img(name):
 if name not in images:images[name]=Image.open(a/name).convert('RGBA')
 return images[name]
def stamp(canvas,name,p,x,y,scale,alpha=1):
 rx,ry,w,h=p['rect'];im=img(name).crop((rx,ry,rx+w,ry+h));im=im.resize((max(1,round(w*scale)),max(1,round(h*scale))),Image.Resampling.NEAREST)
 if alpha!=1:im.putalpha(im.getchannel('A').point(lambda v:round(v*alpha)))
 canvas.paste(im,(round(x-p['anchor'][0]*scale),round(y-p['anchor'][1]*scale)),im)
def scene(item,mode='optimized',layers=True):
 s=item['state'];f=item['frame'];im=Image.new('RGB',(1200,580),'#161519');d=ImageDraw.Draw(im);d.rectangle((0,451,1200,580),fill='#211b19');d.line((0,450,1200,450),fill='#6e4430')
 rec=f['receiver'];p=target['poses'][rec['pose']];stamp(im,target['file'],p,rec['x'],rec['y'],p['scale'])
 if rec['flash']:stamp(im,'v3-target-flash-v7.png',p,rec['x'],rec['y'],p['scale'],.45)
 b=f['body'];bank=rig['materials'][mode];p=bank['poses'][b['pose']];stamp(im,p.get('file',bank['file']),p,b['x'],b['y'],p['scale'])
 if layers:
  for l in f['layers']:
   bank=lfx if l['bank']=='light' else fx;p=next(p for p in bank['frames'] if p['id']==l['id']);stamp(im,bank['fit'],p,l['x'],l['y'],p['scale']*l['mult'],l['alpha'])
 d.text((24,20),f"V8 {s['action']} / {s['outcome']} / tick {s['tick']} / damage {s['hits']}",fill='white');d.text((24,550),'Independent FX candidate | contacts selected in preview | choreography pending',fill='#cba88b')
 return im
seq=states['q-hit'];frames=[scene(x).resize((900,435)) for x in seq];frames[0].save(out/'mavuika-q-fx-v8.gif',save_all=True,append_images=frames[1:],duration=[50]*(len(frames)-1)+[600],loop=0,optimize=False)
seqs=[states['heavy-'+o] for o in ['hit','block','miss']];n=max(map(len,seqs));frames=[]
for i in range(n):
 im=Image.new('RGB',(900,900));
 for j,seq in enumerate(seqs):im.paste(scene(seq[min(i,len(seq)-1)]).resize((900,300)),(0,j*300))
 frames.append(im)
frames[0].save(out/'mavuika-bike-fx-v8.gif',save_all=True,append_images=frames[1:],duration=[65]*(n-1)+[500],loop=0,optimize=False)
# Key stages and unmasked bodies; include contact plus brake recovery.
keys=[('q-hit',20),('q-hit',48),('q-hit',55),('heavy-hit',20),('heavy-block',20),('heavy-miss',45)]
sheet=Image.new('RGB',(1200,870),'#161519')
for i,(key,tick) in enumerate(keys):item=next(x for x in states[key] if x['state']['tick']==tick);sheet.paste(scene(item).resize((600,290)),(i%2*600,i//2*290))
sheet.save(out/'mavuika-q-bike-fx-v8.png')
scene(next(x for x in states['q-hit'] if x['state']['tick']==55)).save(out/'mavuika-q-impact-v8.png')
print('Q, bike branch GIFs and key stage PNG generated')
