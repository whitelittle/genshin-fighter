from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if 'function AI:throwChoice(' not in s:
 a=s.index('    if p.y<=0 and foe.y<=0 and foe.invul==0 and dist*C<=sim:throwRange(p)');b=s.index('\n    if attacking(o)',a)
 s=s[:a]+"    local throw=self:throwChoice(p,foe,dist)\n    if throw~=0 then return throw end\n"+s[b:]
 s=s.replace("        if r < 0.115 * lv.aggro + 0.01 and foe.state == 'block' then return self:edge(B.TH) end\n",'')
 method='''function AI:throwChoice(p,foe,dist)
    local sim=self.sim
    if sim.tick<(self.throwReadyAt or 0) or sim.tick<(self.throwThinkAt or 0) then return 0 end
    local allowed=foe.state=='idle' or foe.state=='walk' or foe.state=='back' or foe.state=='block' or foe.state=='cblock' or foe.state=='crouch' or foe.state=='land'
    if p.y>0 or foe.y>0 or foe.invul>0 or not allowed or dist*C>sim:throwRange(p) then return 0 end
    -- One shared policy for every fighter: evaluate at most once per 18 frames.
    self.throwThinkAt=sim.tick+18
    local chance=(foe.state=='block' or foe.state=='cblock') and 0.32 or 0.22
    if self:rand()>=chance then return 0 end
    local out=self:edge(B.TH)
    if out~=0 then self.throwReadyAt=sim.tick+480;self.throwAttempts=(self.throwAttempts or 0)+1 end
    return out
end

'''
 s=s.replace('function AI:tick()',method+'function AI:tick()',1)
# The sprite integration is appended below after the drawn asset has arrived.
j['assets']['scripts'][0]['source']=s;p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
print('Unified AI throw: every 18f decision, 480f/8s cooldown; guard cannot bypass; both fighters same conditions')
from PIL import Image
import numpy as np
asset=R/'dist/actions/nahida/assets/viewfinder-r27.png';im=Image.open(asset).convert('RGBA');assert im.getextrema()[3][0]==0,'alpha background required'
W,H=im.size;frames=[];native={}
def rects(idx):
 out=[];prev={}
 for y,row in enumerate(idx):
  now={};x=0
  while x<len(row):
   c=int(row[x]);e=x+1
   while e<len(row) and row[e]==c:e+=1
   if c>=0:
    key=(x,e-x,c)
    if key in prev:r=prev[key];r[3]+=1
    else:r=[x,y,e-x,1,c];out.append(r)
    now[key]=r
   x=e
  prev=now
 return out
