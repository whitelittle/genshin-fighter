from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'work/optimization-test-deps'))
from lupa.lua53 import LuaRuntime
O=R/'outputs/six-character-size-20261013';O.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
rt=LuaRuntime(unpack_returned_tuples=True);rt.execute((R/'runtime/dist/genshin_fighter.lua').read_text(encoding='utf-8'))
A=rt.globals().GF_REQUIRE('gf_animation_data')
records=[]
for key in ['raiden','nahida']:
 bank=A[key].lo
 for pose,img in bank.items():
  if hasattr(img,'items') and img.n:records.append({'key':key,'pose':pose,'w':img.w,'h':img.h,'u':img.u})
(O/'legacy-source-units.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
for key in ['clorinde','arlecchino']:
 folder=R/f'outputs/{key}-actions-20261011';bank=json.loads((folder/'actions.json').read_text(encoding='utf-8'))
 rows=[]
 for label,g in bank.items():
  strip=Image.new('RGBA',(210*3,280),(96,100,115,255));d=ImageDraw.Draw(strip);d.line((0,265,strip.width,265),fill='white')
  for i,f in enumerate([bank['idle']['frames'][0],g['frames'][0],g['frames'][-1]]):
   im=Image.open(folder/f['file']).convert('RGBA');scale=f['scale']*.62
   im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
   strip.alpha_composite(im,(105+i*210-round(f['anchor'][0]*scale),265-round(f['anchor'][1]*scale)))
   d.text((i*210+4,4),f'{label} '+['待机','首帧','尾帧'][i],font=font,fill='white')
  rows.append(strip)
 for page in range((len(rows)+4)//5):
  subs=rows[page*5:page*5+5];board=Image.new('RGBA',(630,len(subs)*280))
  for j,row in enumerate(subs):board.alpha_composite(row,(0,j*280))
  board.convert('RGB').save(O/f'{key}-before-{page}.png')
print([(r['key'],r['pose'],r['u']) for r in records if r['pose'].endswith('_0')])
ART=rt.globals().GF_REQUIRE('gf_art')
pairs={'idle':['basic_0','basic_1'],'walk':['basic_2','basic_7'],'back':['basic_7','basic_2'],'jump':['move_0','move_3'],'dash':['move_4','move_5'],'backdash':['move_6','move_7'],'crouch':['guard_0','guard_1'],'block':['guard_6','guard_6'],'cblock':['guard_7','guard_7'],'light1':['light_0','light_3'],'light2':['light_4','light_7'],'light3':['heavy_0','heavy_3'],'heavy':['heavy_4','heavy_7'],'crouchLight':['air_0','air_1'],'crouchHeavy':['air_2','air_3'],'airLight':['air_4','air_5'],'airHeavy':['air_6','air_7'],'skill':['skill_0','skill_3'],'burst':['qburst_0','qburst_3'],'throw':['throw_0','throw_3'],'thrown':['victim_0','victim_3'],'hurt':['hurt_0','hurt_3'],'getup':['hurt_4','hurt_5'],'win':['hurt_6','hurt_6'],'lose':['hurt_7','hurt_7']}
for key in ['raidenshogun','nahida']:
 rows=[]
 for label,ps in pairs.items():
  if key=='nahida' and label=='burst':ps=['skill_4','skill_7']
  strip=Image.new('RGBA',(630,280),(96,100,115,255));d=ImageDraw.Draw(strip);d.line((0,265,630,265),fill='white')
  for i,pose in enumerate(['basic_0',*ps]):
   img=ART.pose(key,'lo',pose);b=img.bytes;pal=img.pal
   # Current Art returns baked world-space rectangles. Draw at a common world scale.
   for k in range(img.n):
    o=k*5;x,y,w,h,c=[b[o+j] for j in range(1,6)];col=tuple(pal[int(c)+1].values())
    x0=105+i*210+((img.ox or 0)+x-img.ax)*.62;y0=265+(y-img.ay)*.62
    d.rectangle((round(x0),round(y0),round(x0+w*.62),round(y0+h*.62)),fill=col)
   d.text((i*210+4,4),label+' '+['待机','首帧','尾帧'][i],font=font,fill='white')
  rows.append(strip)
 for page in range(5):
  board=Image.new('RGBA',(630,1400));subs=rows[page*5:page*5+5]
  for j,row in enumerate(subs):board.alpha_composite(row,(0,j*280))
  board.convert('RGB').save(O/f'{key}-before-{page}.png')
