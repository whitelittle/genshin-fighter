"""Draw Nahida by semantic parts using only native UI primitives."""
import io
import json
import sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path('work/vector-research-deps').resolve()))
import resvg_py
from PIL import Image,ImageDraw,ImageFont

OUT=Path('outputs/nahida-native-collage-20261014');OUT.mkdir(parents=True,exist_ok=True)
elements=[]
INK='#716956'; HAIR='#f9f4ee'; SHADE='#ddd4cd'; SOFT='#ebe3dc'
GREEN='#697d43'; DARK='#34492c'; LIGHT='#b6c47b'; GOLD='#c6b16d'; BRIGHT='#eadcb0'
SKIN='#fce4d2'; SKINSHADE='#d69b82'; WHITE='#fff8e9'
def add(kind,name,x,y,w,h,color,rot=0,part='body',fill=1):
    elements.append(dict(type=kind,name=name,x=x,y=y,width=w,height=h,color=color,rotation=rot,part=part,fill=fill))
def ell(name,x,y,w,h,color,rot=0,part='body'):add('ellipse',name,x,y,w,h,color,rot,part)
def tri(name,x,y,w,h,color,rot=0,part='body'):add('triangle',name,x,y,w,h,color,rot,part)
def rect(name,x,y,w,h,color,rot=0,part='body'):add('rectangle',name,x,y,w,h,color,rot,part)
def edge(kind,name,x,y,w,h,color,rot=0,part='body',line=1.4):
    add(kind,name+'外缘',x,y,w+line*2,h+line*2,INK,rot,part)
    add(kind,name,x,y,w,h,color,rot,part)
def leaf(name,x,y,w,h,rot,color=GREEN,part='ornament'):
    ell(name+'金边',x,y,w+2,h+2,GOLD,rot,part)
    ell(name,x,y,w,h,color,rot,part)
    rect(name+'叶脉',x,y,1,h*.72,BRIGHT,rot,part)

# Back skirt ribbons, each a long transformed leaf rather than sampled color patches.
for n,x,y,w,h,r in [('披带上',64,224,20,137,-62),('披带中',57,254,28,149,-49),('披带下',64,278,29,113,-26),('右裙叶',219,268,24,75,24)]:
    edge('ellipse',n,x,y,w,h,LIGHT,r,'back-cloth')
    ell(n+'绿面',x-2,y-3,w*.63,h*.9,GREEN,r,'back-cloth')
    rect(n+'中线',x,y,1.1,h*.82,GOLD,r,'back-cloth')
for x,y,r in [(22,236,241),(12,273,222),(54,312,193),(243,299,156)]:
    tri('披带尖',x,y,17,33,LIGHT,r,'back-cloth')

# Legs: a few connected ellipses and tapered triangular transitions.
for name,x,y,w,h,r in [('后大腿',174,328,31,87,-9),('后小腿',168,404,22,83,4),('前大腿',144,335,32,98,-8),('前小腿',134,409,22,79,-3)]:
    edge('ellipse',name,x,y,w,h,SKIN,r,'legs',1)
edge('ellipse','后脚',183,450,43,13,SKIN,10,'legs',1)
edge('ellipse','前脚',146,454,47,13,SKIN,13,'legs',1)
ell('后膝连续',172,373,24,37,SKIN,2,'legs')
ell('前膝连续',138,376,25,36,SKIN,2,'legs')
ell('后踝连续',168,437,23,20,SKIN,0,'legs')
ell('前踝连续',132,443,23,19,SKIN,0,'legs')
rect('前腿内侧线',147,389,1,63,SKINSHADE,-8,'legs')
rect('后脚趾线',194,450,1,7,SKINSHADE,40,'legs')
rect('前脚趾线',160,454,1,7,SKINSHADE,40,'legs')
leaf('踝饰',127,432,5,18,13,part='legs')

# Rear arm remains behind the torso; front arm and hand added after clothing.
edge('ellipse','后上臂',205,196,15,62,SKIN,17,'rear-arm',1)
edge('ellipse','后前臂',225,243,13,50,SKIN,26,'rear-arm',1)
edge('ellipse','后手',237,265,13,25,SKIN,33,'rear-arm',1)
ell('后肘连续',213,222,18,24,SKIN,22,'rear-arm')

