__loaders['gf_sim'] = function()


-- Deterministic fight simulation (60 ticks/s). Pure Lua, no client API: the same inputs give
-- the same match on every machine (integer positions), which keeps rollback netcode possible.
--
-- Units: positions/velocities in centi-units (1/100 of a design unit); y = 0 is the floor,
-- y up. Inputs per tick: bit masks (gf_input.B) for both players, in absolute directions.
-- The view reads fighters and the per-tick `events` list; it never writes into the sim.
local K = require('gf_kits')

local S = {}
S.__index = S

local C = 100
local GRAV = 115
local WALL = 1100 * C
local B = {U = 1, D = 2, L = 4, R = 8, LP = 16, HP = 32, SK = 64, BU = 128, DA = 256, TH = 512}
S.B = B
local HIST = 30

local floor, abs, max, min = math.floor, math.abs, math.max, math.min
local function idiv(a, b) return floor(a / b) end

------------------------------------------------------------------ rng (deterministic)
local function rnd(s)
    s.seed = (s.seed * 1103515245 + 12345) & 0x7fffffff
    return s.seed
end
function S:rand(n) return rnd(self) % n end

------------------------------------------------------------------ setup
local function buildKit(char)
    local w = K.weapons[char.weapon] or K.weapons.sword
    local body = K.body[char.key] or K.body.default
    local kit = {weapon = w, body = body, skill = K.skills[char.key], burst = K.bursts[char.key]}
    return kit
end

local function newFighter(id, char, x, face)
    local kit = buildKit(char)
    local scale = (char.h or 335) / 335
    return {
        id = id, char = char, key = char.key, element = char.element, weapon = char.weapon, kit = kit,
        size = scale, x = x, y = 0, vx = 0, vy = 0, face = face,
        hp = kit.body.health, maxhp = kit.body.health, energy = 0, skillCd = 0,
        state = 'intro', t = 0, move = nil, moveId = nil, hitstop = 0, stun = 0,
        juggle = 0, combo = 0, comboDmg = 0, invul = 0, coat = 0, vuln = 0, shield = 0, shieldT = 0,
        frozen = 0, dots = {}, hist = {}, histN = 0, lastFwd = -100, lastFwdRel = -100,
        wins = 0, airMove = nil, hitId = 0, armorUsed = false, pose = 'idle', bufferedMove = nil,
        stats = {hits = 0, maxCombo = 0, damage = 0, bursts = 0, reactions = 0, blocks = 0},
    }
end

-- opts: {chars = {charA, charB}, rounds = 2 (wins needed), time = 99, seed, training = bool}
function S.new(opts)
    local self = setmetatable({}, S)
    self.opts = opts
    self.seed = (opts.seed or 12345) & 0x7fffffff
    self.f = {newFighter(1, opts.chars[1], -260 * C, 1), newFighter(2, opts.chars[2], 260 * C, -1)}
    self.f[1].foe, self.f[2].foe = self.f[2], self.f[1]
    self.proj = {}
    self.events = {}
    self.round = 1
    self.winsNeeded = opts.rounds or 2
    self.tick = 0
    self.freeze = 0          -- super freeze (bursts)
    self.freezeBy = nil
    self.timeLimit = opts.time or 99
    self:startRound(true)
    return self
end

