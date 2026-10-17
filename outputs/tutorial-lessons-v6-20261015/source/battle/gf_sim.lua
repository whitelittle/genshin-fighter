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
    local w = K.characterWeapons and K.characterWeapons[char.key] or K.weapons[char.weapon] or K.weapons.sword
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
local ctx={C=C,GRAV=GRAV,WALL=WALL,B=B,HIST=HIST,fwdBit=fwdBit,backBit=backBit,holding=holding,pressed=pressed,grounded=grounded,motion236=motion236,boxOf=boxOf,overlap=overlap,moveTable=moveTable}
require('gf_sim_combat')(S,ctx)
require('gf_sim_projectiles')(S,ctx)
require('gf_sim_actions')(S,ctx)
require('gf_sim_fighter')(S,ctx)
require('gf_sim_physics')(S,C, GRAV, WALL)
require('gf_sim_flow')(S,C)
require('gf_sim_snapshot')(S,HIST)
require('gf_sim_furina')(S,ctx)
require('gf_sim_ayaka')(S,ctx)
require('gf_sim_clorinde')(S,ctx)
require('gf_sim_arlecchino')(S,ctx)
require('gf_sim_team')(S,newFighter,C)
require('gf_sim_feedback')(S,ctx)
S.C = C
S.WALL = WALL
return S
end
