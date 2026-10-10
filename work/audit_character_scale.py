"""Generate source contact sheets for explicit anatomical landmark review."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont
R=Path(__file__).resolve().parents[1]
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
for character,folder in [('ayaka',R/'outputs/v4-one-character-20261010/ayaka-armed-v2'),('furina',R/'outputs/furina-design-20261010')]:
 data=json.loads((folder/'actions.json').read_text(encoding='utf-8'))
 rows=[]
 for label,d in data.items():
  fs=d.get('sourceFrames') or d['frames']
  strip=Image.new('RGB',(len(fs)*230,300),'#777780');draw=ImageDraw.Draw(strip)
  for i,f in enumerate(fs):
   im=Image.open(folder/f['file']).convert('RGBA');b=im.getchannel('A').getbbox();im=im.crop(b)
   ratio=min(210/im.width,240/im.height);im=im.resize((round(im.width*ratio),round(im.height*ratio)))
   strip.paste(im,(i*230+10,35),im);draw.text((i*230+5,4),f'{label} {i}',font=FONT,fill='white')
  rows.append(strip)
 for page in range((len(rows)+5)//6):
  subset=rows[page*6:page*6+6];sheet=Image.new('RGB',(max(x.width for x in subset),len(subset)*300),'#777780')
  for i,strip in enumerate(subset):sheet.paste(strip,(0,i*300))
  sheet.save(folder/f'scale-audit-source-{page}.jpg')
