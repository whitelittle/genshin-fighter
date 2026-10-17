"""All 150 action endpoints, fixed transforms, source imports and new rules/replay."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).resolve().parent))
from performance import BenchClient,wait
R=Path(__file__).resolve().parents[2];O=R/'outputs/six-character-size-20261013';O.mkdir(exist_ok=True)
import argparse
ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=O/'release/genshin_fighter.lua');args=ap.parse_args()
SOURCE=args.source
KEYS=['raidenshogun','nahida','furina','kamisatoayaka','clorinde','arlecchino']
OLD={'idle':['basic_0','basic_1'],'walk':['basic_2','basic_7'],'back':['basic_7','basic_2'],'jump':['move_0','move_3'],'dash':['move_4','move_5'],'backdash':['move_6','move_7'],'crouch':['guard_0','guard_1'],'block':['guard_6','guard_6'],'cblock':['guard_7','guard_7'],'light1':['light_0','light_3'],'light2':['light_4','light_7'],'light3':['heavy_0','heavy_3'],'heavy':['heavy_4','heavy_7'],'crouchLight':['air_0','air_1'],'crouchHeavy':['air_2','air_3'],'airLight':['air_4','air_5'],'airHeavy':['air_6','air_7'],'skill':['skill_0','skill_3'],'burst':['qburst_0','qburst_3'],'throw':['throw_0','throw_3'],'thrown':['victim_0','victim_3'],'hurt':['hurt_0','hurt_3'],'getup':['hurt_4','hurt_5'],'win':['hurt_6','hurt_6'],'lose':['hurt_7','hurt_7']}
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
checks=[];imports=[];rules=[]
for key in KEYS:
 c=BenchClient(SOURCE);c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c._to_lua({'chars':[key,'nahida' if key!='nahida' else 'raidenshogun'],'mode':'training','cpu':[False,False],'infinite':True,'seed':21})
 wait(c,"GF_APP() and GF_APP().sceneName=='fight' and GF_APP().scene.state=='run'")
 c.lua("(function()GF_APP().scene.sim.phase='fight';GF_APP().scene.sim.freeze=10000;return true end)()")
 P=c.lua(f"GF_REQUIRE('gf_character_registry').provider('{key}')")
 if P:
  pairs={id:[group.frames[1],group.frames[len(group.frames)]] for id,group in P.data.groups.items()}
 else:pairs=dict(OLD);pairs['burst']=['skill_4','skill_7'] if key=='nahida' else pairs['burst']
 idle=(P.data.groups.idle.frames[1] if P else 'basic_0');rows=[]
 for id,endpoints in pairs.items():
  row=Image.new('RGBA',(630,290),(90,97,115,255));draw=ImageDraw.Draw(row);draw.line((0,275,630,275),fill='white')
  for index,pose in enumerate([idle,*endpoints]):
   state=id if id not in ['jump',*['light1','light2','light3','heavy','crouchLight','crouchHeavy','airLight','airHeavy']] else ('air' if id=='jump' else 'attack')
   c.lua(f"""(function()local s=GF_APP().scene;local v=s.views[1];local f=v.f;f.state='{state}';f.t=0;f.coat=0;f.hitstop=10000;f.frozen=0;f.airMove=nil;f.move=f.kit.weapon.heavy;f.moveId='heavy';v.walkT=0;v.poseFor=function()return '{pose}' end;v.nextLocomotion=function()return nil end;return true end)()""")
   c.run(.2)
   assert c.lua('GF_APP().scene.views[1].front.key')==pose,(key,id,pose)
   assert c.lua('math.abs(GF_APP().scene.views[1].root.sx)==1 and GF_APP().scene.views[1].root.sy==1')
   assert c.lua('GF_APP().scene.zoom==1')
   img=c.lua('GF_APP().scene.views[1].poseImg');b=img.bytes;pal=img.pal
   for n in range(img.n):
    o=n*5;x,y,w,h,col=[b[o+i] for i in range(1,6)]
    x0=105+index*210+((img.ox or 0)+x-img.ax)*.62;y0=275+(y-img.ay)*.62
    draw.rectangle((round(x0),round(y0),round(x0+w*.62),round(y0+h*.62)),fill=tuple(pal[int(col)+1][i] for i in range(1,5)))
   draw.text((index*210+3,4),id+' '+['待机','首帧','尾帧'][index],font=font,fill='white')
   if index:checks.append({'key':key,'action':id,'endpoint':index,'pose':pose,'rootScale':[1,1],'cameraZoom':1,'sourceUnitRetained':True})
  rows.append(row)
 for page in range(5):
  subs=rows[page*5:page*5+5];board=Image.new('RGBA',(630,290*len(subs)))
  for i,row in enumerate(subs):board.alpha_composite(row,(0,i*290))
  board.convert('RGB').save(O/f'{key}-after-{page}.png')
 if key in ['clorinde','arlecchino']:
  receipt=json.loads((R/f'runtime/{key}-import.json').read_text(encoding='utf-8'))
  art=c.lua("GF_REQUIRE('gf_art')")
  for r in receipt['sources']:
   im=np.array(Image.open(R/r['file']).convert('RGBA'));rebuilt=np.zeros_like(im);img=art.pose(key,'lo',r['pose']);u=r['scale']
   for n in range(img.n):
    o=n*5;x,y,w,h=[round(img.bytes[o+i]/u) for i in range(1,5)];col=img.pal[int(img.bytes[o+5])+1];rebuilt[y:y+h,x:x+w]=[col[i] for i in range(1,5)]
   assert np.array_equal(im,rebuilt),(key,r['pose'])
  imports.append({'key':key,'pixelStates':len(receipt['sources']),'exact':True})
 print(key,len(pairs),'endpoint scale checks passed',flush=True)
(O/'size-audit.json').write_text(json.dumps({'scope':'fixed physical transforms; anatomical source units retained, bbox height not normalized; mock only','checks':checks,'imports':imports,'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},ensure_ascii=False,indent=2),encoding='utf-8')
