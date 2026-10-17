"""Contact sheets / GIFs from encoded sprites and exported model states, not a device capture."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
root=Path(__file__).resolve().parents[1];a=root/'dist/assets';out=root/'dist/review';out.mkdir(exist_ok=True)
rig=json.loads((a/'neutral-rig-v6.json').read_text());font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f=lambda size:ImageFont.truetype(font,size)
banks={(k,m):Image.open(a/g[m]).convert('RGBA') for k,g in rig['groups'].items() for m in ['source','initial','optimized']}
def text(im,xy,s,size=24,color='#ede4d7'):ImageDraw.Draw(im).text(xy,s,font=f(size),fill=color)
def sprite(im,key,mode,i,x,y):
 g=rig['groups'][key];p=g['poses'][i];r=p['sourceRect'] if mode=='source' else p['atlasRect'];anchor=p['sourceAnchor'] if mode=='source' else p['anchor'];scale=g['displayScale'] if mode=='source' else 4
 crop=banks[key,mode].crop((r[0],r[1],r[0]+r[2],r[1]+r[3]));crop=crop.resize((round(r[2]*scale),round(r[3]*scale)),Image.Resampling.NEAREST)
 im.paste(crop,(round(x-anchor[0]*scale),round(y-anchor[1]*scale)),crop)
def floor(im,x0,x1,y):ImageDraw.Draw(im).line((x0,y,x1,y),fill='#7d6856',width=2)
def savegif(frames,path,durations):
 contact=Image.new('RGB',(frames[0].width,frames[0].height*len(frames)))
 for i,im in enumerate(frames):contact.paste(im,(0,i*im.height))
 palette=contact.quantize(256)
 converted=[im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
 converted[0].save(path,save_all=True,append_images=converted[1:],duration=durations,loop=0,disposal=2,optimize=False)
neutral=[]
for step in range(12):
 im=Image.new('RGB',(1500,990),'#191b20');text(im,(35,18),'MAVUIKA / NEUTRAL CYCLES - V06 CANDIDATES',30)
 for row,key in enumerate(['idle','walk','backwalk']):
  y=70+row*300;text(im,(35,y),key.upper(),22,'#efb16c');i=step//6 if key=='idle' else step%6
  for col,mode in enumerate(['source','initial','optimized']):
   x=230+col*500;floor(im,col*500+20,col*500+480,y+268);text(im,(col*500+45,y+38),mode.upper(),18,'#aeb2bb');sprite(im,key,mode,i,x,y+268)
 text(im,(35,964),'Support alignment and gait candidates; not game/device acceptance.',17,'#aeb2bb');neutral.append(im)
savegif(neutral,out/'mavuika-neutral-v6.gif',[180]*12)
states=json.loads((root/'production/light1-playback-v6.json').read_text());frames=[]
for s in states['frames']:
 im=Image.new('RGB',(1500,490),'#191b20');text(im,(35,18),'MAVUIKA / LIGHT ATTACK 1 - 4x SLOW REVIEW',28)
 text(im,(35,59),f"tick {s['tick']:02}/36   {s['phase'].upper()}   hits {s['hits']}   hitstop {s['stop']}",20,'#efb16c')
 for col,mode in enumerate(['source','initial','optimized']):
  x=230+col*500;floor(im,col*500+20,col*500+480,395);text(im,(col*500+45,98),mode.upper(),18,'#aeb2bb')
  d=ImageDraw.Draw(im);d.rectangle((x+132,215,x+168,395),fill='#55624a' if s['hits'] else '#404651')
  if 14<=s['tick']<=16:d.rectangle((x+83,395-118,x+226,395-91),outline='#efb16c',width=2)
  sprite(im,'light1',mode,s['pose'],x,395)
 text(im,(35,441),'One geometry-candidate strike at tick 14; 6-tick hitstop. Formal engine pending.',19,'#aeb2bb');frames.append(im)
savegif(frames,out/'mavuika-light1-v6.gif',[(round((i+1)*1000/60*4/10)-round(i*1000/60*4/10))*10 for i in range(len(frames))])
sheet=Image.new('RGB',(1600,1000),'#191b20');text(sheet,(35,22),'MAVUIKA / V06 - LIGHT ATTACK 1 AND OUTLINE FIX',32)
text(sheet,(35,83),'Prepare / release / active / recover - source pose sequence',22,'#efb16c')
for i,label in enumerate(['PREPARE','RELEASE','ACTIVE','RECOVER']):
 floor(sheet,i*400+12,i*400+388,370);sprite(sheet,'light1','source',i,190+i*400,370);text(sheet,(25+i*400,389),label,18,'#aeb2bb')
text(sheet,(35,457),'Idle comparison / original source - previous inner outline - new outward outline',23,'#efb16c')
sprite(sheet,'idle','source',0,280,790)
old=json.loads((a/'neutral-rig-v5.json').read_text());g=old['groups']['idle'];p=g['poses'][0];r=p['atlasRect'];crop=Image.open(a/g['optimized']).convert('RGBA').crop((r[0],r[1],r[0]+r[2],r[1]+r[3])).resize((r[2]*4,r[3]*4),Image.Resampling.NEAREST)
anchor=rig['groups']['idle']['poses'][0]['sourceAnchor'];sheet.paste(crop,(round(800-anchor[0]*.24),round(790-anchor[1]*.24)),crop)
sprite(sheet,'idle','optimized',0,1320,790)
for i,label in enumerate(['SOURCE','V05 / INNER OUTLINE','V06 / INTERIOR PRESERVED']):floor(sheet,i*520+35,i*520+505,790);text(sheet,(55+i*520,811),label,21,'#aeb2bb')
text(sheet,(35,901),'18 pose candidates; clearer interior colors cost more rectangles.',23,'#efb16c')
text(sheet,(35,944),'Gait, grips, full 25 actions and formal combat/device checks remain pending.',19,'#aeb2bb')
sheet.save(out/'mavuika-v6-review.png')
print(json.dumps({'files':[str(out/f) for f in ['mavuika-neutral-v6.gif','mavuika-light1-v6.gif','mavuika-v6-review.png']],'lightFrames':len(frames),'neutralFrames':len(neutral)}))
