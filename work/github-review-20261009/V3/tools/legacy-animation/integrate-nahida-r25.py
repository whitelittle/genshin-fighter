from pathlib import Path
from PIL import Image
import json,numpy as np,re
R=Path(__file__).resolve().parents[1]
p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
def lua(v):
 if isinstance(v,dict):return '{'+','.join('['+json.dumps(str(k))+']='+lua(a) for k,a in v.items())+'}'
 if isinstance(v,list):return '{'+','.join(lua(a) for a in v)+'}'
 return str(v)
def rectangles(idx):
 out=[];last={}
 for y,row in enumerate(idx):
  now={};x=0
  while x<len(row):
   c=int(row[x]);end=x+1
   while end<len(row) and row[end]==c:end+=1
   if c>=0:
    k=(x,end-x,c)
    if k in last:r=last[k];r[3]+=1
    else:r=[x,y,end-x,1,c];out.append(r)
    now[k]=r
   x=end
  last=now
 return out
# Fit the same three assistants used in the action preview into native bitmap controls.
atlas=json.loads((R/'dist/actions/nahida/atlas.json').read_text())['aranara'];src=Image.open(R/'dist/actions/nahida'/atlas['url']).convert('RGBA');helpers={}
for i,f in enumerate(atlas['frames']):
 im=src.crop((f['x'],f['y'],f['x']+f['w'],f['y']+f['h']));size=76
 while True:
  ratio=size/max(im.size);a=im.resize((max(1,round(im.width*ratio)),max(1,round(im.height*ratio))),Image.Resampling.BOX)
  q=a.quantize(colors=24,method=Image.Quantize.FASTOCTREE);pal=q.getpalette('RGBA');idx=np.array(q).astype(int);idx[np.array(a)[:,:,3]<70]=-1;rs=rectangles(idx)
  if len(rs)<=350:break
  size-=4
 helpers[str(i)]=dict(bytes=[v for r in rs for v in r],n=len(rs),pal=[pal[k:k+4] for k in range(0,96,4)],ax=a.width/2,ay=a.height/2,w=a.width,h=a.height,u=1)
helperSource='return '+lua(helpers)+'\n';(R/'project-inputs/gf_aranara_data.lua').write_text(helperSource)
if "GF_RELEASE_ID='nahida-integrated-r25'" not in s:
 draft=(R/'project-inputs/nahida-design-r23.lua').read_text()
 def module(text,name):
  a=text.index("__loaders['"+name+"'] = function()");b=text.index("__loaders['",a+12);return text[a:b]
 # Retain r24 graphics and application pool lifecycle. Move only redesigned character modules.
 for name in ['gf_kits','gf_sim','gf_fview','gf_scene_fight']:
  s=s.replace(module(s,name),module(draft,name),1)
 s=s.replace("        elseif ty == 'roundEnd' then\n            self:roundEndFx(e)","        elseif ty == 'roundEnd' then\n            G.requestImageRetirement()\n            self:roundEndFx(e)")
 s=s.replace("        elseif ty == 'matchEnd' then","        elseif ty == 'matchEnd' then\n            G.requestImageRetirement()")
 # Nahida summons assistants instead of physically grabbing/lifting her opponent.
 s=s.replace("    if st=='walk' or st=='back' then local i=", "    if f.key=='nahida' and (st=='walk' or st=='back') then return frameName('move',1+self.walkT//16%2) end\n    if st=='walk' or st=='back' then local i=")
 s=s.replace("    if st=='throw' then return frameName('throw',", "    if st=='throw' and f.key=='nahida' then return frameName('skill',t<12 and 4 or t<30 and 5 or t<58 and 6 or 7) end\n    if st=='throw' then return frameName('throw',")
 s=s.replace("    if st=='thrown' then return frameName('victim',", "    if st=='thrown' and f.foe.key=='nahida' then return frameName('basic',0) end\n    if st=='thrown' then return frameName('victim',")
 s=s.replace('    self.aimLayer=G.layer(layers.fx)', '    self.aimLayer=G.layer(layers.fx)\n    self.assistants={}\n    if fighter.key==\'nahida\' then for i=1,3 do self.assistants[i]=G.bitmap(layers.fx);self.assistants[i].node:on(false) end end')
 method='''local assistantData
function V:drawAssistants()
    if #self.assistants==0 then return end
    local f=self.f;local t=f.t
    local active=f.state=='throw' and t>=12 and t<68
    if active then assistantData=assistantData or require('gf_aranara_data') end
    for i,bmp in ipairs(self.assistants) do
        if not active or t<12+(i-1)*3 then bmp.node:on(false)
        else
            local delay=t-12-(i-1)*3;local k=U.clamp(delay/20,0,1);local ease=k*k*(3-2*k)
            local target=f.foe.x/C-f.face*16
            local x=f.x/C-f.face*130+(target-f.x/C+f.face*130)*ease
            local y=160+(i-2)*72+70*math.sin(k*math.pi)
            local frame=delay<8 and 0 or delay<19 and 1 or 2;local alpha=1
            if t>=38 then local out=U.clamp((t-38)/30,0,1);x=target+f.face*out*300;y=y+out*200;frame=3;alpha=1-out end
            local img=assistantData[tostring((i-1)*4+frame)]
            bmp:draw(img,tostring(frame));local scale=96/img.w
            bmp.node:pos(x,y):scale(f.face*scale,scale):on(true)
            for n=1,bmp.used do local c=img.pal[img.bytes[(n-1)*5+5]+1];bmp.kids[n]:color(c[1],c[2],c[3],(c[4] or 255)*alpha) end
        end
    end
end

'''
 s=s.replace('function V:drawCapture()',method+'function V:drawCapture()',1)
 s=s.replace('    self:drawCapture()\n','    self:drawCapture()\n    self:drawAssistants()\n',1)
 s=s.replace('    self.tilt, self.sx, self.sy, self.ox, self.oy = tilt, sx, sy, ox, oy', '''    if f.key=='nahida' and (st=='idle' or st=='walk' or st=='back' or st=='attack' or st=='skill' or st=='burst' or st=='throw' or st=='dash' or st=='win') then
        local hover=st=='burst' and 65 or st=='skill' and 38 or 25
        if st=='skill' and t>f.move.startup then hover=hover*(1-U.clamp((t-f.move.startup)/f.move.recovery,0,1)) end
        oy=oy+hover+5*math.sin(self.app.t*6+f.id)
        if st=='walk' or st=='back' then tilt=0 end
    end
    self.tilt, self.sx, self.sy, self.ox, self.oy = tilt, sx, sy, ox, oy''',1)
 s=s.replace('    local hgt = math.max(0, y)','    local hgt = math.max(0, y+oy)',1)
 s=s.replace('    if self.aimLayer then self.aimLayer:free() end','    if self.aimLayer then self.aimLayer:free() end\n    for _,bmp in ipairs(self.assistants) do bmp:free() end',1)
 s=s.replace("        if p.t == 30 then\n            local dmg = K.throw.damage", "        local assist=p.key=='nahida'\n        local impact=assist and 34 or 30\n        if p.t == impact then\n            local dmg = K.throw.damage",1)
 s=s.replace('            d.vy = -12 * C\n            d.y=math.max(d.y,40*C)\n            d.vx = p.face * 9 * C','            d.vy = (assist and 24 or -12) * C\n            d.y=math.max(d.y,(assist and 20 or 40)*C)\n            d.vx = p.face * (assist and 15 or 9) * C',1)
 s=s.replace('        elseif p.t < 30 then\n            d.x = p.x + p.face * 120 * C','        elseif p.t < impact then\n            if assist then\n                d.t=p.t;d.face=-p.face;d.y=0\n            else\n            d.x = p.x + p.face * 120 * C',1)
 s=s.replace("            d.y=math.max(0,lift)*160*C\n        end\n        if p.t >= 50 then self:setState(p, 'idle') end", "            d.y=math.max(0,lift)*160*C\n            end\n        end\n        if p.t >= (assist and 76 or 50) then self:setState(p, 'idle') end",1)
 s=s.replace("__loaders['gf_fview'] = function()", "__loaders['gf_aranara_data'] = function()\n"+helperSource+"end\n__loaders['gf_fview'] = function()",1)
 s=s.replace("GF_RELEASE_ID='preview-boundary-pool-r24'","GF_RELEASE_ID='nahida-integrated-r25'")
 j['meta']['name']='雷电与纳西妲 · 草神重做已接入 r25';j['assets']['scripts'][0]['source']=s
 p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
