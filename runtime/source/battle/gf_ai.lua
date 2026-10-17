__loaders['gf_ai'] = function()
local K = require('gf_kits')

local AI = {}
AI.__index = AI

local B = {U = 1, D = 2, L = 4, R = 8, LP = 16, HP = 32, SK = 64, BU = 128, DA = 256, TH = 512}
local C = 100

local LEVELS = {
    {react=30,block=.12,comboLen=1,aggro=.28,antiAir=.10,punish=.12,burstUse=.20,jump=.002,think=18,attackGap=36,throwChance=.08},
    {react=22,block=.30,comboLen=2,aggro=.42,antiAir=.28,punish=.28,burstUse=.45,jump=.005,think=12,attackGap=24,throwChance=.12},
    {react=12,block=.60,comboLen=3,aggro=.58,antiAir=.55,punish=.62,burstUse=.75,jump=.008,think=8,attackGap=14,throwChance=.20},
    {react=6,block=.82,comboLen=4,aggro=.72,antiAir=.78,punish=.88,burstUse=.95,jump=.01,think=5,attackGap=8,throwChance=.28},
}

function AI.new(sim, id, level, seed)
    local self = setmetatable({sim = sim, id = id, level=LEVELS[level] and level or 2, seed = seed or (id * 7919 + 13),
                               plan = nil, planT = 0, hold = 0, press = 0, seen = {}, chain = 0, blockFor = 0}, AI)
    self:profile(sim.f[id].key);return self
end

function AI:profile(key)
    local lv={};for k,v in pairs(LEVELS[self.level])do lv[k]=v end
    -- The long polearm needs more openings on beginner/normal; change policy,
    -- never player damage, hit boxes, or shared fighter rules.
    if key=='arlecchino' and self.level<=2 then lv.react=lv.react+4;lv.attackGap=lv.attackGap+8;lv.think=lv.think+2;lv.block=lv.block*.8;lv.comboLen=math.max(1,lv.comboLen-1) end
    self.lv=lv;self.profileKey=key;self.thinkAt=0;self.nextAttack=0;self.comboHit=nil;self.blockDecision=nil;self.blockFor=0;self.throwReadyAt=0;self.moveHold=0;self.chain=0;self.seen={};self.lastOut=0
end

function AI:rand()
    self.seed = (self.seed * 1103515245 + 12345) & 0x7fffffff
    return (self.seed % 10000) / 10000
end

local function dirTo(p) return p.foe.x >= p.x and B.R or B.L end
local function dirAway(p) return p.foe.x >= p.x and B.L or B.R end

function AI:observe(foe)
    local s = self.seen
    s[#s + 1] = {state = foe.state, t = foe.t, x = foe.x, y = foe.y, vy = foe.vy, move = foe.move, moveId = foe.moveId,
                 airMove = foe.airMove,hitId=foe.hitId}
    if #s > 40 then table.remove(s, 1) end
end

function AI:delayed()
    local s = self.seen
    local i = #s - self.lv.react
    if i < 1 then i = 1 end
    return s[i]
end

local function attacking(o)
    return o and (o.state == 'attack' or o.state == 'skill' or o.state == 'burst' or o.airMove ~= nil)
end

function AI:throwChoice(p,foe,dist)
    local sim=self.sim
    if sim.tick<(self.throwReadyAt or 0) or sim.tick<(self.throwThinkAt or 0) then return 0 end
    local allowed=foe.state=='idle' or foe.state=='walk' or foe.state=='back' or foe.state=='block' or foe.state=='cblock' or foe.state=='crouch' or foe.state=='land'
    if p.y>0 or foe.y>0 or foe.invul>0 or not allowed or dist*C>sim:throwRange(p) then return 0 end
    -- One shared policy for every fighter: evaluate at most once per 18 frames.
    self.throwThinkAt=sim.tick+18
    local chance=self.lv.throwChance*((foe.state=='block' or foe.state=='cblock') and 1.4 or 1)
    if self:rand()>=chance then return 0 end
    local out=self:edge(B.TH)
    if out~=0 then self.throwReadyAt=sim.tick+480;self.throwAttempts=(self.throwAttempts or 0)+1 end
    return out
end

