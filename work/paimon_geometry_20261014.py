"""Paimon study: editable primitives, no pixel fitting and no arbitrary paths."""
import json, math
from pathlib import Path
OUT=Path('outputs/paimon-vector-20261014'); OUT.mkdir(parents=True,exist_ok=True)
elements=[]
INK='#626A85'; WHITE='#FFFDF5'; HAIR='#E8EAF4'; SKIN='#FFE5D5'; CORAL='#EEB0A0'; GOLD='#DCAA89'; NAVY='#313653'; BLUE='#5675AF'
def add(kind,name,x,y,w,h,col,rot=0,alpha=1,part='body'):
    elements.append(dict(id=f'p{len(elements)+1:03}',name=part+' / '+name,type=kind,x=x,y=y,width=w,height=h,color=col,opacity=alpha,rotation=rot,zIndex=len(elements),rotationX=0,rotationY=0))
def ellipse(name,x,y,w,h,col,rot=0,alpha=1,part='body'):add('ellipse',name,x,y,w,h,col,rot,alpha,part)
def tri(name,x,y,w,h,col,rot=180,part='body'):add('triangle',name,x,y,w,h,col,rot,part=part)
def star(name,x,y,s,col,rot=0,part='body'):add('four_point_star',name,x,y,s,s,col,rot,part=part)
def outline(kind,name,x,y,w,h,col,rot=0,edge=3,part='body'):
    add(kind,name+'轮廓',x,y,w+edge*2,h+edge*2,INK,rot,part=part)
    add(kind,name,x,y,w,h,col,rot,part=part)

# Floating cape: layering of triangles, elliptic shoulder lobes, white corner stars.
tri('披风外缘',300,431,258,219,HAIR,part='cape')
tri('星空披风',300,433,236,208,NAVY,part='cape')
ellipse('左披肩',233,369,122,61,NAVY,22,part='cape')
ellipse('右披肩',367,369,122,61,NAVY,-22,part='cape')
for x,y,s in [(203,406,9),(217,433,5),(393,405,7),(383,447,9),(252,492,6),(350,493,5)]:star('披风星点',x,y,s,'#ECEAFB',part='cape')
for x,y in [(224,397),(374,393),(239,457),(360,468)]:ellipse('披风小星',x,y,3,3,'#AEBCE4',part='cape')

# Legs and boots, each independent transformable component.
for x,rot,side in [(272,9,'左'),(328,-9,'右')]:
    outline('ellipse',side+'腿',x,530,35,98,SKIN,rot,part='leg-'+side)
    outline('ellipse',side+'袜靴',x+(2 if rot>0 else -2),571,44,89,WHITE,rot,part='leg-'+side)
    ellipse(side+'靴饰',x,570,36,58,CORAL,rot,part='leg-'+side)
    ellipse(side+'靴白面',x,579,30,49,WHITE,rot,part='leg-'+side)
    star(side+'靴星',x,562,13,GOLD,part='leg-'+side)

# Spread arms + tapered sleeves, filled occlusion is inside the same silhouette.
for x,rot,side in [(217,-51,'左'),(383,51,'右')]:
    outline('ellipse',side+'袖',x,408,43,88,WHITE,rot,part='arm-'+side)
    ellipse(side+'袖纹',x,416,32,53,CORAL,rot,part='arm-'+side)
    ellipse(side+'袖中白',x,412,23,45,WHITE,rot,part='arm-'+side)
    hx=176 if side=='左' else 424
    outline('ellipse',side+'手掌',hx,439,32,25,SKIN,-rot/2,part='arm-'+side)
    ellipse(side+'拇指',hx+(10 if side=='左' else -10),432,14,12,SKIN,part='arm-'+side)

outline('ellipse','服装主体',300,432,111,153,WHITE)
tri('裙摆外缘',300,479,135,68,INK)
tri('裙摆白色',300,477,127,62,WHITE)
ellipse('腰侧阴影',300,444,103,18,HAIR)
ellipse('腰带',300,445,105,9,CORAL)
tri('胸前金纹外',300,405,75,92,GOLD)
tri('胸前白芯',300,400,57, seventy:=70,WHITE)
star('胸前标记',300,409,25,CORAL)
for x,rot in [(263,-17),(337,17)]:add('rectangle','胸饰条',x,421,4,43,GOLD,rot)
ellipse('领口披肩',300,367,112,40,CORAL)
ellipse('领口白层',300,360,103,29,WHITE)
ellipse('颈部',300,350,41,38,SKIN,part='head')

# Hair silhouette and face. Large head, navy star clasp, layered tapered locks.
outline('ellipse','白发后脑',300,249,228,213,HAIR,part='head')
for x,y,w,h,r in [(206,285,51,117,-22),(394,285,51,117,22),(235,326,59,65,-21),(365,326,59,65,21)]:
    outline('ellipse','后发束',x,y,w,h,HAIR,r,part='head')