# Green underskirt and patterned white dress, one large piece per garment panel.
edge('ellipse','绿裙底',164,264,114,81,DARK,0,'dress')
for n,x,y,w,h,r in [('左裙叶',115,279,23,44,203),('左中裙叶',137,289,20,41,194),('右中裙叶',192,285,21,44,164),('右裙叶',213,276,20,49,154)]:
    edge('triangle',n,x,y,w,h,GREEN,r,'dress',.7)
    tri(n+'金纹',x,y+4,w*.35,h*.5,GOLD,r,'dress')
for x,y in [(118,286),(135,295),(198,291),(213,279)]:
    add('fourstar','裙饰菱星',x,y,8,11,BRIGHT,0,'dress')
for x,r in [(143,14),(162,0),(183,-13)]:
    edge('triangle','白色内裙瓣',x,291,27,23,WHITE,180+r,'dress',.7)
edge('ellipse','白裙主体',172,230,85,109,WHITE,-5,'dress')
edge('triangle','左衣片',145,228,55,116,WHITE,14,'dress',.7)
edge('triangle','右衣片',198,227,44,113,WHITE,-13,'dress',.7)
ell('衣片接缝覆盖',170,220,48,93,WHITE,0,'dress')
rect('衣片中缝',172,231,1,77,GOLD,0,'dress')
rect('左侧金缝',145,239,1.6,77,GOLD,-14,'dress')
rect('右侧金缝',198,241,1.4,65,GOLD,16,'dress')
for x,y,r in [(144,257,32),(133,265,-24),(200,257,-27),(208,267,20)]:
    ell('裙面浅金枝',x,y,5,16,BRIGHT,r,'dress')
    ell('裙面枝芯',x,y,2.8,11,WHITE,r,'dress')
for x,y in [(145,270),(196,272),(177,255)]:add('fourstar','裙面花纹',x,y,9,12,BRIGHT,0,'dress')
leaf('裙中央叶',170,280,15,26,0,DARK,'dress')

# Front shoulder, bent arm and separately placed fingers.
edge('ellipse','前肩',147,166,27,37,SKIN,-10,'front-arm',1)
edge('ellipse','前上臂',137,193,20,50,SKIN,-20,'front-arm',1)
edge('ellipse','前前臂',115,238,19,62,SKIN,-24,'front-arm',1)
ell('肘部接续',126,218,19,23,SKIN,0,'front-arm')
edge('ellipse','前手掌',101,268,22,27,SKIN,-25,'front-arm',.9)
for i in range(4):edge('ellipse','前手指'+str(i),91+i*4.6,279-i*.8,4,18-i*.8,SKIN,-23-i*3,'front-arm',.5)
edge('ellipse','前拇指',112,273,5,17,SKIN,27,'front-arm',.5)
edge('ellipse','腕环',113,252,24,11,GOLD,-23,'front-arm',.7)
ell('腕环内面',113,252,18,6,DARK,-23,'front-arm')
rect('腕环金线',113,252,1,7,BRIGHT,-23,'front-arm')
leaf('肩饰大叶',130,186,19,40,49,DARK,'front-arm')
leaf('肩饰侧叶',122,197,12,28,67,GREEN,'front-arm')
leaf('肩饰前叶',145,194,10,29,-26,GREEN,'front-arm')
tri('肩饰尖',126,210,12,22,GOLD,194,'front-arm')

# Neck and upper green-gold bib.
edge('ellipse','颈部',170,145,20,28,SKIN,12,'neck',.8)
edge('ellipse','绿领',172,153,30,17,DARK,-26,'neck',.7)
leaf('领尖叶',167,164,13,29,31,DARK,'neck')
edge('ellipse','胸饰底',179,178,33,43,DARK,20,'neck',.8)
ell('胸饰金环',180,177,26,35,GOLD,20,'neck')
ell('胸饰绿芯',180,177,23,31,DARK,20,'neck')
leaf('胸饰斜叶',178,171,10,31,27,GREEN,'neck')
leaf('胸饰小叶',190,190,8,23,-21,GREEN,'neck')
for x,y,r in [(178,208,8),(193,222,-13)]:
    rect('垂饰金线',x,y,1,37,GOLD,r,'dress')
    ell('垂饰珠',x,y+18,4,7,BRIGHT,r,'dress')

