"""Same-world before/after proof, never scale each cell to fit its envelope."""
from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1];O=R/'outputs/furina-design-20261010'
report=json.loads((O/'light3-consistency-report.json').read_text(encoding='utf-8'))
bank=json.loads((O/'actions-size-candidate.json').read_text(encoding='utf-8'))
foe=json.loads((O/'foe-fitted.json').read_text(encoding='utf-8'))['basic_0']
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
def pose(canvas,f,x,y,raiden=False):
 im=Image.open(O/f['file']).convert('RGBA');s=f['scale'];ax,ay=(f['ax'],f['ay']) if raiden else f['anchor']
 im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
 canvas.alpha_composite(im,(round(x-ax*s),round(y-ay*s)))
links=[]
for bg,key,color in [('white','white','#29243d'),('#171625','dark','#fff0c9')]:
 for page in range(3):
  canvas=Image.new('RGBA',(1900,1000),bg);draw=ImageDraw.Draw(canvas)
  for row in range(2):
   i=page*2+row;floor=row*500+460
   for col,label in enumerate(['待机母版',f'修改前 · {i+1} {bank["轻攻三"]["phases"][i]}',f'试修后 · {i+1}','雷神待机']):
    draw.text((col*475+12,row*500+10),label,font=font,fill=color);draw.line((col*475,floor,(col+1)*475,floor),fill='#888899')
   pose(canvas,bank['待机']['frames'][0],140,floor)
   pose(canvas,report['before']['frames'][i],610,floor)
   pose(canvas,report['after']['frames'][i],1085,floor)
   pose(canvas,foe,1610,floor,True)
  name=f'light3-consistency-{key}-{page}.png';canvas.convert('RGB').save(O/name)
  links.append(f'<h2>{key} · 第{page+1}页</h2><img src="{name}" style="width:100%;max-width:1900px">')
rows=[]
for i in range(6):
 r=report['measurements'][i];after=report['after']['sourceFrames'][i].get('proportionTrial',{}).get('segmentDeviation')
 fmt=lambda vs:' / '.join(f'{v:+.1%}' for v in vs)
 rows.append(f'<tr><td>{i+1} {bank["轻攻三"]["phases"][i]}</td><td>{fmt(r["beforeDeviation"])}</td><td>{fmt(after) if after else "保留原状态"}</td><td>{"倍率试修" if i==4 else "源图返修候选" if i==5 else "不据投影自动调整"}</td></tr>')
table='<table border="1" cellpadding="8"><tr><th>显示帧</th><th>修改前：头/躯干/左腿/右腿估计偏差</th><th>试修后估计偏差</th><th>处理</th></tr>'+''.join(rows)+'</table><p>头6%、躯干8%、腿12%为本轮筛查带，不是既有美术标准或用户验收线。数据来自人工投影点，不能把转身、遮挡或屈膝当成确定的解剖错误。<a href="light3-consistency-report.json">完整测量与前后数据</a></p>'
html='<!doctype html><meta charset="utf-8"><title>轻攻三局部试修前后对照</title><h1>同舞台倍率：待机／修改前／试修后／雷神</h1><p>四列世界倍率1、同脚底线，不按单图外框缩放。仅第5/6显示状态改动，其余保留。手工投影测量不是美术验收；剑、帽和裙摆不参与人体倍率拟合。</p>'+table+''.join(links)
(O/'light3-consistency-review.html').write_text(html,encoding='utf-8')
served=R/'work/github-review-20261009/V3/assets/action-reference/furina'
for p in O.glob('light3-consistency*'):
 if served.is_dir():shutil.copy2(p,served/p.name)
print('trial scales',[(i,report['before']['sourceFrames'][i]['scale'],report['after']['sourceFrames'][i]['scale']) for i in [4,5]])
print('new recovery deviation',report['newRecovery']['afterDeviation'])
