"""Fixed world-scale source/fit/white/dark sheets and slowed preview GIFs."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
data=json.loads((O/'actions.json').read_text(encoding='utf-8'))

def pose(canvas,f,x,y):
 im=Image.open(O/f['file']).convert('RGBA');sx=f.get('scaleX',f['scale']);sy=f.get('scaleY',f['scale'])
 im=im.resize((round(im.width*sx),round(im.height*sy)),Image.Resampling.NEAREST)
 canvas.alpha_composite(im,(round(x-f['anchor'][0]*sx),round(y-f['anchor'][1]*sy)))

for key,label in [('forwarddash','前冲'),('backdash','后撤'),('jump','跳跃'),('defeat','败北')]:
 d=data[label]
 for mode in ['source','fit']:
  fs=d['sourceFrames'] if mode=='source' else d['frames']
  for bgname,bg in [('white','#ffffff'),('dark','#171625')]:
   sheet=Image.new('RGBA',(1200,math.ceil(len(fs)/3)*460),bg);draw=ImageDraw.Draw(sheet)
   for i,f in enumerate(fs):
    ox=i%3*400;oy=i//3*460
    draw.line((ox,oy+425,ox+400,oy+425),fill='#8d8b98')
    pose(sheet,f,ox+180,oy+425)
    draw.text((ox+12,oy+12),f'{label} {i+1} · {d["phases"][i]}',font=font,fill='#383446' if bgname=='white' else '#f0eaff')
   sheet.convert('RGB').save(O/f'{key}-{mode}-{bgname}-review.png')
  scenes=[]
  for i,f in enumerate(fs):
   scene=Image.new('RGBA',(800,600),'#171625');draw=ImageDraw.Draw(scene)
   draw.line((0,520,800,520),fill='#8d8b98');mx,my=d['motion'][i]
   pose(scene,f,400+mx,520+my)
   draw.text((20,20),f'{label} · {d["phases"][i]} · 慢放4×',font=font,fill='#f0eaff')
   scenes.append(scene.convert('RGB'))
  scenes[0].save(O/f'{key}-{mode}-review.gif',save_all=True,append_images=scenes[1:],duration=[max(70,round(t*1000/60*4)) for t in d['durations']],loop=0,disposal=2)
 print(key,'rendered')