def lua(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(a) for k,a in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(lua(a) for a in v)+'}'
 return str(v)
for i in range(8):
 x,y=(i%4)*W//4,(i//4)*H//2;w,h=W//4,H//2
 frames.append(dict(x=x,y=y,w=w,h=h,ax=w/2,ay=h/2));crop=im.crop((x,y,x+w,y+h));size=128
 while True:
  a=crop.resize((size,size),Image.Resampling.BOX);q=a.quantize(colors=32,method=Image.Quantize.FASTOCTREE);pal=q.getpalette('RGBA');idx=np.array(q).astype(int);idx[np.array(a)[:,:,3]<75]=-1;rr=rects(idx)
  if len(rr)<=850:break
  size-=4
 native[str(i)]=dict(bytes=[v for r in rr for v in r],n=len(rr),pal=[pal[k:k+4] for k in range(0,128,4)],w=size,h=size,ax=size/2,ay=size/2,u=1)
atlasPath=R/'dist/actions/nahida/atlas.json';atlas=json.loads(atlasPath.read_text());atlas['viewfinder']=dict(url='assets/viewfinder-r27.png',height=H/2,frames=frames);atlasPath.write_text(json.dumps(atlas,ensure_ascii=False,separators=(',',':')))
data='return '+lua(native)+'\n';(R/'project-inputs/gf_viewfinder_data.lua').write_text(data)
j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if "GF_RELEASE_ID='nahida-pixel-viewfinder-r27'" not in s:
 s=s.replace('    self.aimLayer=G.layer(layers.fx)',"    self.aimLayer=G.layer(layers.fx)\n    if fighter.key=='nahida' then self.captureBmp=G.bitmap(layers.fx);self.captureBmp.node:on(false) end",1)
 a=s.index('function V:drawCapture()');b=s.index('\nfunction V:draw(budget)',a)
 s=s[:a]+'''local captureData
function V:drawCapture()
    if not self.captureBmp then return end
    local bmp,f=self.captureBmp,self.f
    if f.state~='skill' or f.t<4 then bmp.node:on(false);return end
    local t=f.t;local steps={0,0.10,0.26,0.48,0.74,1};local k=t<8 and 0 or steps[math.min(6,t-7)]
    local face=f.castFace or f.face
    local x=(f.castX or f.x)/C+face*(110+540*k);local y=(f.castY or 190*C)/C
    local index=t<6 and 0 or t<8 and 1 or t<10 and 2 or 3
    local alpha=1;local age=f.captureHitT and t-f.captureHitT or math.max(0,t-14)
    if f.captureHitT then
        x=(f.captureHitX or f.foe.x)/C;y=(f.captureHitY or 190*C)/C
        index=age<1 and 4 or age<3 and 5 or age<5 and 6 or 7
        alpha=math.max(0,1-age/8)
    elseif t>=14 then index=7;alpha=math.max(0,1-age/4) end
    if alpha<=0 then bmp.node:on(false);return end
    captureData=captureData or require('gf_viewfinder_data')
    local img=captureData[tostring(index)];bmp:draw(img,tostring(index));local scale=380/img.w
    bmp.node:pos(x,y):scale(face*scale,scale):on(true)
    for i=1,bmp.used do local c=img.pal[img.bytes[(i-1)*5+5]+1];bmp.kids[i]:color(c[1],c[2],c[3],(c[4] or 255)*alpha) end
end
''' +s[b:]
 # The authored viewfinder includes the impact frames; do not layer the old generic E bitmap over it.
 a=s.index("        if f.key=='nahida' then\n            if not f.captureHitT");b=s.index('\n        else\n        idx,width',a)
 s=s[:a]+"        if f.key=='nahida' then\n            self.animFx.node:on(false);return"+s[b:]
 s=s.replace('    if self.aimLayer then self.aimLayer:free() end','    if self.aimLayer then self.aimLayer:free() end\n    if self.captureBmp then self.captureBmp:free() end',1)
 s=s.replace("__loaders['gf_fview'] = function()","__loaders['gf_viewfinder_data'] = function()\n"+data+"end\n__loaders['gf_fview'] = function()",1)
 s=s.replace("GF_RELEASE_ID='nahida-frame-strike-r26'","GF_RELEASE_ID='nahida-pixel-viewfinder-r27'")
 j['meta']['name']='雷电与纳西妲 · 像素取景框与统一投技 AI r27';j['assets']['scripts'][0]['source']=s
 p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
method='''function capture(p,x,ground){
 const steps=[0,.10,.26,.48,.74,1],k=time<8?0:steps[Math.max(0,Math.min(5,Math.floor(time-8)))],hit=p>=3,age=hit?localAt(3):0;
 const index=hit?(age<1?4:age<3?5:age<5?6:7):(time<6?0:time<8?1:time<10?2:3),cx=hit?810:x+140+260*k,cy=ground-175;
 const f=atlas.viewfinder.frames[index],alpha=time<4?0:hit?clamp(1-age/8):1;
 ctx.save();ctx.globalAlpha=alpha;ctx.imageSmoothingEnabled=false;ctx.drawImage(images.viewfinder,f.x,f.y,f.w,f.h,cx-190,cy-190,380,380);ctx.restore();}
'''
for file in [R/'animation-tools/preview-engine-r23.js',R/'dist/actions/nahida/app.js',R/'dist/actions/raiden/app.js']:
 text=file.read_text();a=text.index('function capture(');b=text.index('function hitPhase(',a);text=text[:a]+method+text[b:];text=text.replace('v=r26','v=r27').replace('所闻遍计 · 撞框','所闻遍计 · 像素取景框');file.write_text(text)
for file in [R/'dist/actions/nahida/index.html',R/'dist/actions/raiden/index.html']:
 file.write_text(file.read_text().replace('v=r26','v=r27'))
for file in [R/'editor-entry.js',R/'dist/editor/editor.js',R/'editor-bootstrap.js',R/'dist/editor/bootstrap.js',R/'dist/editor/play.js',R/'dist/index.html']:
 file.write_text(file.read_text().replace('nahida-frame-strike-r26','nahida-pixel-viewfinder-r27').replace('草神 E 快速撞框 r26','草神像素取景框 · 投技 AI 修正 r27'))
print('r27 authored square viewfinder sprite: 8 frames, native max',max(v['n'] for v in native.values()),'primitives; no procedural frame')