# Ponytail: large white bundles taper into green tips; curls by overlapping lobes.
edge('ellipse','后发主体',81,74,46,119,HAIR,-39,'back-hair',1.2)
edge('ellipse','长马尾',49,114,38,94,LIGHT,-31,'back-hair',1.2)
ell('马尾白面',55,99,29,78,HAIR,-34,'back-hair')
ell('马尾发亮',73,69,15,87,WHITE,-36,'back-hair')
ell('马尾阴影',80,80,9,97,SHADE,-34,'back-hair')
edge('ellipse','内侧发束',78,97,20,110,HAIR,-16,'back-hair',.8)
ell('内侧绿渐变块',70,140,17,31,LIGHT,-10,'back-hair')
edge('ellipse','尾尖大弯',40,160,29,24,GREEN,34,'back-hair',.9)
ell('弯发内白',46,153,23,18,LIGHT,34,'back-hair')
edge('ellipse','尾尖小弯',25,162,11,26,GREEN,-24,'back-hair',.8)
ell('小弯亮面',28,159,6,21,LIGHT,-24,'back-hair')
tri('尾尖',42,174,14,19,LIGHT,204,'back-hair')
tri('长发尖',28,144,21,37,LIGHT,188,'back-hair')

# Large rear head cap, side locks, face and pointed ear.
edge('ellipse','后脑白发',173,79,91,111,HAIR,8,'head',1.1)
ell('后脑发阴影',209,94,17,82,SHADE,4,'head')
edge('ellipse','右侧发束',215,133,18,39,HAIR,23,'head',.8)
ell('右发绿尖',216,145,13,16,LIGHT,28,'head')
edge('triangle','尖耳',145,112,22,25,SKIN,259,'face',.8)
tri('耳内面',145,113,11,17,SKINSHADE,259,'face')
edge('ellipse','脸颊',186,107,67,57,SKIN,-11,'face',1)
tri('下巴连续',190,124,36,25,SKIN,180,'face')
ell('脸颊肤色覆盖',190,116,47,34,SKIN,-12,'face')
edge('ellipse','鼻尖',216,110,9,11,SKIN,0,'face',.5)
ell('鼻根覆盖',211,108,12,17,SKIN,0,'face')
rect('小嘴',207,124,4,.8,SKINSHADE,-12,'face')
ell('脸侧淡红',199,118,11,3,'#efc3b2',-6,'face')

# Eyes are deliberate nested primitives, not automatic micro-region tracing.
edge('ellipse','主眼',181,100,18,23,WHITE,6,'eyes',.5)
ell('主眼瞳外',183,101,11,18,GREEN,4,'eyes')
ell('主眼瞳亮',183,103,8,12,'#c1d56d',4,'eyes')
ell('主眼瞳心',184,100,4,10,DARK,4,'eyes')
ell('主眼高光',181,96,3.5,5,'#fffef3',0,'eyes')
ell('上眼线',181,90,20,3,DARK,7,'eyes')
tri('外睫毛',172,92,5,8,DARK,235,'eyes')
ell('远眼白',208,102,7,16,WHITE,-8,'eyes')
ell('远眼绿瞳',210,103,4,12,GREEN,-8,'eyes')
ell('远眼瞳心',210,101,2,8,DARK,-8,'eyes')
ell('远眼高光',209,98,1.5,3,WHITE,0,'eyes')
rect('远眼上睫',208,94,7,1.8,DARK,-14,'eyes')
rect('主眉',180,84,13,1.2,SKINSHADE,-9,'eyes')

# Swept bangs and cheeks conceal the top of the face, as in the HD pose.
edge('ellipse','顶发',177,53,86,58,HAIR,4,'front-hair',1)
ell('顶发高光',176,45,65,32,WHITE,0,'front-hair')
for n,x,y,ww,hh,r in [('左刘海',155,74,27,69,-20),('中刘海',177,65,25,58,-31),('右刘海',199,61,22,57,-14)]:
    edge('ellipse',n,x,y,ww,hh,HAIR,r,'front-hair',.7)
    ell(n+'浅影',x+5,y+3,4,hh*.76,SOFT,r,'front-hair')
