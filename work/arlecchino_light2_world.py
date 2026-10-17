from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json
p=Path('outputs/arlecchino-actions-20261011');d=json.loads((p/'actions.json').read_text(encoding='utf-8'));out=Image.new('RGBA',(1800,900),(238,242,248,255));draw=ImageDraw.Draw(out);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
for j,f in enumerate(d['light2']['sourceFrames']):
 x=j%3*600;y=j//3*450;im=Image.open(p/f['file']).convert('RGBA');s=f['scale'];im=im.resize((round(im.width*s),round(im.height*s)));out.alpha_composite(im,(round(x+270-f['anchor'][0]*s),round(y+410-f['anchor'][1]*s)));draw.line((x,y+410,x+600,y+410),fill=(130,140,160));draw.text((x+10,y+10),f'light2 {j+1}',font=font,fill=(30,35,50))
out.convert('RGB').save(p/'evidence/light2-world-v2.jpg')
print([f['roi'] for f in d['light2']['sourceFrames']])