# Remove only the duplicate backdrop shrine. Keep the local shrine and dream lighting.
for file in [R/'animation-tools/preview-engine-r23.js',R/'dist/actions/nahida/app.js',R/'dist/actions/raiden/app.js']:
 text=file.read_text().replace('if(nahida){effect(9,580,580,850,.7,true);for','if(nahida){for').replace('v=r23','v=r25');file.write_text(text)
for file in [R/'dist/actions/nahida/index.html',R/'dist/actions/raiden/index.html']:
 file.write_text(file.read_text().replace('v=r23','v=r25'))
for file in [R/'editor-entry.js',R/'dist/editor/editor.js',R/'editor-bootstrap.js',R/'vendor/play-surface/play.js',R/'dist/editor/bootstrap.js',R/'dist/editor/play.js',R/'dist/index.html']:
 file.write_text(file.read_text().replace('preview-boundary-pool-r24','nahida-integrated-r25').replace('草神重做动作预览 r23','草神重做已接入对战 r25'))
print('r25 integrated capture E, dream Q, floating body, three native Aranara assistants; max helper primitives',max(x['n'] for x in helpers.values()))
# Recognize the new ranged skill in the existing AI strategy.
j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
s=s.replace("(sk.style == 'projectile' or sk.style == 'zone')", "(sk.style == 'projectile' or sk.style == 'zone' or sk.style == 'capture')")
s=s.replace("and sim.tick>=(self.throwReadyAt or 0) and self:rand()<0.05 then", "and sim.tick>=(self.throwReadyAt or 0) and self:rand()<0.12 then")
s=s.replace('        if t==2 or t==28 or t==54 then\n            if math.abs(d.x-p.x)<=bu.range*C then', '        if (t==2 or t==28 or t==54) and not d.ko then\n            if math.abs(d.x-p.x)<=bu.range*C then',1)
s=s.replace('        if p.cinematicConfirmed and t<54 then', '        if p.cinematicConfirmed and not d.ko and t<54 then',1)
j['assets']['scripts'][0]['source']=s;p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)

j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source'].replace('else idx,width,offset,up=9,920,0,0 end','else idx,width,offset,up=9,650,0,0 end');j['assets']['scripts'][0]['source']=s;p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
