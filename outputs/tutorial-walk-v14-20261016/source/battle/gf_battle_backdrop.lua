__loaders['gf_battle_backdrop']=function()
local G = require('gf_gfx')
local Art = require('gf_art')
local K = require('gf_kits')
local U = require('gf_util')
local Sim = require('gf_sim')
local AI = require('gf_ai')
local FView = require('gf_fview')
local FX = require('gf_fx')
local Hud = require('gf_hud')
local Stage = require('gf_stage')
local UI = require('gf_ui')
local Online = require('gf_online')


local C=Sim.C
return function(S)
local burstEyeData
function S:drawBurstBackdrop()
    local L=self.burstBg;if not L then return end
    L:begin()
    if self.burstEye then self.burstEye.node:on(false) end
    if require('gf_character_cinematic_view').backdrop(self,L) then L:finish();return end
    local p
    for _,f in ipairs(self.sim.f) do if f.key=='raidenshogun' and f.state=='burst' and f.cinematicConfirmed then p=f end end
    if p then
        local W,H=self.app.W,self.app.H
        local fade=p.t<85 and 1 or math.max(0,(100-p.t)/15)
        local pulse=(p.t<8 or (p.t>=35 and p.t<44) or (p.t>=70 and p.t<85)) and 1 or 0
        self.app:cover(L,{10,5,28},0.94*fade)
        L:shape(G.ELLIPSE,0,70,W*0.8,H*0.7,{88,35,150},(0.55+0.15*pulse)*fade,0,0.4)
        burstEyeData=burstEyeData or require('gf_raiden_eye_r31')
        local index=p.t<6 and 0 or pulse==1 and 2 or p.t>=85 and 3 or 1
        local img=burstEyeData[self.tier or 'lo'][tostring(index)]
        local bmp=self.burstEye;bmp:draw(img,'eye'..index)
        local scale=W*0.86/img.w;bmp.node:pos(0,90):scale(scale,scale):rot(0):on(true)
        if bmp.lastFade~=fade or bmp.lastIndex~=index then
            for i=1,bmp.used do local c=img.pal[img.bytes[(i-1)*5+5]+1];bmp.kids[i]:color(c[1],c[2],c[3],(c[4] or 255)*fade) end
            bmp.lastFade=fade;bmp.lastIndex=index
        end
        for i=1,7 do
            local x=-W/2+i*W/8
            L:rect(x,0,5,H,{165,95,250},(0.2+0.1*pulse)*fade,-22+(i%3)*12)
        end
    end
    if not p then
        for _,f in ipairs(self.sim.f) do if f.key=='nahida' and f.state=='burst' then p=f end end
        if p then
            local W,H=self.app.W,self.app.H
            local fade=p.t<74 and 1 or math.max(0,(90-p.t)/16)
            local bloom=math.min(1,(p.t+8)/22)
            local pulse=(p.t<8 or (p.t>=28 and p.t<36) or (p.t>=54 and p.t<64)) and 1 or 0
            self.app:cover(L,{4,25,21},0.95*fade)
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


end
end
