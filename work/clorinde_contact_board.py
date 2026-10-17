from clorinde_assets import O
from PIL import Image,ImageDraw,ImageFont
import json
models=json.loads((O/'opponent-models.json').read_text(encoding='utf-8'))
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',15)
for model,poses in models.items():
 sheet=Image.new('RGBA',(1600,800),(235,238,244,255));draw=ImageDraw.Draw(sheet)
 for i,key in enumerate(['victim_0','victim_1','victim_2','victim_3','victim_4','victim_5','throw_0','throw_1','throw_2','throw_3']):
  p=poses[key];im=Image.open(O/p['file']).convert('RGBA');x=i%5*320;y=i//5*400
  z=3;sheet.alpha_composite(im.resize((im.width*z,im.height*z),Image.Resampling.NEAREST),(x+10,y+40))
  draw.text((x+5,y+5),f'{model} {key} ax{p["ax"]} ay{p["ay"]} u{p["scale"]:.2f}',fill=(20,25,40),font=font)
  for xx in range(0,im.width,10):draw.text((x+10+xx*z,y+30),str(xx),font=font,fill=(180,30,40))
  for yy in range(0,im.height,10):draw.text((x+5,y+40+yy*z),str(yy),font=font,fill=(180,30,40))
 sheet.convert('RGB').save(O/f'evidence/{model}-contact-board.jpg')