outline('ellipse','脸',300,275,170,157,SKIN,part='head')
ellipse('右耳',386,280,20,32,SKIN,part='head')
ellipse('左耳',214,280,20,32,SKIN,part='head')
ellipse('刘海顶',300,205,216,114,WHITE,part='head')
# Triangular bangs overlap the top cap, providing pointed white locks without Bezier.
for x,y,w,h,r in [(211,243,47,92,198),(247,236,53,77,191),(287,233,54,73,170),(330,232,52,72,169),(370,242,45,96,159)]:
    outline('triangle','刘海发束',x,y,w,h,WHITE,r,edge=1.3,part='head')
# Restoring top cap hides internal seams; all overlap remains within hair silhouette.
ellipse('顶发覆盖',296,204,195,92,WHITE,part='head')
ellipse('顶发光',285,184,125,48,'#FFFFFF',-10,part='head')
tri('左侧发尖',208,305,47,104,WHITE,167,part='head')
tri('右侧发尖',392,305,47,104,WHITE,193,part='head')
star('发夹外形',379,227,42,NAVY,19,part='head')
star('发夹光',379,227,22,'#69718F',19,part='head')

# Eyes and expression use only ellipses, triangles and one simple rectangle per brow.
for x,rot in [(266,-8),(335,8)]:
    ellipse('眼睫',x,282,37,47,NAVY,rot,part='head')
    ellipse('眼白',x,283,30,39,'#FFFFFF',rot,part='head')
    ellipse('蓝眼瞳',x,285,24,34,BLUE,rot,part='head')
    ellipse('深色瞳',x,282,17,27,NAVY,rot,part='head')
    ellipse('瞳孔下光',x+1,294,15,10,'#91B0D7',rot,part='head')
    ellipse('眼高光',x-5,276,8,10,'#FFFFFF',rot,part='head')
    ellipse('小高光',x+5,287,4,4,'#FFFFFF',part='head')
    add('rectangle','眉毛',x,253,25,3,INK,rot,part='head')
ellipse('左腮红',243,312,24,10,'#EFADAA',alpha=.55,part='head')
ellipse('右腮红',358,312,24,10,'#EFADAA',alpha=.55,part='head')
ellipse('小嘴',301,324,22,14,'#A56F76',part='head')
ellipse('微笑上遮挡',301,318,27,12,SKIN,part='head')
ellipse('鼻尖',302,308,6,3,'#E7B9AC',part='head')

# Paimon's peach halo: ring retains fixed inner/outer ratio, stretched as a whole.
add('ring','悬浮冠环',299,116,172,46,GOLD,7,part='halo')
star('冠左角',228,113,25,GOLD,12,part='halo')
star('冠右角',370,104,22,GOLD,12,part='halo')
add('rectangle','冠尖连接',316,94,7,34,GOLD,12,part='halo')
star('冠顶尖',311,80,28,GOLD,12,part='halo')

scene={'canvas':{'width':600,'height':700,'background':'transparent','mask':{'enabled':True,'shapeType':1,'x':0,'y':0,'width':600,'height':700,'previewOnCanvas':False}},'elements':elements,'meta':{'sourceType':'editor','sourceName':'派蒙_图元变换试作','warnings':['仅几何拼装候选；非真机验收；画布遮罩非逐部件蒙版']}}
(OUT/'paimon-scene.json').write_text(json.dumps(scene,ensure_ascii=False,indent=2),encoding='utf-8')
parts={}
for e in elements:parts.setdefault(e['name'].split(' / ')[0],[]).append(e['id'])
(OUT/'part-groups.json').write_text(json.dumps(parts,ensure_ascii=False,indent=2),encoding='utf-8')
def shape(e):
    w,h=e['width'],e['height'];typ=e['type'];col=e['color']
    if typ=='ellipse':s=f'<ellipse rx="{w/2}" ry="{h/2}"/>'
    elif typ=='rectangle':s=f'<rect x="{-w/2}" y="{-h/2}" width="{w}" height="{h}"/>'
    elif typ=='triangle':s=f'<polygon points="0,{-h/2} {w/2},{h/2} {-w/2},{h/2}"/>'
    elif typ=='four_point_star':s=f'<polygon points="0,{-h/2} {w*.12},{-h*.12} {w/2},0 {w*.12},{h*.12} 0,{h/2} {-w*.12},{h*.12} {-w/2},0 {-w*.12},{-h*.12}"/>'
    else:
        # Preview of native ring ratio; not an invented editable arbitrary path.
        s=f'<path fill-rule="evenodd" d="M {-w/2},0 a {w/2},{h/2} 0 1 0 {w},0 a {w/2},{h/2} 0 1 0 {-w},0 M {-w*.4},0 a {w*.4},{h*.4} 0 1 1 {w*.8},0 a {w*.4},{h*.4} 0 1 1 {-w*.8},0"/>'
    return f'<g id="{e["id"]}" data-part="{e["name"].split(" / ")[0]}" transform="translate({e["x"]} {e["y"]}) rotate({-e["rotation"]})" fill="{col}" opacity="{e["opacity"]}">{s}</g>'
svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 700" width="600" height="700"><title>派蒙图元变换试作</title>'+''.join(map(shape,elements))+'</svg>'
(OUT/'paimon.svg').write_text(svg,encoding='utf-8')
print(json.dumps({'elements':len(elements),'parts':{p:len(ids) for p,ids in parts.items()}},ensure_ascii=False))
