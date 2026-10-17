from clorinde_assets import O
from PIL import Image,ImageDraw,ImageFont
import json
data=json.loads((O/'actions.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)
items=[(k,i,f) for k,d in data.items() for i,f in enumerate(d['sourceFrames'])]
for page in range((len(items)+11)//12):
 out=Image.new('RGBA',(1600,1200),(234,237,244,255));draw=ImageDraw.Draw(out)
 for j,(k,i,f) in enumerate(items[page*12:(page+1)*12]):
  x=j%4*400;y=j//4*400;im=Image.open(O/f['file']).convert('RGBA');s=f['scale']*.8
  im=im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))))
  out.alpha_composite(im,(round(x+200-f['anchor'][0]*s),round(y+375-f['anchor'][1]*s)))
  draw.text((x+5,y+5),f'{k} {i+1} {f["scale"]:.3f}',font=font,fill=(30,35,55));draw.line((x,y+375,x+400,y+375),fill=(130,140,160))
 out.convert('RGB').save(O/f'evidence/world-size-{page}.jpg')
