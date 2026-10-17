"""Flatten the selected HD SVG into native half-filled triangles, never pixels."""
import json
import math
import re
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
sys.path.insert(0,str(Path('work/vector-research-deps').resolve()))
import mapbox_earcut

OUT=Path('outputs/nahida-18color-native-gia-20261014')
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=Path('outputs/nahida-hd-vector-fit-20261014/hd-fit-18color.svg')
TOLERANCE=.35

def area(p):
    return sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(p,p[1:]+p[:1]))*.5

def flatten(a,c,b,out):
    mid=(a+2*c+b)*.25
    chord=(a+b)*.5
    if np.linalg.norm(mid-chord)<=TOLERANCE:
        out.append(b.tolist())
        return
    ac=(a+c)*.5;cb=(c+b)*.5
    flatten(a,ac,mid,out);flatten(mid,cb,b,out)

def contours(d):
    tokens=re.findall(r'[MQZ]|-?\d+(?:\.\d+)?',d)
    i=0;result=[];poly=[];current=None
    while i<len(tokens):
        command=tokens[i];i+=1
        if command=='M':
            current=np.array([float(tokens[i]),float(tokens[i+1])]);i+=2
            poly=[current.tolist()]
        elif command=='Q':
            c=np.array([float(tokens[i]),float(tokens[i+1])]);b=np.array([float(tokens[i+2]),float(tokens[i+3])]);i+=4
            flatten(current,c,b,poly);current=b
        elif command=='Z':
            if np.linalg.norm(np.array(poly[0])-poly[-1])<1e-5:poly.pop()
            if len(poly)>=3:result.append(poly)
        else:raise ValueError(command)
    return result

def inside(point,poly):
    x,y=point;hit=False
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:hit=not hit
    return hit

def right_triangle(foot,a,b,color):
    va=np.array(a)-foot;vb=np.array(b)-foot
    if abs(float(np.cross(va,vb)))<1e-5:return
    # HD coordinates are Y-down; exported controls are Y-up.
    foot=np.array([foot[0],-foot[1]])
    va=np.array([va[0],-va[1]]);vb=np.array([vb[0],-vb[1]])
    if float(np.cross(vb,va))>=0:va,vb=vb,va
    height=float(np.linalg.norm(va));halfwidth=float(np.linalg.norm(vb))
    center=foot+va*.5
    angle=math.degrees(math.atan2(va[1],va[0]))-90
    images.append([float(center[0]),float(center[1]),2*halfwidth,height,angle,color])

images=[];triangle_count=0;source_contours=0;vertices=0
for path in ET.parse(SOURCE).getroot():
    if not path.tag.endswith('path'):continue
    polygons=contours(path.get('d'));source_contours+=len(polygons)
    outers=[p for p in polygons if area(p)>0]
    holes=[p for p in polygons if area(p)<0]
    ownership=[[] for _ in outers]
    for hole in holes:
        candidates=[(abs(area(p)),i) for i,p in enumerate(outers) if inside(hole[0],p)]
        if not candidates:raise ValueError('Uncontained hole')
        ownership[min(candidates)[1]].append(hole)
    color=path.get('fill')
    for i,outer in enumerate(outers):
        rings=[outer]+ownership[i]
        verts=np.array([p for ring in rings for p in ring],dtype=np.float64)
        ends=np.cumsum([len(r) for r in rings],dtype=np.uint32)
        indices=mapbox_earcut.triangulate_float64(verts,ends)
        vertices+=len(verts)
        for j in range(0,len(indices),3):
            pts=verts[indices[j:j+3]]
            if abs(float(np.cross(pts[1]-pts[0],pts[2]-pts[0])))<1e-6:continue
            # The altitude to the longest edge always lies on that edge.
            lengths=[np.linalg.norm(pts[(k+1)%3]-pts[(k+2)%3]) for k in range(3)]
            k=int(np.argmax(lengths));apex=pts[k];a=pts[(k+1)%3];b=pts[(k+2)%3]
            v=b-a;t=float(np.dot(apex-a,v)/np.dot(v,v));foot=a+v*t
            right_triangle(foot,apex,a,color);right_triangle(foot,apex,b,color)
            triangle_count+=1

(OUT/'native-geometry.json').write_text(json.dumps({'w':251,'h':462,'images':images},separators=(',',':')),encoding='utf-8')
report={'selectedSVG':'hd-fit-18color.svg','sourceClosedSubpaths':source_contours,
        'flattenToleranceHDpixels':TOLERANCE,'flattenedVertices':vertices,
        'meshTriangles':triangle_count,'nativeTriangleImages':len(images),
        'method':'SVG curves → adaptive geometric flattening → polygon-with-holes triangulation → altitude split → 100003 horizontal-left 50% fill',
        'inputRasterized':False,'svgSameColorStrokeNotConverted':True,
        'deviceVerified':False}
(OUT/'geometry-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False))
