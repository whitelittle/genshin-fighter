from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1];p=ROOT/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
def change(a,b):
 global s
 assert a in s,a[:100]
 s=s.replace(a,b,1)
if "GF_RELEASE_ID='nahida-capture-pool-r23'" not in s:
 change('select=9500, online=9500, vs=9500, fight=9500','select=14000, online=12000, vs=14000, fight=14000')
 change('batch=32, limit=10000','batch=32, limit=18000')
 change("    if not n then error('image pool exhausted', 2) end", """    if not n and G.reclaimDormant then
        G.reclaimDormant()
        n=table.remove(freeImg) or table.remove(freeSecond)
    end
    if not n then error('image pool exhausted; used='..G.counts.img..' capacity='..G.counts.img, 2) end""")
 change('local Bitmap = {}',"local dormantBitmaps=setmetatable({},{__mode='k'})\nlocal Bitmap = {}")
 change("    return setmetatable({node = g, kids = {}, cap = capacity or 0, used = 0, job = nil, key = nil}, Bitmap)","""    local bmp=setmetatable({node = g, kids = {}, cap = capacity or 0, used = 0, job = nil, key = nil}, Bitmap)
    dormantBitmaps[bmp]=true
    return bmp""")
 change('function Bitmap:ensure(n)\n    local kids = self.kids', '''function Bitmap:trim(keep)
    keep=keep or 0
    for i=#self.kids,keep+1,-1 do G.release(self.kids[i]);self.kids[i]=nil end
    self.used=math.min(self.used,keep)
    if keep==0 then self.key=nil end
end
function G.reclaimDormant()
    for bmp in pairs(dormantBitmaps) do
        if bmp~=G.activeBitmap and not bmp.job and not bmp.node.act then bmp:trim(0) end
    end
end
function Bitmap:ensure(n)
    local previous=G.activeBitmap;G.activeBitmap=self
    local kids = self.kids''')
 change('        kids[i] = c\n    end\nend\n\nfunction Bitmap:start', '        kids[i] = c\n    end\n    G.activeBitmap=previous\nend\n\nfunction Bitmap:start')
 change('function Bitmap:free()\n', 'function Bitmap:free()\n    dormantBitmaps[self]=nil\n')
 change("nahida        = {style = 'zone',  startup = 12, recovery = 16, damage = 70, cd = 140, delay = 14, w = 200, h = 220, fx = 'seed', hitstun = 30, snare = 40}","nahida        = {style = 'capture', startup = 30, recovery = 18, damage = 70, cd = 140, range = 1400, w = 280, h = 360, fx = 'capture', hitstun = 30}")
 change("    p.airSkill = p.y > 0", "    p.airSkill = p.y > 0\n    if p.key=='nahida' then p.aimX=p.foe.x;p.aimY=p.foe.y+170*C end")
 change("        if st == 'projectile' then\n            self:spawnProj", """        if st=='capture' then
            local ax,ay=p.aimX or d.x,p.aimY or (d.y+170*C)
            if abs(ax-p.x)<=sk.range*C and abs(d.x-ax)<=sk.w*C/2 and abs(d.y+170*C-ay)<=sk.h*C/2 then
                self:hit(p,d,{damage=sk.damage,hitstun=sk.hitstun,blockstun=16,push=5,level='mid',energy=8,shake=5},'skill')
            end
        elseif st == 'projectile' then
            self:spawnProj""")
 change("if st=='skill' then local startup=f.move.startup;return frameName('skill',t<startup/2 and 0 or t<startup and 1 or t<startup+6 and 2 or 3) end", """if st=='skill' then
        local startup=f.move.startup
        if f.key=='nahida' then return frameName('skill',t<6 and 0 or t<startup and 1 or t<startup+8 and 2 or 3) end
        return frameName('skill',t<startup/2 and 0 or t<startup and 1 or t<startup+6 and 2 or 3)
    end""")
 change('    self.animFx=G.bitmap(layers.ghost);self.animFx.node:on(false)', '    self.animFx=G.bitmap(layers.ghost);self.animFx.node:on(false)\n    self.aimLayer=G.layer(layers.fx)')
 change("    elseif st=='skill' then\n        idx,width,offset,up=4,130,25,260", """    elseif st=='skill' then
        if f.key=='nahida' then
            if t<f.move.startup or t>=f.move.startup+8 then self.animFx.node:on(false);return end
            idx,width,offset,up=3,280,((f.aimX or f.foe.x)-f.x)/100*f.face,(f.aimY or 17000)/100-f.y/100
        else
        idx,width,offset,up=4,130,25,260""")
 change("if t>=f.move.startup then idx,width,offset,up=6,180,(f.foe.x-f.x)/100*f.face,0 end\n    elseif st=='burst'", "if t>=f.move.startup then idx,width,offset,up=6,180,(f.foe.x-f.x)/100*f.face,0 end\n        end\n    elseif st=='burst'")
 change("        else idx,width,offset,up=9,630,0,0 end", "        else idx,width,offset,up=9,920,0,0 end")
 aim='''function V:drawCapture()
    local L=self.aimLayer;L:begin()
    local f=self.f
    if f.key=='nahida' and f.state=='skill' and f.move.style=='capture' then
        local t,su=f.t,f.move.startup
        local k=math.min(1,t/su);local ec={150,246,108};local white={230,255,192}
        local tx,ty=(f.aimX or f.foe.x)/C,(f.aimY or 170*C)/C
        local hx,hy=f.x/C+f.face*110,f.y/C+215
        local x=hx+(tx-hx)*math.min(1,k*1.8);local y=hy+(ty-hy)*math.min(1,k*1.8)
        local settle=math.max(0,math.min(1,(t-su)/12));local w,h=320*(1-settle*0.7),340*(1-settle*0.7)
        local a=math.min(1,t/5)*(1-settle);local thick=4
        L:rect(x,y,w,h,ec,0.055*a)
        for _,sx in ipairs({-1,1}) do for _,sy in ipairs({-1,1}) do
            L:rect(x+sx*(w/2-32),y+sy*h/2,64,thick,ec,a)
            L:rect(x+sx*w/2,y+sy*(h/2-32),thick,64,ec,a)
            L:rect(x+sx*(w/2-20),y+sy*(h/2-9),40,2,white,0.8*a)
        end end
        if t<su then
            local scanX=x-w/2+w*k
            L:rect(scanX,y,3,h-18,white,0.9*a)
            L:rect(scanX-10*f.face,y,22,h-18,ec,0.1*a)
            L:rect(x,y,30,2,ec,0.7*a);L:rect(x,y,2,30,ec,0.7*a)
            for i=1,4 do L:shape(G.STAR4,x+(i%2==0 and 1 or -1)*(w/2+18),y+(i<3 and 1 or -1)*(h/2+10),10,10,white,a,45) end
        else
            L:shape(G.RING,tx,ty,60+settle*220,60+settle*220,ec,0.8*a)
            L:shape(G.STAR4,tx,ty,55*(1-settle),55*(1-settle),white,a,45)
        end
    end
    L:finish()
end

'''
 change('function V:draw(budget)',aim+'function V:draw(budget)')
 change('    self:drawAnimatedFx()\n', '    self:drawAnimatedFx()\n    self:drawCapture()\n')
 change('    if self.animFx then self.animFx:free() end', '    if self.animFx then self.animFx:free() end\n    if self.aimLayer then self.aimLayer:free() end')
 # Replace generic cast flashes only for Nahida, leaving the hand/frame visual clear.
 change("            fx:spawn(fx.world, {shape = G.RING, x = p.x / C, y = p.y / C + 160, w = 80, col = ec", "            if p.key~='nahida' then\n            fx:spawn(fx.world, {shape = G.RING, x = p.x / C, y = p.y / C + 160, w = 80, col = ec")
 change("            au:play(au.ID.ecast[p.element])", "            end\n            au:play(au.ID.ecast[p.element])")
 # Original portrait introduction followed by slower, three-hit dream domain.
 change('function S:burstUpdate(p)\n', '''function S:burstUpdate(p)
    if p.key=='nahida' then
        local t,d,bu=p.t,p.foe,p.move
        local per={damage=bu.damage//bu.hits,hitstun=75,blockstun=18,push=3,level='mid',energy=0,shake=9,launch=13}
        if t==1 then self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style}) end
        if t==2 or t==28 or t==54 then
            if math.abs(d.x-p.x)<=bu.range*C then
                per.launch=t==54 and 26 or 13;per.knockdown=t==54
                local result=self:hit(p,d,per,'burst',{unblockable=p.cinematicConfirmed==true})
                if result=='hit' then p.cinematicConfirmed=true;p.invul=100 end
                if t>2 then self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style}) end
            end
        end
        if p.cinematicConfirmed and t<54 then
            p.x=math.max(-WALL+400*C,math.min(WALL-400*C,p.x))
            d.x=p.x+p.face*330*C;d.y=math.max(d.y,110*C);d.vx=0
        end
        if t>=90 then p.cinematicConfirmed=false;self:setState(p,p.y>0 and 'air' or 'idle') end
        return
    end
''')
 change("        return frameName('skill',t<8 and 4 or t<16 and 5 or t<36 and 6 or 7)", "        return frameName('skill',t<8 and 4 or t<22 and 5 or t<74 and 6 or 7)")
 change("    L:finish()\nend\n\nfunction S:draw()", '''    if not p then
        for _,f in ipairs(self.sim.f) do if f.key=='nahida' and f.state=='burst' then p=f end end
        if p then
            local W,H=self.app.W,self.app.H
            local fade=p.t<74 and 1 or math.max(0,(90-p.t)/16)
            local bloom=math.min(1,(p.t+8)/22)
            local pulse=(p.t<8 or (p.t>=28 and p.t<36) or (p.t>=54 and p.t<64)) and 1 or 0
            L:rect(0,0,W+40,H+40,{4,25,21},0.95*fade)
            L:shape(G.ELLIPSE,0,40,W*0.86,H*0.92,{24,93,66},0.75*fade,0,0.4)
            L:shape(G.ELLIPSE,0,-180,W*0.85,200,{111,190,71},(0.25+0.12*pulse)*fade)
            for i=1,3 do
                L:shape(G.RING,0,80,350+i*220*bloom,350+i*220*bloom,{132,211,102},(0.22+i*0.1)*fade,0,0.1)
            end
            for i=1,16 do
                local x=-W/2+(i*103)%W;local y=-H/2+(i*167+p.t*2)%H
                L:shape(G.STAR4,x,y,6+(i%3)*3,6+(i%3)*3,{225,250,172},0.55*fade,p.t+i*24)
            end
        end
    end
    L:finish()
end

function S:draw()''')
 change("GF_RELEASE_ID='dual-scale-throw-r22'", "GF_RELEASE_ID='nahida-capture-pool-r23'")
j['meta']['name']='雷电与纳西妲 · 取景框与梦境领域 r23';j['assets']['scripts'][0]['source']=s
p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(ROOT/'project-inputs/dual-character.lua').write_text(s)
print('Prepared draft r23: Nahida capture E, dream Q, 14000 pool and dormant bitmap reclamation')
