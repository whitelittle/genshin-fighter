from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
p=Path('outputs/arlecchino-actions-20261011');d=json.loads((p/'actions.json').read_text(encoding='utf-8'));out=Image.new('RGBA',(1600,900),(238,242,248,255));draw=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
items=[(k,i,f) for k,a in d.items() for i,f in enumerate(a['sourceFrames'])]
for j,(k,i,f) in enumerate(items):
 x=j%4*400;y=j//4*450;im=Image.open(p/f['file']).convert('RGBA');s=f['scale'];im=im.resize((round(im.width*s),round(im.height*s)));out.alpha_composite(im,(round(x+200-f['anchor'][0]*s),round(y+410-f['anchor'][1]*s)));draw.line((x,y+410,x+400,y+410),fill=(130,140,160));draw.text((x+10,y+10),f'{k} {i+1} unit={s}',font=font,fill=(30,35,50))
out.convert('RGB').save(p/'evidence/initial-world-scale.jpg')
