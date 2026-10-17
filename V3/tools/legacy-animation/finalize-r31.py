from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if "GF_RELEASE_ID='dual-eye-grass-r31'" not in s:
 old="            G.pingpong(b, {localRotationZ = a0 - 5}, {localRotationZ = a0 + 6}, 1.6 + U.hash(i * 5 + j) * 1.4, 'InOutSine')"
 assert old in s
 s=s.replace(old,"            self.sway=self.sway or {}\n            self.sway[#self.sway+1]={node=b,base=a0,x=bx,h=h,phase=U.hash(i*19+j)*6.283185,period=3.2+U.hash(i*5+j)*2.8}",1)
 method='''function St:updateSway()
    for _,blade in ipairs(self.sway or {}) do
        local angle=blade.base+5*math.sin((self.app.t or 0)*6.283185/blade.period+blade.phase)
        local rad=math.rad(angle)
        blade.node:rot(angle):pos(blade.x-math.sin(rad)*blade.h/2,-175+math.cos(rad)*blade.h/2)
    end
end

'''
 s=s.replace('function St:camera(cx, zoom, floorY, sx, sy)',method+'function St:camera(cx, zoom, floorY, sx, sy)\n    self:updateSway()',1)
 s=s.replace('        self.burstBg = G.layer(app.layers.back)','        self.burstBg = G.layer(app.layers.back)\n        self.burstEye=G.bitmap(app.layers.back);self.burstEye.node:on(false)',1)
 s=s.replace('    if self.burstBg then self.burstBg:free() end','    if self.burstBg then self.burstBg:free() end\n    if self.burstEye then self.burstEye:free() end',1)
 s=s.replace('function S:drawBurstBackdrop()','local burstEyeData\nfunction S:drawBurstBackdrop()',1)
 s=s.replace('    L:begin()\n    local p\n    for _,f in ipairs(self.sim.f)', '    L:begin()\n    if self.burstEye then self.burstEye.node:on(false) end\n    local p\n    for _,f in ipairs(self.sim.f)',1)
 a=s.index('        L:shape(G.ELLIPSE,0,90,600,190');b=s.index('        for i=1,7 do',a)
 s=s[:a]+'''        burstEyeData=burstEyeData or require('gf_raiden_eye_r31')
        local index=p.t<6 and 0 or pulse==1 and 2 or p.t>=85 and 3 or 1
        local img=burstEyeData[self.tier or 'lo'][tostring(index)]
        local bmp=self.burstEye;bmp:draw(img,'eye'..index)
        local scale=W*0.86/img.w;bmp.node:pos(0,90):scale(scale,scale):rot(0):on(true)
        if bmp.lastFade~=fade or bmp.lastIndex~=index then
            for i=1,bmp.used do local c=img.pal[img.bytes[(i-1)*5+5]+1];bmp.kids[i]:color(c[1],c[2],c[3],(c[4] or 255)*fade) end
            bmp.lastFade=fade;bmp.lastIndex=index
        end
'''+s[b:]
 s=s.replace("__loaders['gf_fight'] = function()","__loaders['gf_raiden_eye_r31'] = function()\n"+(R/'project-inputs/gf_raiden_eye_r31.lua').read_text()+"end\n__loaders['gf_fight'] = function()",1)
 # Preserve the r30 continuation fix when rebuilding from an older base.
 s=s.replace("if d.invul > 0 or d.state == 'down'", "if (d.invul > 0 and not opts.ignoreInvul) or d.state == 'down'",1)
 s=s.replace("self:hit(p,d,per,'burst',{unblockable=true})","self:hit(p,d,per,'burst',{unblockable=true,ignoreInvul=true})")
 s=re.sub(r"GF_RELEASE_ID='[^']+'", "GF_RELEASE_ID='dual-eye-grass-r31'",s,count=1)
# Approved characters only: every menu and AI roster shares this list.
eye="__loaders['gf_raiden_eye_r31'] = function()\n"+(R/'project-inputs/gf_raiden_eye_r31.lua').read_text()+"end\n"
if "__loaders['gf_raiden_eye_r31'] = function()" in s:
 a=s.index("__loaders['gf_raiden_eye_r31'] = function()");b=s.index("__loaders[",a+10);s=s[:a]+eye+s[b:]
else:
 s=s.replace("__loaders['gf_scene_fight'] = function()",eye+"__loaders['gf_scene_fight'] = function()",1)
a=s.index("__loaders['gf_roster'] = function()");b=s.index("\nend\n__loaders[",a)
lines=[line for line in s[a:b].splitlines() if line.startswith("{key='raidenshogun'") or line.startswith("{key='nahida'")]
assert len(lines)==2
s=s[:a]+"__loaders['gf_roster'] = function()\nreturn {\n"+'\n'.join(lines)+"\n}"+s[b:]
s=re.sub(r"local PAIRS = \{\{.*?\}\}\n", "local PAIRS = {{'raidenshogun','nahida'}}\n",s,count=1,flags=re.S)
# Two centered cards, while keeping normal multi-character layout reusable.
s=s.replace('local COLS = 8','local COLS = math.min(8,#Art.roster)')
s=s.replace("self:hit(p,d,per,'burst',{unblockable=p.cinematicConfirmed==true})", "self:hit(p,d,per,'burst',{unblockable=p.cinematicConfirmed==true,ignoreInvul=p.cinematicConfirmed==true})")
s=s.replace('function FX:number(x, y, value, element, big, label)', 'function FX:number(x, y, value, element, big, label, hold)')
s=s.replace('t.fadeAt = app.t + (label and 0.9 or 0.6)', 't.fadeAt = app.t + (hold or (label and 0.9 or 0.6))')
s=s.replace('fx:number(x, y + 60, e.dmg, e.element, e.heavy)', "fx:number(x, y + 60, e.dmg, e.element, e.heavy or e.kind=='burst', nil, e.kind=='burst' and 1.3 or nil)")
j['assets']['scripts'][0]['source']=s;j['meta']['name']='雷电与纳西妲 · 双角色正式测试 r31';p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
for file in [R/'animation-tools/preview-engine-r23.js',R/'dist/actions/nahida/app.js',R/'dist/actions/raiden/app.js']:
 x=file.read_text();x=x.replace("else{effect(5,620,255,680,.68);", "else{const index=p<2?0:hitPhase(p)?2:p===a.frames.length-1?3:1;sprite(atlas,images,'burst_eye',index,620,265,450);")
 x=x.replace('v=r29','v=r31');file.write_text(x)
for file in [R/'editor-entry.js',R/'editor-bootstrap.js',R/'dist/editor/editor.js',R/'dist/editor/bootstrap.js',R/'dist/editor/play.js',R/'dist/index.html']:
 x=file.read_text().replace('dual-inbetweens-r30','dual-eye-grass-r31').replace('双方全动作补帧 r30 · 雷神大招三段修复','完整测试版 r31 · 雷眼与前景摆动');file.write_text(x)
for char in ['nahida','raiden']:
 file=R/'dist/actions'/char/'index.html';x=file.read_text().replace('v=r29','v=r31').replace('r30 · 雷神大招修复','r31 · 雷眼与前景修复');file.write_text(x)
print('r31 integrated: anchored grass sway, authored eye bitmap, r30 hit continuation preserved')
