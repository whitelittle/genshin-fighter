__loaders['gf_fview'] = function()


local G = require('gf_gfx')
local Art = require('gf_art')
local K = require('gf_kits')
local U = require('gf_util')

local V = {}
V.__index = V

local C = 100
local NEXT = {idle_0='idle_1',idle_1='idle_0',idle = 'walk1', walk1 = 'walk2', walk2 = 'walk1', slash = 'idle', special = 'idle', qRelease = 'idle',
              crouch = 'idle', jump = 'idle', hurt = 'idle', guard = 'idle', crouchGuard = 'crouch', down = 'crouch'}

function V.new(app, layers, fighter, tier)
    local self = setmetatable({app = app, f = fighter, tier = tier or 'hi', key = fighter.key,
                               element = fighter.element, ecol = K.elementColor[fighter.element] or {255, 255, 255}}, V)
    self.root = G.group(layers.body)
    self.spin = G.group(self.root)
    self.content = G.group(self.spin)
    self.aura = G.bitmap(self.content)       -- element glow behind the body
    self.slots = {G.bitmap(self.content), G.bitmap(self.content)}
    self.flash = G.bitmap(self.content)      -- white / ice overlay
    for _, s in ipairs(self.slots) do s.node:on(false) end
    self.aura.node:on(false)
    self.flash.node:on(false)
    self.animFx=G.bitmap(layers.ghost);self.animFx.node:on(false)
    self.aimLayer=G.layer(layers.fx)
    if fighter.key=='nahida' then self.captureBmp=G.bitmap(layers.fx);self.captureBmp.node:on(false) end
    self.assistants={}
    if fighter.key=='nahida' then for i=1,3 do self.assistants[i]=G.bitmap(layers.fx);self.assistants[i].node:on(false) end end
    self.front = nil
    self.want = 'idle'
    self.shadow = G.image(layers.shadow, G.ELLIPSE)
    self.shadow:color(0, 0, 0, 110):on(true)
    self.ghosts = {}
    for i = 1, 3 do
        local g = G.bitmap(layers.ghost)
        g.node:on(false)
        self.ghosts[i] = {bmp = g, x = 0, y = 0, life = 0, pose = nil, face = 1, a = 0}
    end
    self.ghostI = 0
    self.flashT = 0
    self.trail = 0
    self.walkT = 0
    self.shake = 0
    self.tilt, self.sx, self.sy, self.ox, self.oy = 0, 1, 1, 0, 0
    return self
end