function S:emit(e) self.events[#self.events + 1] = e end

function S:startRound(first)
    self.phase = 'intro'
    self.phaseT = 0
    self.timer = self.timeLimit * 60
    self.proj = {}
    self.freeze = 0
    for i, p in ipairs(self.f) do
        p.x = (i == 1 and -260 or 260) * C
        p.y, p.vx, p.vy = 0, 0, 0
        p.face = i == 1 and 1 or -1
        p.hp = p.maxhp
        p.ko = false  -- A previous round's K.O. must not disable this round's get-up.
        if first then p.energy = 0 end
        p.skillCd, p.stun, p.hitstop, p.invul, p.coat, p.vuln, p.shield, p.frozen = 0, 0, 0, 0, 0, 0, 0, 0
        p.dots = {}
        p.combo, p.comboDmg, p.juggle = 0, 0, 0
        p.move, p.airMove, p.bufferedMove = nil, nil, nil
        p.inNow,p.inPrev,p.inPressed,p.histN=0,0,0,0
        p.hist={};p.introHeld=0;p.releaseMask=0
        self:setState(p, 'intro')
    end
    self:emit({type = 'roundIntro', round = self.round, first = first})
end

------------------------------------------------------------------ helpers
function S:setState(p, st, move, moveId)
    if st~='burst' then p.cinematicConfirmed=false end
    p.state, p.t = st, 0
    p.move, p.moveId = move, moveId
    p.connected = false
    p.hitCount = 0
    p.armorUsed = false
    if move then
        p.hitId = p.hitId + 1
    end
end

local function fwdBit(p) return p.face > 0 and B.R or B.L end
local function backBit(p) return p.face > 0 and B.L or B.R end

local function holding(p, bit) return p.inNow & bit ~= 0 end
local function pressed(p, bit) return p.inPressed & bit ~= 0 end

local function grounded(p) return p.y <= 0 and p.vy <= 0 end

------------------------------------------------------------------ boxes
-- hurtbox (centi): x0, x1, y0, y1
local function motion236(p)
    local f = fwdBit(p)
    local stage = 0
    for i = HIST - 1, 0, -1 do
        local idx = (p.histN - i) % HIST
        local m = p.hist[idx] or 0
        if i <= 14 then
            if stage == 0 and m & B.D ~= 0 and m & f == 0 then stage = 1
            elseif stage == 1 and m & B.D ~= 0 and m & f ~= 0 then stage = 2
            elseif stage >= 1 and m & f ~= 0 and m & B.D == 0 then if stage == 2 then return true end end
        end
    end
    return false
end

function S:hurtbox(p)
    local s = p.size
    local w = floor(100 * C * s)
    local h = floor(290 * C * s)
    local st = p.state
    if st == 'crouch' or (p.move and p.move.pose == 'crouch') or st == 'cblock' then h = floor(190 * C * s) end
    if st == 'down' or st == 'getup' then return nil end
    local y0 = p.y
    if st == 'air' or st == 'airhit' or st == 'jumpsq' then
        y0 = p.y + floor(30 * C * s)
        h = floor(240 * C * s)
    end
    return p.x - w // 2, p.x + w // 2, y0, y0 + h
end

-- hitbox of a move box {x, y, w, h} (design units) for fighter p
local function boxOf(p, b, reach)
    reach = reach or 1
    local x0 = p.x + p.face * floor(b.x * C * reach)
    local x1 = p.x + p.face * floor((b.x + b.w) * C * reach)
    if x0 > x1 then x0, x1 = x1, x0 end
    local y0 = p.y + floor(b.y * C * p.size)
    return x0, x1, y0, y0 + floor(b.h * C * p.size)
end
S.boxOf = boxOf

local function overlap(ax0, ax1, ay0, ay1, bx0, bx1, by0, by1)
    return ax0 < bx1 and bx0 < ax1 and ay0 < by1 and by0 < ay1
end

------------------------------------------------------------------ actions
local function moveTable(p, id)
    if id == 'skill' or id == 'burst' or id == 'throw' then return nil end
    return p.kit.weapon[id]
end

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
            self:emit({type = 'block', p = d.id, by = a.id, x = d.x, y = d.y + floor(170 * C * d.size), heavy = (m.damage or 0) >= 60})
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
function S:spawnProj(p, spec, dmgMove, kind)
    local pr = {owner = p.id, x = p.x + p.face * floor((spec.x or 90) * C), y = p.y + floor((spec.y or 120) * C * p.size),
                vx = p.face * floor((spec.speed or 14) * C), vy = floor((spec.vy or 0) * C), w = floor((spec.w or 80) * C),
                h = floor((spec.h or 80) * C), life = spec.life or 60, t = 0, move = dmgMove, kind = kind or 'skill',
                style = spec.style or spec.fx, face = p.face, element = p.element, hits = spec.hits or 1, delay = spec.delay or 0,
                zone = spec.zone}
    self.proj[#self.proj + 1] = pr
    self:emit({type = 'proj', p = p.id, pr = pr})
    return pr
end

function S:updateProj()
    local list = self.proj
    for i = #list, 1, -1 do
        local pr = list[i]
        pr.t = pr.t + 1
        local alive = pr.t <= pr.life
        if pr.t > pr.delay then
            if not pr.zone then
                pr.x = pr.x + pr.vx
                pr.y = pr.y + pr.vy
                if pr.vy < 0 and pr.y <= 0 then pr.y = 0; pr.vy = 0 end
            end
            local owner = self.f[pr.owner]
            local d = owner.foe
            local hb = {self:hurtbox(d)}
            if hb[1] and alive and pr.hits > 0 then
                local x0, x1, y0, y1 = pr.x - pr.w // 2, pr.x + pr.w // 2, pr.y - (pr.zone and 0 or pr.h // 2), pr.y + (pr.zone and pr.h or pr.h // 2)
                if overlap(x0, x1, y0, y1, hb[1], hb[2], hb[3], hb[4]) then
                    local r = self:hit(owner, d, pr.move, pr.kind, {x = d.x, y = d.y + floor(170 * C * d.size)})
                    if r then
                        pr.hits = pr.hits - 1
                        if pr.hits <= 0 then alive = false end
                    end
                end
            end
            -- projectile clash
            if alive and not pr.zone then
                for j = #list, 1, -1 do
                    local o = list[j]
                    if o ~= pr and o.owner ~= pr.owner and not o.zone and o.dead ~= true then
                        if abs(o.x - pr.x) < (o.w + pr.w) // 2 and abs(o.y - pr.y) < (o.h + pr.h) // 2 then
                            o.dead, alive = true, false
                            self:emit({type = 'clash', x = (o.x + pr.x) // 2, y = (o.y + pr.y) // 2})
                        end
                    end
                end
            end
            if pr.x < -WALL - 300 * C or pr.x > WALL + 300 * C then alive = false end
        end
        if not alive or pr.dead then
            table.remove(list, i)
            self:emit({type = 'projEnd', pr = pr})
        end
    end
end

------------------------------------------------------------------ per-fighter logic
local function canAct(p)
    local st = p.state
    return st == 'idle' or st == 'walk' or st == 'back' or st == 'crouch' or st == 'land'
end

function S:faceFoe(p)
    if p.foe.x > p.x then p.face = 1 elseif p.foe.x < p.x then p.face = -1 end
end

function S:neutral(p)
    local nowIn, pr = p.inNow, p.inPressed
    local f, bk = fwdBit(p), backBit(p)
    -- burst > skill > throw > attacks > dash > jump > move
    if pr & B.BU ~= 0 and self:startBurst(p) then return end
    if (pr & B.SK ~= 0 or ((pr & (B.LP | B.HP)) ~= 0 and motion236(p))) and self:startSkill(p) then return end
    if pr & B.TH ~= 0 then self:tryThrow(p) return end
    if pr & B.HP ~= 0 then
        if nowIn & f ~= 0 and abs(p.foe.x - p.x) <= self:throwRange(p) and grounded(p.foe) and p.foe.state ~= 'airhit' then
            self:tryThrow(p) return
        end
        self:startMove(p, nowIn & B.D ~= 0 and 'crouchHeavy' or 'heavy') return
    end
    if pr & B.LP ~= 0 then self:startMove(p, nowIn & B.D ~= 0 and 'crouchLight' or 'light1') return end
    -- dashes: button, or double tap
    local dashF = (pr & B.DA ~= 0 and nowIn & bk == 0) or (pr & f ~= 0 and self.tick - p.lastFwd <= 12)
    local dashB = (pr & B.DA ~= 0 and nowIn & bk ~= 0) or (pr & bk ~= 0 and self.tick - (p.lastBack or -100) <= 12)
    if pr & f ~= 0 then p.lastFwd = self.tick end
    if pr & bk ~= 0 then p.lastBack = self.tick end
    if dashF then
        self:setState(p, 'dash'); p.vx = p.face * floor(p.kit.body.dash * C)
        self:emit({type = 'dash', p = p.id}) p.lastFwd = -100 return
    end
    if dashB then
        self:setState(p, 'backdash'); p.vx = -p.face * floor(p.kit.body.dash * C * 0.85); p.vy = 6 * C; p.invul = 8
        self:emit({type = 'dash', p = p.id, back = true}) p.lastBack = -100 return
    end
    if nowIn & B.U ~= 0 then
        self:setState(p, 'jumpsq')
        p.jumpDir = (nowIn & f ~= 0 and 1) or (nowIn & bk ~= 0 and -1) or 0
        return
    end
    if nowIn & B.D ~= 0 then
        if p.state ~= 'crouch' then self:setState(p, 'crouch') end
        p.vx = 0
        return
    end
    if nowIn & f ~= 0 then
        if p.state ~= 'walk' then self:setState(p, 'walk') end
        p.vx = p.face * floor(p.kit.body.walk * C)
    elseif nowIn & bk ~= 0 then
        if p.state ~= 'back' then self:setState(p, 'back') end
        p.vx = -p.face * floor(p.kit.body.back * C)
    else
        if p.state ~= 'idle' then self:setState(p, 'idle') end
        p.vx = 0
    end
end

-- cancel window: on hit/block, during active and the first 8 recovery frames (or hitstop)
function S:tryCancel(p, m)
    if not p.connected or not m.cancel then return false end
    local pr = p.inPressed
    if pr == 0 then return false end
    local want
    if pr & B.BU ~= 0 then want = 'burst'
    elseif pr & B.SK ~= 0 or ((pr & (B.LP | B.HP)) ~= 0 and motion236(p)) then want = 'skill'
    elseif pr & B.HP ~= 0 then want = (p.inNow & B.D ~= 0) and 'crouchHeavy' or (p.y > 0 and 'airHeavy' or 'heavy')
    elseif pr & B.LP ~= 0 then
        local id = p.moveId or p.airMoveId
        if id == 'light1' then want = 'light2' elseif id == 'light2' then want = 'light3'
        elseif id == 'crouchLight' then want = 'crouchLight' else want = 'light1' end
    end
    if not want then return false end
    local allowed = false
    for _, c in ipairs(m.cancel) do if c == want then allowed = true break end end
    if not allowed then return false end
    if want == 'burst' then return self:startBurst(p) end
    if want == 'skill' then return self:startSkill(p) end
    if p.y > 0 then
        if want ~= 'airHeavy' then return false end
    end
    return self:startMove(p, want)
end

function S:attackUpdate(p)
    local m = p.move
    local t = p.t
    local su, ac = m.startup, m.active
    if m.lunge and t < su then p.vx = p.face * floor(m.lunge * C / su) elseif t < su + ac then p.vx = p.vx * 6 // 10 else p.vx = 0 end
    if t >= su and t < su + ac and not m.whiff then
        if m.projectile then
            if t == su then self:spawnProj(p, m.projectile, m, 'heavy') end
        elseif not p.connected then
            local x0, x1, y0, y1 = boxOf(p, m.box, p.kit.weapon.reach)
            local d = p.foe
            local hx0, hx1, hy0, hy1 = self:hurtbox(d)
            if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
                local kind = (p.moveId and p.moveId:find('eavy')) and 'heavy' or 'light'
                self:hit(p, d, m, kind)
            end
        end
    end
    if t >= su then
        if self:tryCancel(p, m) then return end
    end
    if t >= su + ac + m.recovery then self:setState(p, 'idle') end
end

function S:airAttackUpdate(p)
    local m = p.airMove
    local t = p.airT
    p.airT = t + 1
    local su, ac = m.startup, m.active
    if t >= su and t < su + ac then
        if m.projectile then
            if t == su then self:spawnProj(p, m.projectile, m, 'heavy') end
        elseif not p.connected then
            local x0, x1, y0, y1 = boxOf(p, m.box, p.kit.weapon.reach)
            local hx0, hx1, hy0, hy1 = self:hurtbox(p.foe)
            if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
                self:hit(p, p.foe, m, p.airMoveId == 'airHeavy' and 'heavy' or 'light')
            end
        end
    end
    if t >= su and self:tryCancel(p, m) then return end
    if t >= su + ac + m.recovery then p.airMove = nil end
end

function S:skillUpdate(p)
    local sk = p.move
    local t = p.t
    local d = p.foe
    local st = sk.style
    if sk.invuln and t < sk.invuln then p.invul = max(p.invul, 1) end
    if t == sk.startup then
        self:emit({type = 'skillActive', p = p.id, fx = sk.fx, style = st, element = p.element})
        if st == 'projectile' then
            self:spawnProj(p, {x = 100, y = sk.y or 130, speed = sk.speed, w = sk.w, h = sk.h, life = sk.life, style = sk.fx}, sk, 'skill')
        elseif st == 'zone' then
            local pr = self:spawnProj(p, {x = 0, y = 0, speed = 0, w = sk.w, h = sk.h, life = sk.delay + 8, style = sk.fx, delay = sk.delay, zone = true}, sk, 'skill')
            pr.x = d.x
            pr.y = 0
        elseif st == 'pillar' then
            local pr = self:spawnProj(p, {x = sk.dist, y = 0, speed = 0, w = sk.w, h = sk.h, life = 30, style = sk.fx, delay = 2, zone = true}, sk, 'skill')
            pr.y = 0
            if sk.shield then p.shield = max(p.shield, sk.shield); p.shieldT = 420 end
        elseif st == 'rush' then
            p.vx = p.face * floor(sk.speed * C)
            p.rushHits = sk.hits or 1
        elseif st == 'rising' then
            p.vy = 20 * C
            p.vx = p.face * 3 * C
        end
    end
    if st=='capture' and t>=8 and t<=13 and not p.connected then
        local steps={0,0.10,0.26,0.48,0.74,1};local k=steps[t-7]
        local cx=(p.castX or p.x)+(p.castFace or p.face)*math.floor((110+540*k)*C)
        local cy=p.castY or 190*C
        local hx0,hx1,hy0,hy1=self:hurtbox(d)
        if hx0 and overlap(cx-sk.w*C/2,cx+sk.w*C/2,cy-sk.h*C/2,cy+sk.h*C/2,hx0,hx1,hy0,hy1) then
            local result=self:hit(p,d,{damage=sk.damage,hitstun=sk.hitstun,blockstun=16,push=9,level='mid',energy=8,shake=8},'skill')
            if result then p.captureHitT=t;p.captureHitX=d.x;p.captureHitY=cy end
        end
    end
    if st == 'rush' and t >= sk.startup and t < sk.startup + sk.dur then
        p.vx = p.face * floor(sk.speed * C) * (sk.startup + sk.dur - t) // sk.dur
        if p.rushHits > 0 and (not p.lastRushHit or t - p.lastRushHit >= 5) then
            local x0, x1, y0, y1 = boxOf(p, {x = -20, y = 40, w = sk.w, h = sk.h})
            local hx0, hx1, hy0, hy1 = self:hurtbox(d)
            if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
                local per = {damage = sk.damage // (sk.hits or 1), hitstun = sk.hitstun, blockstun = 14, push = 6,
                             launch = (p.rushHits == 1) and sk.launch or nil, level = 'mid', energy = 4, shake = 5}
                if self:hit(p, d, per, 'skill') then p.rushHits = p.rushHits - 1; p.lastRushHit = t end
            end
        end
    elseif st == 'rush' and t >= sk.startup + sk.dur then
        p.vx = p.vx * 7 // 10
    end
    if st == 'rising' and t >= sk.startup and t < sk.startup + 10 and not p.connected then
        local x0, x1, y0, y1 = boxOf(p, {x = -sk.w / 3, y = 0, w = sk.w, h = sk.h})
        local hx0, hx1, hy0, hy1 = self:hurtbox(d)
        if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
            self:hit(p, d, {damage = sk.damage, hitstun = sk.hitstun, blockstun = 16, push = 4, launch = sk.launch, level = 'mid', energy = 8, shake = 7}, 'skill')
        end
    end
    local total = sk.startup + (sk.dur or 0) + sk.recovery
    if st == 'rising' then
        if t > sk.startup and p.y <= 0 and p.vy <= 0 then self:setState(p, 'land'); p.landT = 8 return end
        if t >= total + 30 then self:setState(p, p.y > 0 and 'air' or 'idle') end
        return
    end
    if t >= total then
        p.armor = false
        self:setState(p, p.y > 0 and 'air' or 'idle')
    end
end

function S:burstUpdate(p)
    if p.key=='nahida' then
        local t,d,bu=p.t,p.foe,p.move
        local per={damage=bu.damage//bu.hits,hitstun=75,blockstun=18,push=3,level='mid',energy=0,shake=9,launch=13}
        if t==1 then self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style}) end
        if (t==2 or t==28 or t==54) and not d.ko then
            if math.abs(d.x-p.x)<=bu.range*C then
                per.launch=t==54 and 26 or 13;per.knockdown=t==54
                local result=self:hit(p,d,per,'burst',{unblockable=p.cinematicConfirmed==true,ignoreInvul=p.cinematicConfirmed==true})
                if result=='hit' then p.cinematicConfirmed=true;p.invul=100 end
                if t>2 then self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style}) end
            end
        end
        if p.cinematicConfirmed and not d.ko and t<54 then
            p.x=math.max(-WALL+400*C,math.min(WALL-400*C,p.x))
            d.x=p.x+p.face*330*C;d.y=math.max(d.y,110*C);d.vx=0
        end
        if t>=90 then p.cinematicConfirmed=false;self:setState(p,p.y>0 and 'air' or 'idle') end
        return
    end
    if p.key=='raidenshogun' then
        local t,d,bu=p.t,p.foe,p.move
        local per={damage=bu.damage//bu.hits,hitstun=80,blockstun=18,push=3,level='mid',energy=0,shake=12,launch=22}
        if t==2 then
            if math.abs(d.x-p.x)<=bu.range*C and d.y<420*C then
                local result=self:hit(p,d,per,'burst',{unblockable=false})
                if result=='hit' then
                    p.cinematicConfirmed=true;p.invul=160
                    -- Reserve space for the victim even at the stage wall.
                    p.x=math.max(-WALL+400*C,math.min(WALL-400*C,p.x))
                    d.x=p.x+p.face*330*C
                    d.y=math.max(d.y,130*C);d.vx=0
                    self.freeze=56;self.freezeBy=p.id
                    self:emit({type='burst',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
                    self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
                end
            end
        end
        if p.cinematicConfirmed then
            -- Hold the caught opponent in the cinematic until the final launch.
            if t<70 then d.x=p.x+p.face*330*C;d.y=math.max(d.y,130*C);d.vx=0 end
            if t==35 or t==70 then
                per.launch=t==70 and 28 or 18;per.knockdown=t==70
                self:hit(p,d,per,'burst',{unblockable=true,ignoreInvul=true})
                self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
            end
            if t>=100 then p.cinematicConfirmed=false;self:setState(p,p.y>0 and 'air' or 'idle') end
        elseif t>=32 then self:setState(p,p.y>0 and 'air' or 'idle') end
        return
    end
    local bu = p.move
    local t = p.t
    local d = p.foe
    -- the cinematic freeze runs first (self.freeze); t counts after it
    if t == 1 then self:emit({type = 'burstActive', p = p.id, fx = bu.fx, style = bu.style, element = p.element}) end
    local per = {damage = bu.damage // bu.hits, hitstun = 30, blockstun = 18, push = 5, level = 'mid', energy = 0, shake = 10}
    local window = 6 * bu.hits
    if bu.style == 'rush' and t < 22 then
        p.vx = p.face * 30 * C
    else
        p.vx = p.vx * 7 // 10
    end
    if t >= 2 and t < 2 + window and (t - 2) % 6 == 0 then
        local inRange
        if bu.style == 'rain' then inRange = true
        elseif bu.style == 'beam' then
            inRange = (d.x - p.x) * p.face > -40 * C and abs(d.x - p.x) <= bu.range * C and d.y < 420 * C
        elseif bu.style == 'rush' then
            inRange = abs(d.x - p.x) <= 260 * C
        else
            inRange = abs(d.x - p.x) <= bu.range * C
        end
        if inRange then
            local last = (t - 2) // 6 == bu.hits - 1
            per.launch = last and 24 or 9
            per.knockdown = last
            if bu.pull and not last then per.push = -6 end
            self:hit(p, d, per, 'burst', {unblockable = false})
        end
    end
    if t >= 2 + window + 26 then
        self:setState(p, p.y > 0 and 'air' or 'idle')
    end
end

function S:physics(p)
    -- velocity, gravity, floor, walls
    p.x = p.x + p.vx
    local air = p.y > 0 or p.vy > 0
    if air then
        p.vy = p.vy - GRAV
        p.y = p.y + p.vy
        if p.y <= 0 then
            p.y = 0
            p.vy = 0
            self:landed(p)
        end
    end
    if p.x < -WALL then p.x = -WALL; p.atWall = -1 elseif p.x > WALL then p.x = WALL; p.atWall = 1 else p.atWall = nil end
end

function S:landed(p)
    local st = p.state
    if st == 'airhit' then
        if p.ko then
            self:setState(p, 'down'); p.vx = 0
            self:emit({type = 'land', p = p.id, hard = true, x = p.x})
            return
        end
        self:setState(p, 'down')
        p.vx = p.vx // 3
        self:emit({type = 'land', p = p.id, hard = true, x = p.x})
    elseif st == 'air' or st == 'skill' then
        p.airMove = nil
        if st == 'skill' and p.move and p.move.style ~= 'rising' then return end
        self:setState(p, 'land'); p.landT = 4; p.vx = 0
        self:emit({type = 'land', p = p.id, x = p.x})
    elseif st == 'backdash' then
        p.vx = 0
    end
end

function S:fighterTick(p)
    p.t = p.t + 1
    if p.invul > 0 then p.invul = p.invul - 1 end
    if p.coat > 0 then p.coat = p.coat - 1 end
    if p.vuln > 0 then p.vuln = p.vuln - 1 end
    if p.skillCd > 0 then p.skillCd = p.skillCd - 1 end
    if p.shieldT > 0 then p.shieldT = p.shieldT - 1 if p.shieldT == 0 then p.shield = 0 end end
    -- damage over time from reactions
    for i = #p.dots, 1, -1 do
        local d = p.dots[i]
        d.t = d.t + 1
        if d.t % d.every == 0 then
            d.left = d.left - 1
            if p.hp > 0 then
                p.hp = max(p.state == 'ko' and 0 or 1, p.hp - d.dmg)
                self:emit({type = 'dot', p = p.id, dmg = d.dmg, x = p.x, y = p.y + floor(200 * C * p.size)})
            end
            if d.left <= 0 then table.remove(p.dots, i) end
        end
    end
    local st = p.state
    if p.frozen > 0 then p.frozen = p.frozen - 1 end
    if st == 'intro' or st == 'win' or st == 'lose' or st == 'thrown' then
        p.vx = 0
    elseif st == 'idle' or st == 'walk' or st == 'back' or st == 'crouch' then
        self:faceFoe(p)
        if self.phase == 'fight' then self:neutral(p) else p.vx = 0 end
    elseif st == 'land' then
        if p.t >= (p.landT or 4) then self:setState(p, 'idle') end
    elseif st == 'jumpsq' then
        if p.t >= 4 then
            self:setState(p, 'air')
            p.vy = 24 * C
            p.vx = (p.jumpDir or 0) * p.face * floor(5.6 * C)
            self:emit({type = 'jump', p = p.id})
        end
    elseif st == 'air' then
        if p.airMove then self:airAttackUpdate(p)
        elseif self.phase == 'fight' then
            local pr = p.inPressed
            if pr & B.BU ~= 0 and self:startBurst(p) then return end
            if pr & B.SK ~= 0 and self:startSkill(p) then return end
            if pr & B.HP ~= 0 then self:startMove(p, 'airHeavy')
            elseif pr & B.LP ~= 0 then self:startMove(p, 'airLight') end
        end
    elseif st == 'dash' then
        if p.t >= 14 then self:setState(p, 'idle') end
        p.vx = p.vx * 92 // 100
        if p.t >= 5 and self.phase == 'fight' and p.inPressed ~= 0 then
            -- dash cancel into attacks
            if p.inPressed & (B.LP | B.HP | B.SK | B.BU | B.TH) ~= 0 then self:setState(p, 'idle'); self:neutral(p) end
        end
    elseif st == 'backdash' then
        p.vx = p.vx * 90 // 100
        if p.t >= 18 then self:setState(p, 'idle') end
    elseif st == 'attack' then
        self:attackUpdate(p)
    elseif st == 'skill' then
        self:skillUpdate(p)
    elseif st == 'burst' then
        self:burstUpdate(p)
    elseif st == 'throw' then
        local d = p.foe
        p.vx = 0
        local assist=p.key=='nahida'
        local impact=assist and 34 or 30
        if p.t == impact then
            local dmg = K.throw.damage
            d.hp = max(0, d.hp - dmg)
            p.energy = min(100, p.energy + K.throw.energy)
            p.stats.damage = p.stats.damage + dmg
            self:setState(d, 'airhit')
            d.vy = (assist and 24 or -12) * C
            d.y=math.max(d.y,(assist and 20 or 40)*C)
            d.vx = p.face * (assist and 15 or 9) * C
            d.combo, d.comboDmg = 1, dmg
            if d.hp <= 0 then d.ko = true; self:emit({type = 'ko', p = d.id, by = p.id, x = d.x, y = d.y + 170 * C}) end
            p.hitstop, d.hitstop = 12, 12
            self:emit({type = 'hit', p = d.id, by = p.id, kind = 'throw', dmg = dmg, combo = 1, x = d.x, y = d.y + floor(170 * C * d.size),
                       element = p.element, heavy = true, shake = 9, weapon = p.weapon})
        elseif p.t < impact then
            if assist then
                d.t=p.t;d.face=-p.face;d.y=0
            else
            d.x = p.x + p.face * 120 * C
            d.t=p.t;d.face=-p.face
            local lift=p.t<12 and 0 or p.t<24 and (p.t-12)/12 or (30-p.t)/6
            d.y=math.max(0,lift)*160*C
            end
        end
        if p.t >= (assist and 76 or 50) then self:setState(p, 'idle') end
    elseif st == 'hit' or st == 'block' or st == 'cblock' then
        p.vx = p.vx * 85 // 100
        if p.atWall and p.foe and (st == 'hit' or st == 'block' or st == 'cblock') then
            -- pushback transfers to the attacker at the wall
            local a = p.foe
            if a.state == 'attack' or a.state == 'skill' then a.x = a.x - a.face * abs(p.vx) // 2 end
        end
        p.stun = p.stun - 1
        if p.stun <= 0 and p.frozen <= 0 then
            p.combo, p.comboDmg, p.juggle = 0, 0, 0
            self:setState(p, (p.inNow & B.D ~= 0) and 'crouch' or 'idle')
        end
    elseif st == 'airhit' then
        -- physics only
    elseif st == 'down' then
        p.vx = p.vx * 8 // 10
        if p.ko then
            if p.t == 1 then self:emit({type = 'downed', p = p.id}) end
        elseif p.t >= 38 then
            self:setState(p, 'getup')
            p.invul = 18
        end
    elseif st == 'getup' then
        if p.t >= 16 then
            p.combo, p.comboDmg, p.juggle = 0, 0, 0
            self:setState(p, 'idle')
            p.invul = 4
        end
    end
end

-- keep fighters apart (push boxes) and inside the camera span
function S:separate()
    local a, b = self.f[1], self.f[2]
    if a.state == 'thrown' or b.state == 'thrown' then return end
    local wa, wb = floor(70 * C * a.size), floor(70 * C * b.size)
    local need = wa + wb
    local dx = b.x - a.x
    local vertical = abs(a.y - b.y) < floor(220 * C)
    if vertical and abs(dx) < need then
        local push = (need - abs(dx)) // 2 + 1
        if dx == 0 then dx = a.face end
        if dx > 0 then a.x = a.x - push; b.x = b.x + push else a.x = a.x + push; b.x = b.x - push end
        for _, p in ipairs(self.f) do
            if p.x < -WALL then local o = -WALL - p.x; p.x = -WALL; p.foe.x = p.foe.x + o end
            if p.x > WALL then local o = p.x - WALL; p.x = WALL; p.foe.x = p.foe.x - o end
        end
    end
    -- max distance (camera span)
    local span = 1250 * C
    if abs(b.x - a.x) > span then
        local mid = (a.x + b.x) // 2
        if a.x < b.x then a.x, b.x = mid - span // 2, mid + span // 2 else a.x, b.x = mid + span // 2, mid - span // 2 end
    end
end

------------------------------------------------------------------ round flow
function S:roundOver(winner, reason)
    self.phase = 'ko'
    self.phaseT = 0
    self.koReason = reason
    self.roundWinner = winner
    if winner then self.f[winner].wins = self.f[winner].wins + 1 end
    self:emit({type = 'roundEnd', winner = winner, reason = reason,
               perfect = winner and self.f[winner].hp == self.f[winner].maxhp})
end

function S:flow()
    self.phaseT = self.phaseT + 1
    local a, b = self.f[1], self.f[2]
    if self.phase == 'intro' then
        if self.phaseT == 1 then self:emit({type = 'announce', what = 'round', round = self.round}) end
        if self.phaseT == 40 then self:emit({type='announce',what='fight'}) end
        if self.phaseT >= 60 then
            self.phase = 'fight'
            self.phaseT = 0
            for _, p in ipairs(self.f) do self:setState(p, 'idle') end
        end
    elseif self.phase == 'fight' then
        if not self.opts.training and self.timeLimit < 999 then
            self.timer = self.timer - 1
            if self.timer % 60 == 0 then self:emit({type = 'second', left = self.timer // 60}) end
        else
            self.timer = self.timeLimit * 60
        end
        if self.opts.training then
            for _, p in ipairs(self.f) do
                if p.hp <= 0 then p.hp = p.maxhp; p.ko = false end
                if p.state == 'idle' and p.combo == 0 and p.hp < p.maxhp and p.t > 60 then p.hp = min(p.maxhp, p.hp + 20) end
                if self.opts.infinite then p.energy = 100 end
            end
            return
        end
        local ka, kb = a.hp <= 0, b.hp <= 0
        if ka or kb then
            local w
            if not (ka and kb) then w = ka and 2 or 1 end   -- double K.O.: nobody wins the round
            self:roundOver(w, (ka and kb) and 'double' or 'ko')
        elseif self.timer <= 0 then
            local w
            if a.hp * b.maxhp > b.hp * a.maxhp then w = 1 elseif b.hp * a.maxhp > a.hp * b.maxhp then w = 2 end
            self:roundOver(w, 'time')
        end
    elseif self.phase == 'ko' then
        -- wait for the loser to land, then victory pose
        if self.phaseT == 150 then
            local w = self.roundWinner
            for _, p in ipairs(self.f) do
                if w and p.id == w and p.state ~= 'airhit' and p.state ~= 'down' then self:setState(p, 'win'); p.vx = 0 end
            end
            self:emit({type = 'victoryPose', p = w})
        end
        if self.phaseT >= 260 then
            local w = self.roundWinner
            if (w and self.f[w].wins >= self.winsNeeded) or self.round >= 9 then
                -- round cap (draws): the side with more round wins takes the match
                if not (w and self.f[w].wins >= self.winsNeeded) then
                    local wa, wb = self.f[1].wins, self.f[2].wins
                    w = wa > wb and 1 or (wb > wa and 2 or nil)
                end
                self.phase = 'over'
                self.phaseT = 0
                self.matchWinner = w
                self:emit({type = 'matchEnd', winner = w})
            else
                self.round = self.round + 1
                self:startRound(false)
            end
        end
    end
end

------------------------------------------------------------------ main tick
-- in1, in2: input masks (absolute directions) for this tick
function S:step(in1, in2)
    self.events = {}
    self.tick = self.tick + 1
    local ins = {in1 or 0, in2 or 0}
    if self.phase=='intro' then
        for i,p in ipairs(self.f) do
            p.introHeld=ins[i]
            p.releaseMask=ins[i] & 1008 -- Attack keys held at start must be released.
            p.inNow,p.inPrev,p.inPressed=0,0,0
            p.vx,p.vy=0,0
        end
        self:flow()
        return -- No fighter, physics, projectile or collision updates under banners.
    end
    for i, p in ipairs(self.f) do
        local m = ins[i]
        if self.phase ~= 'fight' then m = 0 end
        p.releaseMask=(p.releaseMask or 0) & m
        m=m & ~p.releaseMask
        p.inPressed = m & ~(p.inPrev or 0)
        p.inNow = m
        p.inPrev = m
        p.histN = p.histN + 1
        -- store directions relative to facing is done at parse time; keep raw
        p.hist[p.histN % HIST] = m
    end
    -- super freeze: only the caster's cinematic runs
    if self.freeze > 0 then
        self.freeze = self.freeze - 1
        self:emit({type = 'freeze', left = self.freeze, by = self.freezeBy})
        return
    end
    -- KO slow motion: two of three ticks skip physics
    if self.phase == 'ko' and self.phaseT < 90 and self.phaseT % 3 ~= 0 then
        self.phaseT = self.phaseT + 1
        return
    end
    for _, p in ipairs(self.f) do
        if p.hitstop > 0 then
            p.hitstop = p.hitstop - 1
            -- buffer: allow cancels to register during hitstop
            if p.inPressed ~= 0 and p.state == 'attack' and p.move then self:tryCancel(p, p.move) end
        else
            self:fighterTick(p)
        end
    end
    for _, p in ipairs(self.f) do
        if p.hitstop <= 0 then self:physics(p) end
    end
    self:updateProj()
    self:separate()
    self:flow()
end

-- compact state hash (tests / desync detection)
------------------------------------------------------------------ snapshots (rollback)
-- Copy of the whole match state. Move / kit / char tables are shared: the sim never writes
-- into them. Mutable sub-tables (history, dots, stats, projectiles) are copied.
local function copyList(src)
    local out = {}
    for i = 1, #src do
        local e = src[i]
        local c = {}
        for k, v in pairs(e) do c[k] = v end
        out[i] = c
    end
    return out
end

local function copyFighter(p)
    local c = {}
    for k, v in pairs(p) do c[k] = v end
    local h = {}
    for k = 0, HIST - 1 do h[k] = p.hist[k] end
    c.hist = h
    c.dots = copyList(p.dots)
    local st = {}
    for k, v in pairs(p.stats) do st[k] = v end
    c.stats = st
    return c
end

function S.copy(src)
    local self = setmetatable({}, S)
    for k, v in pairs(src) do self[k] = v end
    local a, b = copyFighter(src.f[1]), copyFighter(src.f[2])
    a.foe, b.foe = b, a
    self.f = {a, b}
    self.proj = copyList(src.proj)
    self.events = {}
    return self
end
S.snapshot = S.copy

function S:hash()
    local h = self.tick
    for _, p in ipairs(self.f) do
        h = (h * 31 + p.x) & 0x7fffffff
        h = (h * 31 + p.y) & 0x7fffffff
        h = (h * 31 + p.hp) & 0x7fffffff
        h = (h * 31 + p.energy) & 0x7fffffff
        h = (h * 31 + #p.state) & 0x7fffffff
        h = (h * 31 + p.vx + p.vy * 7) & 0x7fffffff
        h = (h * 31 + p.t + p.stun * 3 + p.combo * 5 + p.wins * 11) & 0x7fffffff
    end
    h = (h * 31 + #self.proj + self.seed) & 0x7fffffff
    return h
end

S.C = C
S.WALL = WALL
return S
end
