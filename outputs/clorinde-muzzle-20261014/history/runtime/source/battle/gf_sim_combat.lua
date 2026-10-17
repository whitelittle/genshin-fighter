__loaders['gf_sim_combat']=function()
local K=require('gf_kits')
local floor,abs,max,min=math.floor,math.abs,math.max,math.min
return function(S,ctx)
local C=ctx.C
local GRAV=ctx.GRAV
local WALL=ctx.WALL
local B=ctx.B
local HIST=ctx.HIST
local fwdBit=ctx.fwdBit
local backBit=ctx.backBit
local holding=ctx.holding
local pressed=ctx.pressed
local grounded=ctx.grounded
local motion236=ctx.motion236
local boxOf=ctx.boxOf
local overlap=ctx.overlap
local moveTable=ctx.moveTable
function S:startMove(p, id)
    local m = moveTable(p, id)
    if not m then return false end
    if p.state == 'air' or (p.y > 0) then
        p.airMove = m
        p.airMoveId = id
        p.airT = 0
        p.connected = false
        p.hitCount = 0
        p.hitId = p.hitId + 1
        self:emit({type = 'swing', p = p.id, move = id, weapon = p.weapon, heavy = id == 'airHeavy'})
        return true
    end
    self:setState(p, 'attack', m, id)
    self:emit({type = 'swing', p = p.id, move = id, weapon = p.weapon, heavy = id:find('eavy') ~= nil})
    return true
end

function S:startSkill(p)
    local sk = p.kit.skill
    if not sk or p.skillCd > 0 then return false end
    p.skillCd = sk.cd
    p.coat = 100
    p.energy = min(100, p.energy + 8)
    self:setState(p, 'skill', sk, 'skill')
    p.airSkill = p.y > 0
    if p.key=='nahida' then p.castX=p.x;p.castY=p.y+190*C;p.castFace=p.face;p.captureHitT=nil;p.captureHitX=nil;p.captureHitY=nil end
    if sk.style == 'rush' and sk.armor then p.armor = true end
    self:emit({type = 'skill', p = p.id, style = sk.style, fx = sk.fx, element = p.element})
    return true
end

function S:startBurst(p)
    local bu = p.kit.burst
    if not bu or p.energy < 100 then return false end
    p.energy = 0
    p.coat = 160
    self:setState(p, 'burst', bu, 'burst')
    p.cinematicConfirmed=false
    p.invul = p.key=='raidenshogun' and 24 or 70
    self.freeze = p.key=='raidenshogun' and 0 or 56
    self.freezeBy = p.id
    p.stats.bursts = p.stats.bursts + 1
    self:emit({type = p.key=='raidenshogun' and 'burstAttempt' or 'burst', p = p.id, fx = bu.fx, element = p.element, style = bu.style})
    return true
end

function S:throwRange(p)
    return math.max(K.throw.range*C,math.floor(70*C*p.size)+math.floor(70*C*p.foe.size)+18*C)
end
function S:tryThrow(p)
    local d = p.foe
    local th = K.throw
    local dist = abs(d.x - p.x)
    local can = dist <= self:throwRange(p) and grounded(d) and d.state ~= 'down' and d.state ~= 'getup'
        and d.invul == 0 and (d.state ~= 'hit' and d.state ~= 'airhit') and d.state ~= 'thrown'
        and d.state ~= 'attack' and d.state ~= 'skill' and d.state ~= 'burst'
    if can then
        self:setState(p, 'throw', th, 'throw')
        self:setState(d, 'thrown')
        p.stats.throws=(p.stats.throws or 0)+1
        d.face=-p.face
        d.vx, d.vy = 0, 0
        self:emit({type = 'throw', p = p.id})
    else
        self:setState(p, 'attack', {pose = 'slash', startup = 4, active = 2, recovery = 22, damage = 0, box = {x = 0, y = 0, w = 0, h = 0}, whiff = true}, 'throwWhiff')
    end
end

------------------------------------------------------------------ hit resolution
-- holding away from the attacker
local function backBitTo(d, a)
    if a.x > d.x then return B.L elseif a.x < d.x then return B.R end
    return d.face > 0 and B.L or B.R
end

local function backDir(d, a)
    if a.x > d.x then return -1 end
    return 1
end
local HITSTOP = {light = 7, heavy = 11, skill = 11, burst = 14, throw = 14}

