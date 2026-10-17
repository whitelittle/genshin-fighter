"""Contact sheets for visual review only, never silently accepts legacy art."""
from pathlib import Path
import json,math
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];V=R/'work/v4-handoff-20261009-partial/V4'
O=R/'outputs/clorinde-actions-20261011'
MAP={'idle':'clorinde-idle-review','walk':'clorinde-walk-review','light1':'clorinde-light1-review',
 'light2':'actions-20261009/clorinde-light2-body-v1','E':'clorinde-E-review',
 **{k:f'full-delivery-20261009/clorinde-{k}-body-full-v1' for k in ['light3','heavy','crouchlight','crouchheavy']},
 **{k:f'codex-batch-20261009/clorinde-{k}-body-v{v}' for k,v in [('backwalk',2),('jump',1),('standguard',2),('hit_knockdown',1),('wakeup',1)]}}
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
records=[]
for batch in range(2):
 subset=list(MAP.items())[batch*7:(batch+1)*7]
 sheet=Image.new('RGB',(1200,240*len(subset)),(231,234,240));draw=ImageDraw.Draw(sheet)
 for row,(key,folder) in enumerate(subset):
  path=V/'evidence'/folder
  sources=sorted(path.glob('source-cell-[0-9]*.png')) or sorted(path.glob('source-[0-9]*.png'))
  sources=[p for p in sources if p.stem[-1].isdigit()]
  draw.text((5,row*240+5),key,fill=(20,25,40),font=font)
  for i,p in enumerate(sources):
   im=Image.open(p).convert('RGBA');im.thumbnail((180,200),Image.Resampling.LANCZOS)
   sheet.paste(im,(i*195+5,row*240+35),im)
  records.append({'group':key,'frames':len(sources),'sourceFiles':[p.relative_to(R).as_posix() for p in sources],
    'status':'待逐姿视觉复核；缩略图只作初筛'})
 sheet.save(O/f'evidence/legacy-{batch}.jpg')
(O/'legacy-review-sources.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
print('14组历史候选复核板保存，未登记视觉通过')
