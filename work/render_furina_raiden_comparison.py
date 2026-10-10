"""Fixed world-scale same-action comparison; never certify art acceptance."""
from pathlib import Path
import json,math,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
B=R/'outputs/v4-one-character-20261010/baseline-actions'
data=json.loads((O/'actions-size-candidate.json').read_text(encoding='utf-8'))
poses={p['pose']:p for p in json.loads((B/'parameters.json').read_text(encoding='utf-8'))['characters']['raidenshogun']['poses'] if p['origin']=='keyframes'}
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
specs={'败北':('defeat',['hurt_7']), '受击与倒地':('hurt',['hurt_0','hurt_1','hurt_2','hurt_3']),
 '空轻':('airlight',['air_4','air_5','air_4']), '空重':('airheavy',['air_6','air_7','air_6']),
 '站立格挡':('guard',['guard_2','guard_3','guard_6','guard_3']), '蹲防':('crouchguard',['guard_4','guard_5','guard_7','guard_5']),
 '被投':('victim',[f'victim_{i}' for i in range(6)]), '胜利':('victory',['hurt_6']),
 '轻攻三':('light3',['heavy_0','heavy_1','heavy_2','heavy_3'])}
def furina(canvas,f,x,y):
 im=Image.open(O/f['file']).convert('RGBA');s=f['scale']
 im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
 canvas.alpha_composite(im,(round(x-f['anchor'][0]*s),round(y-f['anchor'][1]*s)))
def raiden(canvas,key,x,y):
 p=poses[key];im=Image.open(B/p['file']).convert('RGBA');s=p['u']*330/336
 im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
 canvas.alpha_composite(im,(round(x-p['ax']*s),round(y-p['ay']*s)))
links=[]
for label,(key,refseq) in specs.items():
 fs=data[label]['frames']
 for page in range(math.ceil(len(fs)/2)):
  sheet=Image.new('RGBA',(1800,1120),'white');draw=ImageDraw.Draw(sheet)
  for row,f in enumerate(fs[page*2:page*2+2]):
   i=page*2+row;oy=row*560;ground=oy+525;air=label in ['空轻','空重'];y=ground-(100 if air else 0)
   ref=refseq[min(len(refseq)-1,round(i*(len(refseq)-1)/max(1,len(fs)-1)))]
   for col,text in enumerate(['芙芙待机基准',f'{label} · {i+1} · {data[label]["phases"][i]}',f'雷神对应动作 · {ref}','雷神待机基准']):
    draw.text((col*450+12,oy+10),text,font=FONT,fill='#302b45');draw.line((col*450,ground,(col+1)*450,ground),fill='#9999aa')
   furina(sheet,data['待机']['frames'][0],130,ground)
   furina(sheet,f,580,y);raiden(sheet,ref,1125,y);raiden(sheet,'basic_0',1530,ground)
  name=f'raiden-compare-{key}-{page}.png';sheet.convert('RGB').save(O/name)
  links.append(f'<h2>{label} · 第{page+1}页</h2><img src="{name}" style="width:100%;max-width:1800px">')
html='<!doctype html><meta charset="utf-8"><title>芙芙与拟合雷神同动作对照</title><h1>同舞台倍率：待机／芙芙动作／雷神对应动作／雷神待机</h1><p>四列全按世界倍率1，不适应外框、不逐图缩放。双方动作阶段并非相同招式，不据此强制剪影等高；人物比例和肢体仍需人工验收。空中两列同样离地100。</p>'+''.join(links)
(O/'raiden-comparison.html').write_text(html,encoding='utf-8')
served=R/'work/github-review-20261009/V3/assets/action-reference/furina'
for p in O.glob('raiden-comp*'):
 if served.is_dir():shutil.copy2(p,served/p.name)
print('same-action comparison pages:',len(links))
