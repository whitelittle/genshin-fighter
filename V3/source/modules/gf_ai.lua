__loaders['gf_ai'] = function()
local K = require('gf_kits')

local AI = {}
AI.__index = AI

local B = {U = 1, D = 2, L = 4, R = 8, LP = 16, HP = 32, SK = 64, BU = 128, DA = 256, TH = 512}
local C = 100

local LEVELS = {
    {react = 26, block = 0.25, comboLen = 2, aggro = 0.35, antiAir = 0.15, punish = 0.2, burstUse = 0.4, jump = 0.006},
    {react = 16, block = 0.55, comboLen = 3, aggro = 0.5, antiAir = 0.45, punish = 0.5, burstUse = 0.7, jump = 0.008},
    {react = 10, block = 0.78, comboLen = 4, aggro = 0.6, antiAir = 0.7, punish = 0.8, burstUse = 0.9, jump = 0.01},
    {react = 6, block = 0.9, comboLen = 5, aggro = 0.7, antiAir = 0.85, punish = 0.95, burstUse = 1.0, jump = 0.01},
}

function AI.new(sim, id, level, seed)
    local self = setmetatable({sim = sim, id = id, lv = LEVELS[level] or LEVELS[2], seed = seed or (id * 7919 + 13),
                               plan = nil, planT = 0, hold = 0, press = 0, seen = {}, chain = 0, blockFor = 0}, AI)
    return self
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
                 airMove = foe.airMove}
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
    local chance=(foe.state=='block' or foe.state=='cblock') and 0.32 or 0.22
    if self:rand()>=chance then return 0 end
    local out=self:edge(B.TH)
    if out~=0 then self.throwReadyAt=sim.tick+480;self.throwAttempts=(self.throwAttempts or 0)+1 end
    return out
end

function AI:tick()
    local sim = self.sim
    local p = sim.f[self.id]
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
        if self.chain < lv.comboLen and p.t >= 2 then
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
        if self.blockFor > 0 or self:rand() < lv.block then
            self.blockFor = 10
            local low = o.move and o.move.level == 'low'
            local high = o.airMove ~= nil or (o.move and o.move.level == 'high')
            return away | ((low and not high) and B.D or 0)
        end
    end
    if self.blockFor > 0 then self.blockFor = self.blockFor - 1; if self.blockFor > 0 then return away end end

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
        return toward
    elseif dist > 230 then
        local sk = p.kit.skill
        if sk and sk.style == 'rush' and p.skillCd == 0 and r < 0.02 * lv.aggro then return self:edge(B.SK) end
        if r < 0.05 * lv.aggro then return self:edge(toward | B.DA) end
        if r < 0.05 * lv.aggro + lv.jump then return toward | B.U end
        if r < 0.75 then return toward end
        if r < 0.85 then return away end
        return 0
    else
        if r < 0.06 * lv.aggro then return self:edge(B.LP) end
        if r < 0.09 * lv.aggro then return self:edge(B.D | B.LP) end
        if r < 0.11 * lv.aggro then return self:edge(B.HP) end
        if r < 0.13 then return self:edge(B.D | B.HP) end
        if r < 0.2 then return away end
        return 0
    end
end

function AI:edge(mask)
    if self.lastOut and self.lastOut & mask ~= 0 and self.lastOut == mask then
        self.lastOut = 0
        return 0
    end
    self.lastOut = mask
    return mask
end

return AI
end
