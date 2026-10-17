"""World-space pose contact sheets, from the actual runtime provider images."""
from pathlib import Path
import sys,json,argparse,math
R=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(R/'work/optimization-test-deps'))
from lupa.lua53 import LuaRuntime
from PIL import Image,ImageDraw,ImageFont
KEYS=['raidenshogun','nahida','furina','kamisatoayaka','clorinde','arlecchino']
LEGACY={'idle':['basic_0','basic_1'],'walk':[f'basic_{i}' for i in range(2,8)],'back':[f'basic_{i}' for i in range(7,1,-1)],'hurt':[f'hurt_{i}' for i in range(4)],'getup':['hurt_4','hurt_5'],'jump':[f'move_{i}' for i in range(4)],'dash':['move_4','move_5'],'backdash':['move_6','move_7'],'crouch':['guard_0','guard_1'],'block':['guard_6'],'cblock':['guard_7'],'light1':[f'light_{i}' for i in range(4)],'light2':[f'light_{i}' for i in range(4,8)],'light3':[f'heavy_{i}' for i in range(4)],'heavy':[f'heavy_{i}' for i in range(4,8)],'crouchLight':['air_0','air_1'],'crouchHeavy':['air_2','air_3'],'airLight':['air_4','air_5'],'airHeavy':['air_6','air_7'],'skill':[f'skill_{i}' for i in range(4)],'burst':[f'qburst_{i}' for i in range(4)],'throw':[f'throw_{i}' for i in range(4)],'thrown':[f'victim_{i}' for i in range(4)],'win':['hurt_6'],'lose':['hurt_7']}
ORDER=list(LEGACY)
def sprite(img):
 b=img.bytes;p=img.pal
 x0=math.floor(-img.ax+(img.ox or 0));y0=math.floor(-img.ay)
 im=Image.new('RGBA',(math.ceil(img.w)+3,math.ceil(img.h)+3));d=ImageDraw.Draw(im)
 for n in range(img.n):
  o=n*5;x,y,w,h,c=[b[o+i] for i in range(1,6)]
  d.rectangle((round(x),round(y),round(x+w)-1,round(y+h)-1),fill=tuple(p[int(c)+1][i] for i in range(1,5)))
 return im,x0,y0
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=R/'runtime/dist/genshin_fighter.lua');ap.add_argument('--out',type=Path,required=True);ap.add_argument('--keys',default=','.join(KEYS));a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 rt=LuaRuntime(unpack_returned_tuples=True);rt.execute(a.source.read_text(encoding='utf-8'));art=rt.globals().GF_REQUIRE('gf_art');reg=rt.globals().GF_REQUIRE('gf_character_registry');font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
 records=[]
 for key in a.keys.split(','):
  provider=reg.provider(key);groups={g:list(v.frames.values()) for g,v in provider.data.groups.items()} if provider else dict(LEGACY)
  if key=='nahida':groups['burst']=[f'skill_{i}' for i in range(4,8)]
  rows=[]
  for group in ORDER:
   seq=groups[group]
   for offset in range(0,len(seq),6):
    row=Image.new('RGBA',(7*210,320),(86,111,112,255));d=ImageDraw.Draw(row);d.line((0,302,row.width,302),fill=(210,225,210))
    for col,pose in enumerate([groups['idle'][0]]+seq[offset:offset+6]):
     img=art.pose(key,'lo',pose);im,x,y=sprite(img);scale=.72
     im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
     row.alpha_composite(im,(col*210+105+round(x*scale),302+round(y*scale)))
     d.text((col*210+4,4),'idle reference' if col==0 else f'{group} {offset+col-1}: {pose}',font=font,fill='white')
     records.append({'key':key,'action':group,'pose':pose,'worldWidth':img.w,'worldHeight':img.h})
    rows.append(row)
  for page in range((len(rows)+4)//5):
   part=rows[page*5:page*5+5];board=Image.new('RGBA',(1470,320*len(part)))
   for i,row in enumerate(part):board.alpha_composite(row,(0,i*320))
   board.convert('RGB').save(a.out/f'{key}-{page}.png')
  print(key,len(rows),'rows',flush=True)
 (a.out/'poses.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
if __name__=='__main__':main()
