from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
def change(a,b):
 global s
 assert a in s,a[:120];s=s.replace(a,b,1)
if "GF_RELEASE_ID='nahida-frame-strike-r26'" not in s:
 change("nahida        = {style = 'capture', startup = 30, recovery = 18, damage = 70, cd = 140, range = 1400, w = 280, h = 360, fx = 'capture', hitstun = 30}","nahida        = {style = 'capture', startup = 8, recovery = 22, damage = 70, cd = 140, range = 650, w = 280, h = 340, fx = 'capture', hitstun = 30}")
 change("if p.key=='nahida' then p.aimX=p.foe.x;p.aimY=p.foe.y+170*C end", "if p.key=='nahida' then p.castX=p.x;p.castY=p.y+190*C;p.castFace=p.face;p.captureHitT=nil;p.captureHitX=nil;p.captureHitY=nil end")
 change("if f.key=='nahida' then return frameName('skill',t<6 and 0 or t<startup and 1 or t<startup+8 and 2 or 3) end", "if f.key=='nahida' then return frameName('skill',t<4 and 0 or t<startup and 1 or not f.connected and t<14 and 2 or 3) end")
 change("            if t<f.move.startup or t>=f.move.startup+8 then self.animFx.node:on(false);return end\n            idx,width,offset,up=3,280,((f.aimX or f.foe.x)-f.x)/100*f.face,(f.aimY or 17000)/100-f.y/100", "            if not f.captureHitT or t>=f.captureHitT+6 then self.animFx.node:on(false);return end\n            idx,width,offset,up=3,320,((f.captureHitX or f.foe.x)-f.x)/C*f.face,(f.captureHitY or 190*C)/C-f.y/C")
 start=s.index('function V:drawCapture()');end=s.index('\nfunction V:draw(budget)',start)
 s=s[:start]+'''function V:drawCapture()
    local L=self.aimLayer;L:begin()
    local f=self.f
    if f.key=='nahida' and f.state=='skill' and f.t>=4 then
        local t=f.t;local steps={0,0.10,0.26,0.48,0.74,1}
        local frame=math.min(6,math.max(1,t-7));local k=t<8 and 0 or steps[frame]
        local face=f.castFace or f.face
        local x=(f.castX or f.x)/C+face*(110+540*k);local y=(f.castY or 190*C)/C
        local hit=f.captureHitT~=nil;local age=hit and t-f.captureHitT or math.max(0,t-14)
        local w,h=170+150*k,210+130*k;local a=1
        if hit then
            x=(f.captureHitX or f.foe.x)/C;y=(f.captureHitY or 190*C)/C
            local impact=({1.16,0.8,0.38,0.15})[math.min(4,age+1)]
            w,h=320*impact,340*impact;a=math.max(0,1-age/6)
        elseif t>=14 then a=math.max(0,1-age/4) end
        local ec={162,255,116};local white={241,255,211}
        if a>0 then
            L:rect(x,y,w,h,ec,(hit and 0.2 or 0.08)*a)
            for _,sx in ipairs({-1,1}) do for _,sy in ipairs({-1,1}) do
                L:rect(x+sx*(w/2-27),y+sy*h/2,54,5,ec,a)
                L:rect(x+sx*w/2,y+sy*(h/2-27),5,54,ec,a)
                L:rect(x+sx*(w/2-18),y+sy*(h/2-9),36,2,white,a)
            end end
            if t>=8 and not hit then
                for i=1,3 do L:rect(x-face*(w/2+24+i*25),y+(i-2)*82,55+i*20,3,ec,a*(0.65-i*0.12)) end
            elseif hit then
                L:shape(G.STAR4,x,y,120*(1-age/7),120*(1-age/7),white,a,45)
                for i=1,4 do L:shape(G.STAR4,x+(i%2==0 and 1 or -1)*(70+age*24),y+(i<3 and 1 or -1)*(70+age*16),16,16,ec,a,45) end
            end
        end
    end
    L:finish()
end
''' +s[end:]
 old="""        if st=='capture' then
            local ax,ay=p.aimX or d.x,p.aimY or (d.y+170*C)
            if abs(ax-p.x)<=sk.range*C and abs(d.x-ax)<=sk.w*C/2 and abs(d.y+170*C-ay)<=sk.h*C/2 then
                self:hit(p,d,{damage=sk.damage,hitstun=sk.hitstun,blockstun=16,push=5,level='mid',energy=8,shake=5},'skill')
            end
        elseif st == 'projectile' then"""
 change(old,"        if st == 'projectile' then")
 change("    if st == 'rush' and t >= sk.startup", """    if st=='capture' and t>=8 and t<=13 and not p.connected then
        local steps={0,0.10,0.26,0.48,0.74,1};local k=steps[t-7]
        local cx=(p.castX or p.x)+(p.castFace or p.face)*math.floor((110+540*k)*C)
        local cy=p.castY or 190*C
        local hx0,hx1,hy0,hy1=self:hurtbox(d)
        if hx0 and overlap(cx-sk.w*C/2,cx+sk.w*C/2,cy-sk.h*C/2,cy+sk.h*C/2,hx0,hx1,hy0,hy1) then
            local result=self:hit(p,d,{damage=sk.damage,hitstun=sk.hitstun,blockstun=16,push=9,level='mid',energy=8,shake=8},'skill')
            if result then p.captureHitT=t;p.captureHitX=d.x;p.captureHitY=cy end
        end
    end
    if st == 'rush' and t >= sk.startup""")
 s=s.replace("GF_RELEASE_ID='nahida-integrated-r25'","GF_RELEASE_ID='nahida-frame-strike-r26'")
 j['meta']['name']='雷电与纳西妲 · 草神快速撞框 r26';j['assets']['scripts'][0]['source']=s
 p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