function AI:decide()
    local sim = self.sim
    local p = sim.f[self.id]
    if p.key~=self.profileKey then self:profile(p.key) end
    local foe = p.foe
    self:observe(foe)
    if sim.phase ~= 'fight' then return 0 end
    local lv = self.lv
    local o = self:delayed()
    local dist = math.abs(foe.x - p.x) / C
    local toward, away = dirTo(p), dirAway(p)
    local out = 0

    if p.state == 'hit' or p.state == 'airhit' or p.state == 'down' or p.state == 'getup' then
        self.chain = 0
        if self:rand() < lv.block then out = away end
        return out
    end

    if (p.state == 'attack' or p.airMove) and p.connected then
        if self.chain < lv.comboLen and p.t >= 2 and p.hitstop==0 and self.comboHit~=p.hitId then
            self.comboHit=p.hitId
            self.chain = self.chain + 1
            local id = p.moveId or p.airMoveId
            if id == 'light1' then out = B.LP
            elseif id == 'light2' then out = (p.kit.weapon.light3 and self:rand() < 0.6) and B.LP or B.HP
            elseif id == 'light3' or id == 'crouchLight' then out = B.HP
            elseif id == 'heavy' or id == 'crouchHeavy' then
                if p.energy >= 100 and self:rand() < lv.burstUse then out = B.BU
                elseif p.skillCd == 0 then out = B.SK end
            elseif id == 'airLight' then out = B.HP end
            if self.lastOut == out then out = 0 end
            self.lastOut = out
            return out
        end
        self.lastOut = 0
        return 0
    end
    if p.state ~= 'idle' and p.state ~= 'walk' and p.state ~= 'back' and p.state ~= 'crouch' and p.state ~= 'air' and p.state ~= 'land' then
        return 0
    end
    self.chain = 0

    local throw=self:throwChoice(p,foe,dist)
    if throw~=0 then return throw end

    if attacking(o) and dist < 380 and p.y <= 0 then
        local token=(o.hitId or 0)..':'..o.state..':'..(o.moveId or '')
        local decision=self.blockDecision~=token
        if decision then self.blockDecision=token;self.blockRoll=self:rand()<lv.block end
        if self.blockFor > 0 or (decision and self.blockRoll) then
            self.blockFor = 10
            local low = o.move and o.move.level == 'low'
            local high = o.airMove ~= nil or (o.move and o.move.level == 'high')
            return away | ((low and not high) and B.D or 0)
        end
    end
    if self.blockFor > 0 then self.blockFor = self.blockFor - 1; if self.blockFor > 0 then return away end end

    if sim.tick<(self.thinkAt or 0) then return self.moveHold or 0 end
    self.thinkAt=sim.tick+lv.think;self.moveHold=0
    if sim.tick<(self.nextAttack or 0) then return 0 end

    if p.energy >= 100 and p.kit.burst and self:rand() < lv.burstUse * 0.08 then
        local bu = p.kit.burst
        if bu.style == 'rain' or dist * 1 < (bu.range or 600) * 0.7 then return self:edge(B.BU) end
    end

    if o and o.y > 60 * C and o.vy and dist < 330 and self:rand() < lv.antiAir * 0.25 then
        local sk = p.kit.skill
        if sk and sk.style == 'rising' and p.skillCd == 0 then return self:edge(B.SK) end
        return self:edge(B.HP)
    end

    if o and o.move and o.state == 'attack' and o.t > (o.move.startup + o.move.active) and dist < 240 then
        if self:rand() < lv.punish * 0.3 then return self:edge(B.LP) end
    end

    local r = self:rand()
    if dist > 520 then
        local sk = p.kit.skill
        if sk and (sk.style == 'projectile' or sk.style == 'zone' or sk.style == 'capture') and p.skillCd == 0 and r < 0.03 then return self:edge(B.SK) end
        if p.kit.weapon.ranged and r < 0.025 then return self:edge(B.HP) end
        if r < 0.02 then return self:edge(toward | B.DA) end
        if r < 0.02 + lv.jump then return toward | B.U end
        self.moveHold=toward;return toward
    elseif dist > 230 then
        local sk = p.kit.skill
        if sk and sk.style == 'rush' and p.skillCd == 0 and r < 0.02 * lv.aggro then return self:edge(B.SK) end
        if r < 0.05 * lv.aggro then return self:edge(toward | B.DA) end
        if r < 0.05 * lv.aggro + lv.jump then return toward | B.U end
        if r < 0.75 then self.moveHold=toward;return toward end
        if r < 0.85 then self.moveHold=away;return away end
        return 0
    else
        local gentle=p.key=='arlecchino' and self.level<=2
        if r < lv.aggro*(gentle and .60 or .48) then return self:edge(B.LP) end
        if r < lv.aggro*(gentle and .85 or .68) then return self:edge(B.D | B.LP) end
        if r < lv.aggro*(gentle and .97 or .88) then return self:edge(B.HP) end
        if r < lv.aggro then return self:edge(B.D | B.HP) end
        if r < lv.aggro+.10 then self.moveHold=away;return away end
        return 0
    end
end

function AI:edge(mask)
    if self.lastOut and self.lastOut & mask ~= 0 and self.lastOut == mask then
        self.lastOut = 0
        return 0
    end
    self.lastOut = mask
    if mask & (B.LP|B.HP|B.SK|B.BU|B.TH)~=0 then self.nextAttack=self.sim.tick+self.lv.attackGap end
    return mask
end

function AI:tick()
    local out=self:decide();self.lastOut=out;return out
end

return AI
end