for x,y,ww,hh,r in [(152,104,19,33,194),(173,90,17,27,222),(197,85,15,24,195)]:
    tri('刘海尖',x,y,ww,hh,HAIR,r,'front-hair')
edge('ellipse','脸侧长发',157,124,21,40,HAIR,24,'front-hair',.8)
tri('侧发尖',163,142,16,22,HAIR,153,'front-hair')
ell('侧发内影',154,126,5,28,SHADE,24,'front-hair')

# Leaf crown and characteristic gold clover ornament.
for x,y,ww,hh,r in [(146,20,11,25,7),(160,13,9,26,-7),(171,26,8,18,-17)]:
    edge('triangle','头冠叶',x,y,ww,hh,GREEN,r,'head-ornament',.6)
    tri('头冠叶金芯',x,y,ww*.45,hh*.72,GOLD,r,'head-ornament')
for x,y,ww,hh,r in [(125,56,14,35,-18),(119,73,13,31,32),(140,72,12,29,-59),(128,88,12,30,-3),(112,91,10,23,31)]:
    leaf('四叶发饰',x,y,ww,hh,r,DARK,'head-ornament')
ell('发饰中心金珠',128,75,8,8,GOLD,0,'head-ornament')
ell('发饰中心绿芯',128,75,4,4,DARK,0,'head-ornament')
leaf('头顶系叶',132,39,12,27,-32,GREEN,'head-ornament')

# Palette and part counts make the native element count reviewable.
scene={'w':251,'h':462,'elements':elements,'method':'manual semantic primitive collage','reference':'HD first pose','inputRasterized':False}
(OUT/'collage.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2),encoding='utf-8')
shapes=[]
for i,e in enumerate(elements):
    ww,hh=e['width'],e['height'];kind=e['type']
    if kind=='ellipse':shape=f'<ellipse rx="{ww/2}" ry="{hh/2}"/>'
    elif kind=='rectangle':shape=f'<rect x="{-ww/2}" y="{-hh/2}" width="{ww}" height="{hh}"/>'
    elif kind=='triangle':shape=f'<polygon points="0,{-hh/2} {ww/2},{hh/2} {-ww/2},{hh/2}"/>'
    else:shape=f'<polygon points="0,{-hh/2} {ww*.12},{-hh*.12} {ww/2},0 {ww*.12},{hh*.12} 0,{hh/2} {-ww*.12},{hh*.12} {-ww/2},0 {-ww*.12},{-hh*.12}"/>'
    shapes.append(f'<g id="part-{i}" transform="translate({e["x"]} {e["y"]}) rotate({-e["rotation"]})" fill="{e["color"]}">{shape}</g>')
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 251 462" width="251" height="462"><title>草神基础图元拼装小样</title>'+''.join(shapes)+'</svg>'
(OUT/'collage.svg').write_text(svg,encoding='utf-8')
png=resvg_py.svg_to_bytes(svg_string=svg,zoom=3,skip_system_fonts=True)
(OUT/'collage.png').write_bytes(png)
pic=Image.open(io.BytesIO(png)).convert('RGBA')
source=Image.open('outputs/nahida-hd-vector-fit-20261014/source-hd-first.png').convert('RGBA')
panel=Image.new('RGB',(880,850),'#eff2f6');draw=ImageDraw.Draw(panel)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',24);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
draw.text((25,18),'草神 · 按部件拼装基础图元',font=font,fill='#354139')
for i,(image,title) in enumerate([(source,'高清第一帧参考'),(pic,'基础图元拼装小样')]):
    left=18+i*432;draw.rounded_rectangle((left,65,left+412,780),16,fill='white')
    draw.text((left+18,85),title,font=font,fill='#354139')
    shown=image.resize((round(251/462*615),615),Image.Resampling.LANCZOS)
    panel.paste(shown,(left+(412-shown.width)//2,130),shown)
draw.text((25,803),f'{len(elements)} 个图片图元；椭圆、三角形、矩形、四角星；造型小样，真机未验。',font=small,fill='#657169')
panel.save(OUT/'comparison.png')
report={'imagePrimitives':len(elements),'types':dict(Counter(e['type'] for e in elements)),
        'parts':dict(Counter(e['part'] for e in elements)),'arbitraryBezierPaths':0,
        'pixelFitting':False,'automaticColorRegionTracing':False,'deviceVerified':False}
(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
