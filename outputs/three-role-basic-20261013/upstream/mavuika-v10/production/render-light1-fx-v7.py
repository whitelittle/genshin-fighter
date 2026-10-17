"""Offline composite from exported deterministic FX/model frames; not game capture."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math
root=Path(__file__).resolve().parents[1];a=root/'dist/assets';out=root/'dist/review';out.mkdir(exist_ok=True)
body=json.loads((a/'neutral-rig-v6.json').read_text())['groups'];fx=json.loads((a/'light1-fx-rig-v7.json').read_text());target=json.loads((a/'v3-target-rig-v7.json').read_text());play=json.loads((root/'production/light1-fx-playback-v7.json').read_text())
images={('body',key,mode):Image.open(a/g[mode]).convert('RGBA') for key,g in body.items() for mode in ['source','initial','optimized']}
images['target']=Image.open(a/target['file']).convert('RGBA');images['flash']=Image.open(a/'v3-target-flash-v7.png').convert('RGBA');images['fx-source']=Image.open(a/fx['source']).convert('RGBA');images['fx-fit']=Image.open(a/fx['fit']).convert('RGBA')
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=lambda n:ImageFont.truetype(font,n)
def text(im,x,y,value,n=22,color='#ebe0d0'):ImageDraw.Draw(im).text((x,y),value,font=f(n),fill=color)
def stamp(im,image,rect,anchor,scale,x,y,facing=1,alpha=1,rotation=0,zoom=1.25):
 crop=image.crop((rect[0],rect[1],rect[0]+rect[2],rect[1]+rect[3]));size=(max(1,round(rect[2]*scale*zoom)),max(1,round(rect[3]*scale*zoom)))
 crop=crop.resize(size,Image.Resampling.NEAREST);local=Image.new('RGBA',(size[0]*3+40,size[1]*3+40));pivot=(size[0]+20,size[1]+20)
 local.paste(crop,(round(pivot[0]-anchor[0]*scale*zoom),round(pivot[1]-anchor[1]*scale*zoom)))
 # Keep anchor fixed during rotation/mirror, including asymmetric contact frames.
 if rotation:local=local.rotate(-rotation,Image.Resampling.NEAREST,center=pivot)
 if facing<0:
  local=local.transpose(Image.Transpose.FLIP_LEFT_RIGHT);pivot=(local.width-1-pivot[0],pivot[1])
 if alpha<1:local.putalpha(local.getchannel('A').point(lambda v:round(v*alpha)))
 im.paste(local,(round(x-pivot[0]),round(y-pivot[1])),local)
def scene(im,s,top=0,material='optimized',layer='all',label=''):
 d=ImageDraw.Draw(im);floor=top+360;actor=365;zoom=1.25
 d.line((25,floor,975,floor),fill='#7d6856',width=2);text(im,30,top+12,label,26,'#efb16c');text(im,30,top+50,f"tick {s['tick']:02}/36  hits {s['hits']}  blocks {s['blocked']}  stop {s['stop']}",18,'#b9b3a8')
 if layer!='fx':
  rec=s['receiver'];p=target['poses'][rec['pose']];stamp(im,images['target'],p['rect'],p['anchor'],p['scale'],actor+(rec['x']-p['offsetX'])*zoom,floor-rec['y']*zoom,-1)
  if rec['flash'] and layer=='all':stamp(im,images['flash'],p['rect'],p['anchor'],p['scale'],actor+(rec['x']-p['offsetX'])*zoom,floor-rec['y']*zoom,-1,rec['flash'])
  key='idle' if s['ended'] else 'light1';g=body[key];index=0 if s['ended'] else 0 if s['tick']<10 else 1 if s['tick']<14 else 2 if s['tick']<=16 else 3;p=g['poses'][index]
  stamp(im,images['body',key,material],p['sourceRect'] if material=='source' else p['atlasRect'],p['sourceAnchor'] if material=='source' else p['anchor'],g['displayScale'] if material=='source' else 4,actor+s['x']*zoom,floor-s['y']*zoom)
 if layer!='actors':
  for e in s['effects']:
   p=fx['frames'][e['index']];source=material=='source';stamp(im,images['fx-source' if source else 'fx-fit'],p['sourceRect'] if source else p['rect'],p['sourceAnchor'] if source else p['anchor'],p['sourceScale'] if source else p['scale'],actor+e['x']*zoom,floor-e['y']*zoom,e['facing'],e['alpha'],e['rotation'])
 text(im,30,top+380,'V3 loaded opponent poses / independent geometry+FX candidate',16,'#999da8')
frames=[];cases=['hit','block','miss'];count=max(len(play['cases'][k]) for k in cases)
for i in range(count):
 im=Image.new('RGB',(1000,1270),'#191b20')
 for row,(key,label) in enumerate(zip(cases,['HIT / WARM CONTACT','BLOCK / COOL CONTACT','MISS / NO CONTACT BURST'])):
  seq=play['cases'][key];scene(im,seq[min(i,len(seq)-1)],row*420,label=label)
 frames.append(im)
palette=Image.new('RGB',(1000,1270*3))
for i,index in enumerate([0,min(16,count-1),min(20,count-1)]):palette.paste(frames[index],(0,i*1270))
pal=palette.quantize(256);gif=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in frames]
durations=[(round((i+1)*1000/60*4/10)-round(i*1000/60*4/10))*10 for i in range(count)];durations[-1]+=500
gif[0].save(out/'mavuika-fx-branches-v7.gif',save_all=True,append_images=gif[1:],duration=durations,loop=0,disposal=2,optimize=False)
# Show source+SD effects separately and composed at the exact contact peak.
sheet=Image.new('RGB',(1500,1250),'#191b20');text(sheet,35,15,'MAVUIKA / V07 INDEPENDENT FX AND PAIRED CONTACT',30)
for row in range(3):
 for col in range(4):
  p=fx['frames'][row*4+col];x=col*375+65;y=70+row*125
  source=images['fx-source'];stamp(sheet,source,p['sourceRect'],p['sourceAnchor'],p['sourceScale'],x+85,y+50,zoom=.85)
  stamp(sheet,images['fx-fit'],p['rect'],p['anchor'],p['scale'],x+220,y+50,zoom=.85)
  text(sheet,x-20,y+82,p['id'],16,'#b9b3a8')
contact=next(s for s in play['cases']['hit'] if any(e['index']==5 for e in s['effects']))
for row,(layer,label) in enumerate([('all','COMPOSITE / HIT'),('actors','ACTORS / FX OFF')]):
 panel=Image.new('RGB',(1000,420),'#191b20');scene(panel,contact,material='optimized',layer=layer,label=label);sheet.paste(panel.resize((750,315)),(row*750,475))
panel=Image.new('RGB',(1000,420),'#191b20');scene(panel,contact,material='optimized',layer='fx',label='FX ONLY / SAME WORLD ANCHORS');sheet.paste(panel,(250,800))
text(sheet,35,1210,'Original RGBA retained; 12 FX stages. Formal engine, Q/bike FX and device acceptance pending.',18,'#b9b3a8');sheet.save(out/'mavuika-fx-sheet-v7.png')
# Export separate branches for enlarged viewing.
for key in cases:
 branch=[]
 for s in play['cases'][key]:
  im=Image.new('RGB',(1000,420),'#191b20');scene(im,s,label=key.upper());branch.append(im.quantize(palette=pal,dither=Image.Dither.NONE))
 timing=[(round((i+1)*1000/60*4/10)-round(i*1000/60*4/10))*10 for i in range(len(branch))];timing[-1]+=500
 branch[0].save(out/f'mavuika-light1-{key}-v7.gif',save_all=True,append_images=branch[1:],duration=timing,loop=0,disposal=2,optimize=False)
print(json.dumps({'combined':str(out/'mavuika-fx-branches-v7.gif'),'sheet':str(out/'mavuika-fx-sheet-v7.png'),'frames':count,'durationMs':sum(durations),'scope':'offline CPU composite; not browser/game/device capture'}))