# Same discrete six-frame forward strike in the preview, without a scanning/target-lock stage.
method='''function capture(p,x,ground){
 const steps=[0,.10,.26,.48,.74,1],frame=Math.max(0,Math.min(5,Math.floor(time-8))),k=time<8?0:steps[frame],hit=p>=3,age=hit?localAt(3):0;
 let cx=x+140+260*k,cy=ground-175,w=170+150*k,h=210+130*k,alpha=p===0?0:1;
 if(hit){cx=810;const squash=[1.16,.8,.38,.15][Math.min(3,Math.floor(age))];w=320*squash;h=340*squash;alpha=clamp(1-age/6);}
 ctx.save();ctx.globalAlpha=alpha;ctx.fillStyle=hit?'rgba(190,255,133,.2)':'rgba(150,255,108,.08)';ctx.fillRect(cx-w/2,cy-h/2,w,h);
 for(const sx of [-1,1])for(const sy of [-1,1]){const bx=cx+sx*w/2,by=cy+sy*h/2;line(bx,by,bx-sx*54,by,'#adff90',5);line(bx,by,bx,by-sy*54,'#adff90',5);line(bx-sx*8,by-sy*9,bx-sx*36,by-sy*9,'#f0ffdd',2);}
 if(!hit&&time>=8){for(let i=1;i<=3;i++)line(cx-w/2-25-i*25,cy+(i-2)*82,cx-w/2-85-i*35,cy+(i-2)*82,'#b6ff8d',3,.6-i*.12);}
 if(hit){effect(3,810,ground-175,320+age*20,clamp(1-age/6));for(const sx of [-1,1])for(const sy of [-1,1])line(810+sx*60,cy+sy*60,810+sx*(110+age*15),cy+sy*(110+age*15),'#efffd5',4,clamp(1-age/6));}
 ctx.restore();}
'''
for file in [R/'animation-tools/preview-engine-r23.js',R/'dist/actions/nahida/app.js',R/'dist/actions/raiden/app.js']:
 t=file.read_text();a=t.index('function capture(');b=t.index('function hitPhase(',a);t=t[:a]+method+t[b:]
 t=t.replace("name:'E · 所闻遍计 · 取景扫描',sheet:'skill',frames:[0,1,1,2,3],dur:[8,18,24,10,18],phase:['轻浮起势','双手取景','扫描与锁定','收框命中','缓缓落下']", "name:'E · 所闻遍计 · 撞框',sheet:'skill',frames:[0,1,2,3,3],dur:[4,4,6,5,11],phase:['抬手','框成形','快速撞出','命中停顿与碎光','收势']")
 t=t.replace('v=r25','v=r26');file.write_text(t)
for file in [R/'dist/actions/nahida/index.html',R/'dist/actions/raiden/index.html']:
 file.write_text(file.read_text().replace('v=r25','v=r26'))
for file in [R/'editor-entry.js',R/'dist/editor/editor.js',R/'editor-bootstrap.js',R/'dist/editor/bootstrap.js',R/'dist/editor/play.js',R/'dist/index.html']:
 file.write_text(file.read_text().replace('nahida-integrated-r25','nahida-frame-strike-r26').replace('草神重做已接入对战 r25','草神 E 快速撞框 r26'))
print('r26: raise 4f, frame 4f, six discrete strike frames, collision/impact/hitstop; no target tracking')
