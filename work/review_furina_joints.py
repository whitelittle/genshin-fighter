"""Coordinate sheets at native source resolution; never auto-certify anatomy."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
data=json.loads((O/'actions.json').read_text(encoding='utf-8'))
for label,key in [('前走','walk'),('后退','backwalk'),('蹲轻','crouchlight'),('蹲下','crouch'),('蹲重','crouchheavy'),('空轻','airlight'),('空重','airheavy'),('站立格挡','standguard'),('蹲防','crouchguard'),('被投','victim'),('胜利','victory'),('受击与倒地','hurt')]:
 fs=data[label]['sourceFrames'];ims=[Image.open(O/f['file']).convert('RGBA') for f in fs]
 w=max(im.width for im in ims)+20;h=max(im.height for im in ims)+30
 sheet=Image.new('RGBA',(3*w,math.ceil(len(ims)/3)*h),'#777780');d=ImageDraw.Draw(sheet)
 for i,im in enumerate(ims):
  ox=i%3*w;oy=i//3*h+25;sheet.alpha_composite(im,(ox,oy));d.text((ox,oy-23),f'{label} {i} {im.width}×{im.height}',font=font,fill='white')
  for y in range(0,im.height,100):d.line((ox,oy+y,ox+im.width,oy+y),fill='#ffffff55');d.text((ox,oy+y),str(y),font=font,fill='white')
  for x in range(0,im.width,100):d.line((ox+x,oy,ox+x,oy+im.height),fill='#ffffff55');d.text((ox+x,oy+10),str(x),font=font,fill='white')
 sheet.convert('RGB').save(O/f'{key}-coordinate-review.jpg')