function S:hit(a, d, m, kind, opts)
    opts = opts or {}
    if (d.invul > 0 and not opts.ignoreInvul) or d.state == 'down' or d.state == 'getup' or d.state == 'ko' or d.state == 'thrown' then return false end
    local level = m.level or 'mid'
    local dirBack = backBitTo(d, a)
    -- blocking
    local canBlock = grounded(d) and (d.state == 'idle' or d.state == 'walk' or d.state == 'back' or d.state == 'crouch'
        or d.state == 'block' or d.state == 'cblock' or d.state == 'land') and kind ~= 'throw' and not opts.unblockable
    if canBlock and d.inNow & dirBack ~= 0 then
        local crouching = d.inNow & B.D ~= 0
        local ok = (level == 'mid') or (level == 'low' and crouching) or (level == 'high' and not crouching)
        if ok then
            self:setState(d, crouching and 'cblock' or 'block')
            d.stun = m.blockstun or 12
            d.vx = -d.face * floor((m.push or 8) * C * 0.9)
            if kind == 'skill' or kind == 'burst' then
                local chip = floor((m.damage or 0) * (kind == 'burst' and 0.22 or 0.1))
                d.hp = max(1, d.hp - chip)
            end
            d.energy = min(100, d.energy + 3)
            d.stats.blocks = d.stats.blocks + 1
            local hs = 6
            a.hitstop, d.hitstop = hs, hs
            a.connected = true
            self:emit({type = 'block', p = d.id, by = a.id, x = d.x, y = d.y + floor(170 * C * d.size), heavy = (m.damage or 0) >= 60, kind = kind})
            return 'block'
        end
    end
    -- armor (claymore heavy, some skills)
    if d.armor and (d.state == 'attack' or d.state == 'skill') and not d.armorUsed and kind ~= 'throw' and kind ~= 'burst' then
        d.armorUsed = true
        local dmg = floor((m.damage or 0) * 0.5)
        d.hp = max(1, d.hp - dmg)
        a.hitstop, d.hitstop = 8, 8
        a.connected = true
        self:emit({type = 'armor', p = d.id, x = d.x, y = d.y + floor(170 * C * d.size), dmg = dmg})
        return 'armor'
    end
    -- damage with combo scaling and reactions
    local inCombo = (d.state == 'hit' or d.state == 'airhit' or d.frozen > 0)
    if not inCombo then d.combo, d.comboDmg, d.juggle = 0, 0, 0 end
    d.combo = d.combo + 1
    local scale = 100
    if d.combo > 2 then scale = max(30, 100 - (d.combo - 2) * 9) end
    local dmg = (m.damage or 0) * scale // 100
    if d.vuln > 0 then dmg = dmg * 120 // 100 end
    local reaction
    local aura = d.coat > 0 and d.element or nil
    if aura and kind ~= 'light' and aura ~= a.element then
        local r = K.reaction[a.element] and K.reaction[a.element][aura]
        if r then reaction = r end
    end
    local launch = m.launch
    local knock = m.knockdown
    local push = m.push or 8
    if reaction then
        d.coat = 0
        a.stats.reactions = a.stats.reactions + 1
        if reaction == 'vaporize' or reaction == 'melt' then dmg = dmg * 3 // 2
        elseif reaction == 'aggravate' then dmg = dmg * 5 // 4
        elseif reaction == 'overload' then dmg = dmg + 60; launch = max(launch or 0, 26); knock = true; push = push + 10
        elseif reaction == 'frozen' then d.frozen = 70
        elseif reaction == 'electro' then d.dots[#d.dots + 1] = {by = a.id, every = 10, left = 3, dmg = 18, t = 0}
        elseif reaction == 'superconduct' then d.vuln = 240
        elseif reaction == 'swirl' then dmg = dmg + 45; push = push * 2
        elseif reaction == 'crystal' then a.shield = 120; a.shieldT = 360
        elseif reaction == 'bloom' then d.dots[#d.dots + 1] = {by = a.id, every = 24, left = 1, dmg = 75, t = 0}
        elseif reaction == 'burning' then d.dots[#d.dots + 1] = {by = a.id, every = 12, left = 6, dmg = 12, t = 0}
        end
        self:emit({type = 'reaction', p = d.id, by = a.id, r = reaction, x = d.x, y = d.y + floor(200 * C * d.size)})
    end
    if d.shield > 0 then
        local absorb = min(d.shield, dmg)
        d.shield = d.shield - absorb
        dmg = dmg - absorb
        if absorb > 0 then self:emit({type = 'shieldHit', p = d.id, x = d.x, y = d.y + floor(150 * C * d.size)}) end
    end
    d.hp = d.hp - dmg
    d.comboDmg = d.comboDmg + dmg
    a.stats.damage = a.stats.damage + dmg
    a.stats.hits = a.stats.hits + 1
    if d.combo > a.stats.maxCombo then a.stats.maxCombo = d.combo end
    a.energy = min(100, a.energy + (m.energy or 4))
    d.energy = min(100, d.energy + 2)
    a.connected = true
    a.hitCount = (a.hitCount or 0) + 1
    if d.frozen > 0 and reaction ~= 'frozen' then d.frozen = 0 end
    -- reaction state
    local hs = HITSTOP[kind] or 9
    if (m.damage or 0) >= 90 then hs = hs + 2 end
    local stun = max(8, (m.hitstun or 16) - max(0, d.combo - 3))
    local airborne = d.y > 0 or d.state == 'airhit'
    d.move, d.airMove = nil, nil
    d.armor = false
    if d.hp <= 0 then
        d.hp = 0
        self:setState(d, 'airhit')
        d.ko = true
        d.vy = 26 * C
        d.vx = -d.face * 9 * C
        d.face = -backDir(d, a)
        hs = 18
        self:emit({type = 'ko', p = d.id, by = a.id, x = d.x, y = d.y + floor(170 * C * d.size)})
    elseif d.frozen > 0 then
        self:setState(d, 'hit')
        d.stun = d.frozen
        d.vx = 0
    elseif launch or airborne or knock then
        self:setState(d, 'airhit')
        d.juggle = d.juggle + 1
        local vy = launch or (airborne and 10) or (knock and 12) or 10
        if d.juggle > 5 then vy = max(6, vy - (d.juggle - 5) * 4) end
        if m.spike and airborne then vy = -m.spike end
        d.vy = vy * C
        d.vx = a.face * floor(push * C * 0.55)
        if d.juggle > 8 then d.invul = 60 end
    else
        self:setState(d, 'hit')
        d.stun = stun
        d.vx = a.face * floor(push * C)
    end
    a.hitstop, d.hitstop = hs, hs
    self:emit({type = 'hit', p = d.id, by = a.id, kind = kind, move = a.moveId or kind, dmg = dmg, combo = d.combo,
               x = opts.x or d.x, y = opts.y or (d.y + floor(170 * C * d.size)), element = a.element,
               heavy = (m.damage or 0) >= 60, shake = m.shake or ((m.damage or 0) >= 60 and 6 or 2), reaction = reaction,
               weapon = a.weapon, fx = m.fx})
    return 'hit'
end


------------------------------------------------------------------ projectiles / zones

end
end
