import json
from pathlib import Path
from PIL import Image, ImageDraw
root=Path('outputs/paimon-vector-20261014')
scene=json.loads((root/'paimon-scene.json').read_text(encoding='utf-8'))
S=3
canvas=Image.new('RGBA',(600*S,700*S))
for e in scene['elements']:
    w,h=e['width']*S,e['height']*S
    side=int(max(w,h)*2+16*S)
    layer=Image.new('RGBA',(side,side))
    d=ImageDraw.Draw(layer)
    cx=cy=side/2
    c=tuple(bytes.fromhex(e['color'][1:]))+(round(255*e['opacity']),)
    box=(cx-w/2,cy-h/2,cx+w/2,cy+h/2)
    kind=e['type']
    if kind=='ellipse':d.ellipse(box,fill=c)
    elif kind=='rectangle':d.rectangle(box,fill=c)
    elif kind=='triangle':d.polygon([(cx,cy-h/2),(cx+w/2,cy+h/2),(cx-w/2,cy+h/2)],fill=c)
    elif kind=='ring':
        d.ellipse(box,fill=c)
        d.ellipse((cx-w*.4,cy-h*.4,cx+w*.4,cy+h*.4),fill=(0,0,0,0))
    else:d.polygon([(cx,cy-h/2),(cx+w*.12,cy-h*.12),(cx+w/2,cy),(cx+w*.12,cy+h*.12),(cx,cy+h/2),(cx-w*.12,cy+h*.12),(cx-w/2,cy),(cx-w*.12,cy-h*.12)],fill=c)
    layer=layer.rotate(e['rotation'],Image.Resampling.BICUBIC)
    canvas.alpha_composite(layer,(round(e['x']*S-side/2),round(e['y']*S-side/2)))
canvas=canvas.resize((600,700),Image.Resampling.LANCZOS)
canvas.save(root/'paimon.png')
background=Image.new('RGBA',canvas.size,'#E5EBF2')
background.alpha_composite(canvas)
background.convert('RGB').save(root/'paimon-preview.jpg',quality=95)
