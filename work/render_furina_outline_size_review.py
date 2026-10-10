from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
d=json.loads((O/'actions-size-candidate.json').read_text(encoding='utf-8'))
foe=json.loads((O/'foe-fitted.json').read_text(encoding='utf-8'))['basic_0']
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
choices=[('待机基准','待机',0),('胜利 · 站定（同待机）','胜利',0),('胜利 · 提帽','胜利',1),('胜利 · 谢幕','胜利',2),('胜利 · 恢复（同待机）','胜利',3),('轻攻三 · 准备','轻攻三',0)]
for name,bg,ink in [('white','#ffffff','#302b45'),('dark','#171625','#f0eaff')]:
 sheet=Image.new('RGBA',(1950,1000),bg);draw=ImageDraw.Draw(sheet)
 for i,(title,label,index) in enumerate(choices):
  ox=i%3*650;oy=i//3*500;y=oy+465
  draw.text((ox+15,oy+12),title+' / 拟合雷神待机',font=font,fill=ink)
  draw.line((ox,y,ox+650,y),fill='#8d8b98')
  f=d[label]['frames'][index];im=Image.open(O/f['file']).convert('RGBA');s=f['scale']
  im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
  sheet.alpha_composite(im,(round(ox+150-f['anchor'][0]*s),round(y-f['anchor'][1]*s)))
  im=Image.open(O/foe['file']).convert('RGBA');s=foe['scale']
  im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
  sheet.alpha_composite(im,(round(ox+480-foe['ax']*s),round(y-foe['ay']*s)))
 filename=f'outline-size-{name}-review.png';sheet.convert('RGB').save(O/filename)
 served=R/'work/github-review-20261009/V3/assets/action-reference/furina'
 if served.is_dir():shutil.copy2(O/filename,served/filename)
print('white/dark fixed world-scale review rendered')
