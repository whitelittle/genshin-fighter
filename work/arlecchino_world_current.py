from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,numpy as np
p=Path('outputs/arlecchino-actions-20261011');d=json.loads((p/'actions.json').read_text(encoding='utf-8'));items=[(k,i,f) for k,a in d.items() for i,f in enumerate(a['sourceFrames'])];font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
for page in range((len(items)+8)//9):
 out=Image.new('RGBA',(1950,1200),(238,242,248,255));draw=ImageDraw.Draw(out)
 for j,(k,i,f) in enumerate(items[page*9:(page+1)*9]):
  x=j%3*650;y=j//3*400;im=Image.open(p/f['file']).convert('RGBA');s=f['scale']*.8;im=im.resize((max(1,round(im.width*s)),max(1,round(im.height*s))));out.alpha_composite(im,(round(x+270-f['anchor'][0]*s),round(y+375-f['anchor'][1]*s)));draw.line((x,y+375,x+650,y+375),fill=(130,140,160));draw.text((x+10,y+10),f'{k} {i+1}',font=font,fill=(30,35,50))
 out.convert('RGB').save(p/f'evidence/world-current-{page}.jpg')
for k in ['standguard','crouch']:
 a=np.array(Image.open(p/'source'/f'{k}-v1.png'))[:,:,3];print(k,'alpha128 outer edge pixels',int((a[:,[0,-1]]>=128).sum()))