function V:reserveBody(budget)
    if self.key~='raidenshogun' and self.key~='nahida' then return true end
    if not self.bodyCapacity then
        local name=self.key=='raidenshogun' and 'raiden' or 'nahida'
        local data=require('gf_animation_data')[name].lo
        local extra=require('gf_inbetween_data').poses[name].lo
        local n=0
        for _,bank in ipairs({data,extra}) do
            for _,img in pairs(bank) do if type(img)=='table' and img.n then n=math.max(n,img.n) end end
        end
        self.bodyCapacity=n
    end
    for _,slot in ipairs(self.slots) do
        slot.pinned=true -- Body buffers must survive dormant reclamation.
        if #slot.kids<self.bodyCapacity then
            slot:ensure(math.min(self.bodyCapacity,#slot.kids+budget))
            return false
        end
    end
    return true
end

function V:image(pose)
    if self.key=='raidenshogun' and pose:match('^idle_') then
        self.idleImages=self.idleImages or {}
        if not self.idleImages[pose] then
            local img=Art.pose(self.key,self.tier,pose=='idle_0' and 'basic_0' or 'basic_1')
            local aligned={};for k,v in pairs(img) do aligned[k]=v end
            -- Anchor the two real idle poses by their boot soles, not crop width.
            local function footCenter(a)
                local lo,hi=math.huge,-math.huge
                for i=1,a.n do
                    local o=(i-1)*5;local x,y,w,h=a.bytes[o+1],a.bytes[o+2],a.bytes[o+3],a.bytes[o+4]
                    if y<=a.ay+0.1 and y+h>a.ay+0.1 and math.abs(x+w/2-a.ax)<90 then
                        lo=math.min(lo,x-a.ax);hi=math.max(hi,x+w-a.ax)
                    end
                end
                return lo<hi and (lo+hi)/2 or 0
            end
            local base=Art.pose(self.key,self.tier,'basic_0')
            aligned.ox=(img.ox or 0)+footCenter(base)-footCenter(img)
            self.idleImages[pose]=aligned
        end
        return self.idleImages[pose]
    end
    return Art.pose(self.key,self.tier,pose)
end

local function frameName(sheet,index) return sheet .. '_' .. index end
local function attackPose(m,t,id)
    local sheet,frames='light',{0,1,2,3}
    if id=='light2' then frames={4,5,6,7}
    elseif id=='light3' then sheet='heavy'
    elseif id=='heavy' then sheet,frames='heavy',{4,5,6,7}
    elseif id=='crouchLight' then sheet,frames='air',{0,0,1,0}
    elseif id=='crouchHeavy' then sheet,frames='air',{2,2,3,2}
    elseif id=='airLight' then sheet,frames='air',{4,4,5,4}
    elseif id=='airHeavy' then sheet,frames='air',{6,6,7,6} end
    local phase=t<m.startup and (t<m.startup/2 and 1 or 2) or t<m.startup+m.active and 3 or 4
    return frameName(sheet,frames[phase])
end
function V:keyPose()
    local f=self.f;local st,t=f.state,f.t
    if f.airMove then return attackPose(f.airMove,f.airT or 0,f.airMoveId or 'airLight') end
    if st=='idle' or st=='intro' then return frameName('basic',0) end
    if st=='walk' or st=='back' then local i=self.walkT//8%6;return frameName('basic',st=='back' and 7-i or 2+i) end
    if st=='crouch' or st=='jumpsq' or st=='land' then return frameName('guard',t<5 and 0 or 1) end
    if st=='air' then return frameName('move',f.vy>0 and 1 or f.vy==0 and 2 or 3) end
    if st=='dash' then return frameName('move',t<5 and 4 or 5) end
    if st=='backdash' then return frameName('move',t<5 and 6 or 7) end
    if st=='attack' then return attackPose(f.move,t,f.moveId) end
    if st=='skill' then
        local startup=f.move.startup
        if f.key=='nahida' then return frameName('skill',t<4 and 0 or t<startup and 1 or not f.connected and t<14 and 2 or 3) end
        return frameName('skill',t<startup/2 and 0 or t<startup and 1 or t<startup+6 and 2 or 3)
    end
    if st=='burst' then
        if f.key=='raidenshogun' then
            if not f.cinematicConfirmed then return frameName('qburst',0) end
            if t<16 then return frameName('qburst',t<9 and 1 or 2) end
            if t<24 or (t>=35 and t<44) or (t>=70 and t<85) then return frameName('qburst',3) end
            return frameName('qburst',t>=85 and 0 or 2)
        end
        return frameName('skill',t<8 and 4 or t<22 and 5 or t<74 and 6 or 7)
    end
    if st=='throw' and f.key=='nahida' then return frameName('skill',t<12 and 4 or t<30 and 5 or t<58 and 6 or 7) end
    if st=='throw' then return frameName('throw',t<12 and 0 or t<24 and 1 or t<36 and 2 or 3) end
    if st=='thrown' and f.foe.key=='nahida' then return frameName('basic',0) end
    if st=='thrown' then return frameName('victim',t<12 and 0 or t<24 and 1 or 2) end
    if st=='airhit' then return frameName('victim',3) end
    if st=='hit' then return frameName('hurt',0) end
    if st=='down' then return frameName('hurt',3) end
    if st=='getup' then return frameName('hurt',t<8 and 4 or 5) end
    if st=='block' then return frameName('guard',6) end
    if st=='cblock' then return frameName('guard',7) end
    if st=='win' then return frameName('hurt',6) end
    if st=='lose' then return frameName('hurt',7) end
    return frameName('basic',0)
end
local inbetweenKeys
function V:middle(sheet,i,j)
    inbetweenKeys=inbetweenKeys or require('gf_inbetween_data').keys
    local k=inbetweenKeys[self.key=='raidenshogun' and 'raiden' or 'nahida']
    return k[sheet..'_'..i..'_'..j] or k[sheet..'_'..j..'_'..i] or frameName(sheet,i)
end
function V:sequence(sheet,frames,ends,t)
    local start=0
    for i,finish in ipairs(ends) do
        if t<finish then
            local span=finish-start;local window=math.min(3,math.max(1,math.floor(span*0.35)))
            if span>1 and t>=finish-window then return self:middle(sheet,frames[i],frames[i%#frames+1]) end
            return frameName(sheet,frames[i])
        end
        start=finish
    end
    return frameName(sheet,frames[#frames])
end
function V:attackFrames(m,t,id)
    local sheet,frames='light',{0,1,2,3}
    if id=='light2' then frames={4,5,6,7} elseif id=='light3' then sheet='heavy'
    elseif id=='heavy' then sheet,frames='heavy',{4,5,6,7}
    elseif id=='crouchLight' then sheet,frames='air',{0,0,1,0}
    elseif id=='crouchHeavy' then sheet,frames='air',{2,2,3,2}
    elseif id=='airLight' then sheet,frames='air',{4,4,5,4}
    elseif id=='airHeavy' then sheet,frames='air',{6,6,7,6} end
    return self:sequence(sheet,frames,{math.ceil(m.startup/2),m.startup,m.startup+m.active,m.startup+m.active+m.recovery},t)
end
function V:animatedPose()
    local f=self.f;local st,t=f.state,f.t
    if f.airMove then return self:attackFrames(f.airMove,f.airT or 0,f.airMoveId or 'airLight') end
    if st=='idle' and f.key=='raidenshogun' then return 'idle_'..((t//40)%2) end
    if st=='idle' or st=='intro' then return frameName('basic',0) end
    if st=='walk' or st=='back' then
        local i=self.walkT//8%6
        return frameName('basic',st=='back' and 7-i or 2+i)
    end
    if st=='attack' then return self:attackFrames(f.move,t,f.moveId) end
    if st=='crouch' or st=='jumpsq' or st=='land' then return self:sequence('guard',{0,1},{5,12},math.min(t,11)) end
    if st=='dash' then return self:sequence('move',{4,5},{5,14},t) end
    if st=='backdash' then return self:sequence('move',{6,7},{5,18},t) end
    if st=='air' then
        if f.vy>0 and f.vy<3*C then return self:middle('move',1,2) end
        if f.vy<=0 and f.vy>-3*C then return self:middle('move',2,3) end
    end
    if st=='skill' then
        if f.key=='nahida' then
            if f.connected then return self:sequence('skill',{3,0},{27,30},t) end
            return self:sequence('skill',{0,1,2,3},{4,8,14,30},t)
        end
        local su=f.move.startup
        return self:sequence('skill',{0,1,2,3},{math.ceil(su/2),su,su+6,su+f.move.recovery},t)
    end
    if st=='burst' then
        if f.key=='nahida' then return self:sequence('skill',{4,5,6,7},{8,22,74,90},t) end
        if f.cinematicConfirmed then return self:sequence('qburst',{1,2,3,2,3,2,3,0},{9,16,24,35,44,70,85,94},t) end
    end
    if st=='throw' then
        if f.key=='nahida' then return self:sequence('skill',{4,5,6,7},{12,30,58,76},t) end
        return self:sequence('throw',{0,1,2,3},{12,24,36,50},t)
    end
    if st=='thrown' and f.foe.key~='nahida' then return self:sequence('victim',{0,1,2},{12,24,30},t) end
    if st=='thrown' then return self:sequence('basic',{0,1},{18,36},t%36) end
    if st=='airhit' and t>=3 and t<=5 then return self:middle('victim',2,3) end
    if st=='hit' and t>=3 and t<=5 then return self:middle('hurt',0,1) end
    if st=='down' and not f.ko and t>=35 then return self:middle('hurt',3,4) end
    if st=='getup' then return self:sequence('hurt',{4,5},{8,16},t) end
    if st=='block' and t>=3 and t<=5 then return self:middle('guard',6,2) end
    if st=='cblock' and t>=3 and t<=5 then return self:middle('guard',7,4) end
    if st=='win' and t%30>=22 then return self:middle('hurt',6,6) end
    if st=='lose' and t%30>=22 then return self:middle('hurt',7,7) end
    return self:keyPose()
end

function V:poseFor()
    if self.key=='raidenshogun' or self.key=='nahida' then return self:animatedPose() end
    local f = self.f
    local st = f.state
    if f.airMove then
        local m = f.airMove
        if (f.airT or 0) < m.startup and m.windup then return m.windup end
        return m.pose or 'jump'
    end
    if st == 'idle' or st == 'intro' then return 'idle' end
    if st == 'walk' or st == 'back' then
        return ((self.walkT // 10) % 2 == 0) and 'walk1' or 'walk2'
    end
    if st == 'crouch' or st == 'jumpsq' or st == 'land' or st == 'getup' then return 'crouch' end
    if st == 'air' then return 'jump' end
    if st == 'dash' then return 'walk2' end
    if st == 'backdash' then return 'jump' end
    if st == 'attack' or st == 'throw' then
        local m = f.move
        if m.windup and f.t < m.startup then return m.windup end
        return m.pose or 'slash'
    end
    if st == 'skill' then
        local m = f.move
        if f.t < m.startup then return 'guard' end
        return (m.style == 'rising') and 'jump' or 'special'
    end
    if st == 'burst' then return 'qRelease' end
    if st == 'hit' or st == 'airhit' or st == 'thrown' or st == 'lose' then return 'hurt' end
    if st == 'down' then return 'down' end
    if st == 'block' then return 'guard' end
    if st == 'cblock' then return 'crouchGuard' end
    if st == 'win' then return 'special' end
    return 'idle'
end

local function slotHas(s, pose) return s.key == pose and not s.job end

function V:updatePose(budget)
    local want = self:poseFor()
    self.want = want
    local front, back = self.front, nil
    for _, s in ipairs(self.slots) do if s ~= front then back = s end end
    if front and slotHas(front, want) then
        local nxt = NEXT[want]
        if nxt and back and not slotHas(back, nxt) then
            if not back.job or back.job.key ~= nxt then back:start(self:image(nxt), nxt) end
            back:step(math.min(budget // 2, 220))
        end
        return
    end
    if not slotHas(back, want) then
        if not back.job then back:start(self:image(want), want) end
        local locomotion=self.f.state=='idle' or self.f.state=='walk' or self.f.state=='back' or self.f.state=='intro'
        back:step(math.min(budget,locomotion and 320 or 520))
    end
    -- Publish a finished buffer even if simulation has moved on by a tick.
    -- This bounds visual delay and prevents short attack phases starving forever.
    if not back.job and back.key then
        back.node:on(true)
        if front then front.node:on(false) end
        self.front = back
        self.poseImg = self:image(back.key)
        self.poseChanged = true
    end
end

function V:spawnGhost()
    if self.key=='raidenshogun' or self.key=='nahida' then return end
    if not self.poseImg then return end
    self.ghostI = self.ghostI % #self.ghosts + 1
    local g = self.ghosts[self.ghostI]
    local sil = Art.silhouette(self.key, self.front.key)
    g.bmp:draw(sil, self.front.key, self.ecol)
    g.x, g.y, g.face, g.life, g.u = self.wx, self.wy, self.f.face, 14, sil.u
    g.bmp.node:on(true)
end

function V:onHit(e)
    self.flashT = 5
    self.flashTint = {255, 255, 255}
    self.shake = e.heavy and 10 or 6
end

function V:onBlock()
    self.flashT = 3
    self.flashTint = {150, 210, 255}
    self.shake = 4
end


local effectData
function V:drawAnimatedFx()
    if not self.animFx then return end
    if self.key~='raidenshogun' and self.key~='nahida' then self.animFx.node:on(false);return end
    local f=self.f;local t,st=f.t,f.state;local idx,width,offset,up
    if st=='attack' and f.move and t>=f.move.startup and t<f.move.startup+f.move.active then idx,width,offset,up=0,210,170,160
    elseif st=='skill' then
        if f.key=='nahida' then
            self.animFx.node:on(false);return
        else
        idx,width,offset,up=4,130,25,260
        if t>=f.move.startup then idx,width,offset,up=6,180,(f.foe.x-f.x)/100*f.face,0 end
        end
    elseif st=='burst' then
        if f.key=='raidenshogun' then
            if f.cinematicConfirmed then
                if t<16 then idx,width,offset,up=5,250,0,110
                elseif t<24 or (t>=35 and t<44) or (t>=70 and t<85) then idx,width,offset,up=9,640,200,10
                elseif t<70 then idx,width,offset,up=5,230,0,110
                elseif t<94 then idx,width,offset,up=10,460,200,0 end
            end
        else idx,width,offset,up=9,650,0,0 end
    end
    if not idx then self.animFx.node:on(false);return end
    effectData=effectData or require('gf_animation_effects')
    local bank=effectData[f.key=='raidenshogun' and 'raiden' or 'nahida']
    if not bank then self.animFx.node:on(false);return end
    local img=bank[tostring(idx)]
    local scale=width/img.w
    self.animFx:drawMany({{img=img,ox=0,oy=0,s=scale}})
    self.animFx.node:pos(f.x/100+offset*f.face,f.y/100+up):scale(f.face,1):on(true)
end

local assistantData
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

local captureData
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

function V:draw(budget)
    local f = self.f
    local st = f.state
    local tick=self.app.scene and self.app.scene.sim and self.app.scene.sim.tick or self.app.frame
    local elapsed=math.max(0,tick-(self.lastAnimTick or tick))
    self.lastAnimTick=tick
    if st=='walk' or st=='back' then
        self.walkT=self.walkT+(f.hitstop>0 and 0 or elapsed)
    else self.walkT=0 end
    self:updatePose(budget)
    self:drawAnimatedFx()
    self:drawCapture()
    self:drawAssistants()
    local x, y = f.x / C, f.y / C
    self.wx, self.wy = x, y
    local tilt, sx, sy, ox, oy = 0, 1, 1, 0, 0
    local t = f.t
    if st == 'idle' then
        sy = f.key=='raidenshogun' and 1 or 1 + 0.003 * math.sin(self.app.t * 2 + f.id)
    elseif st == 'walk' or st == 'back' then
        oy = math.abs(math.sin(self.walkT * math.pi / 8)) * 1.5
        tilt = (st == 'walk' and -3 or 3)
    elseif st == 'dash' then
        tilt = -10
        sx = 1.06
    elseif st == 'backdash' then
        tilt = 12
    elseif st == 'jumpsq' or st == 'land' then
        sy, sx = 0.9, 1.06
    elseif st == 'air' then
        local vy = f.vy / C
        sy = 1 + U.clamp(vy * 0.006, -0.06, 0.08)
        sx = 2 - sy
        if f.airMove then tilt = -(f.airMove.tilt or 0) end
    elseif st == 'attack' then
        local m = f.move
        if t < m.startup then
            local k = t / math.max(1, m.startup)
            tilt = (m.tilt or 0) * 0.5 * k + 4 * k
            sx = 1 - 0.04 * k
        elseif t < m.startup + m.active then
            tilt = -(m.tilt or 0)
            sx = 1.06
            ox = 8
        else
            local k = U.clamp((t - m.startup - m.active) / math.max(1, m.recovery), 0, 1)
            tilt = -(m.tilt or 0) * (1 - k)
        end
    elseif st == 'skill' or st == 'burst' then
        if t < 6 then sy, sx = 0.94, 1.05 else sx = 1.03 end
    elseif st == 'thrown' then
        tilt,ox=0,0
    elseif st == 'hit' then
        tilt = 8 + math.min(f.stun or 0, 10)
        ox = -10
    elseif st == 'airhit' then
        tilt = U.clamp(f.vy / C * 2.2, -40, 50) + 20
    elseif st == 'block' or st == 'cblock' then
        ox = -6
    elseif st == 'win' then
        sy = 1 + 0.015 * math.sin(self.app.t * 4)
    end
    if self.shake > 0 then
        ox = ox + ((self.shake % 2 == 0) and 1 or -1) * self.shake * 0.8
        self.shake = self.shake - 1
    end
    if f.key=='nahida' and (st=='attack' or st=='skill' or st=='burst' or st=='throw' or st=='dash' or st=='win') then
        local hover=st=='burst' and 65 or st=='skill' and 38 or 25
        if st=='skill' and t>f.move.startup then hover=hover*(1-U.clamp((t-f.move.startup)/f.move.recovery,0,1)) end
        oy=oy+hover+5*math.sin(self.app.t*6+f.id)
    end
    self.tilt, self.sx, self.sy, self.ox, self.oy = tilt, sx, sy, ox, oy
    local face = f.face
    local hc = 150 * f.size
    if st == 'airhit' then
        self.root:pos(x + ox * face, y + oy):rot(0):scale(face * sx, sy)
        self.spin:pos(0, hc):rot(tilt * face)
        self.content:pos(0, -hc)
    else
        self.root:pos(x + ox * face, y + oy):rot(tilt * face):scale(face * sx, sy)
        self.spin:pos(0, 0):rot(0)
        self.content:pos(0, 0)
    end
    local img = self.poseImg
    if self.front and img then
        self.front.node:scale(img.u, img.u)
    end
    local hgt = math.max(0, y+oy)
    local k = U.clamp(1 - hgt / 500, 0.35, 1)
    self.shadow:pos(x, 4):size(170 * k * f.size, 26 * k):color(0, 0, 0, 120 * k)
    local coat = f.coat > 0 or st == 'burst'
    local c = self.ecol
    if coat then
        local pulse = 0.5 + 0.5 * math.sin(self.app.t * 10)
        self.aura.node:on(false)
        if not self.glow then self.glow = G.image(self.content, G.ELLIPSE); self.glow:sibling(0) end
        self.glow:pos(0, 170 * f.size):size(300 * f.size, 380 * f.size):color(c[1], c[2], c[3], 70 + 50 * pulse):soft(0.5):rot(0):scale(1, 1):on(true)
        if self.app.frame % 6 == 0 and self.fx then
            self.fx:spawn(self.fx.world, {shape = G.STAR4, x = x + (math.random() - 0.5) * 140, y = y + 40 + math.random() * 200, w = 14 + math.random() * 10,
                                          col = c, a = 1, to = {y = y + 300 + math.random() * 80, s = 0.3, a = 0}, dur = 0.7})
        end
    else
        self.aura.node:on(false)
        if self.glow then self.glow:on(false) end
    end
    local frozen = f.frozen > 0
    if (self.flashT > 0 or frozen) and img then
        -- The published body may still be an aligned idle buffer while hit pose draws.
        -- Its exact image carries the correct crop/foot offset; no legacy alias lookup.
        local animated=self.key=='raidenshogun' or self.key=='nahida'
        local sil = animated and img or Art.silhouette(self.key, self.front.key)
        local tint = frozen and {170, 235, 255} or self.flashTint
        self.flash:draw(sil, self.front.key .. (frozen and ':ice' or ':flash'), tint)
        local a = frozen and 140 or (30 + self.flashT * 28)
        for i = 1, self.flash.used do self.flash.kids[i]:color(tint[1], tint[2], tint[3], a) end
        self.flash.node:scale(sil.u, sil.u):on(true)
        self.flash.node:front()
        if self.flashT > 0 then self.flashT = self.flashT - 1 end
    else
        self.flash.node:on(false)
    end
    local speed = math.abs(f.vx) / C
    local fast = speed > 9 and (st == 'dash' or st == 'backdash' or st == 'skill' or st == 'burst' or (st == 'airhit' and f.ko))
    if fast and self.app.frame % 3 == 0 then self:spawnGhost() end
    for _, g in ipairs(self.ghosts) do
        if g.life > 0 then
            g.life = g.life - 1
            local a = g.life / 14
            g.bmp.node:pos(g.x, g.y):scale(g.face * g.u, g.u)
            local c = self.ecol
            for i = 1, g.bmp.used do g.bmp.kids[i]:color(c[1], c[2], c[3], 110 * a) end
            if g.life == 0 then g.bmp.node:on(false) end
        end
    end
end

function V:free()
    if self.animFx then self.animFx:free() end
    if self.aimLayer then self.aimLayer:free() end
    if self.captureBmp then self.captureBmp:free() end
    for _,bmp in ipairs(self.assistants) do bmp:free() end
    for _, s in ipairs(self.slots) do s:free() end
    self.aura:free()
    self.flash:free()
    for _, g in ipairs(self.ghosts) do g.bmp:free() end
    G.release(self.shadow)
    G.release(self.content)
    G.release(self.spin)
    if self.glow then G.release(self.glow) end
    G.release(self.root)
end

return V
end
