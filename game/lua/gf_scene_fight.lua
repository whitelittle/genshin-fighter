-- The fight: loads stage + both fighters over a few frames behind a curtain, then runs the
-- simulation at 60 Hz and turns its events into effects, sound, camera and announcements.
--
-- args: {chars = {key1, key2}, mode = 'arcade' | 'versus' | 'cpu' | 'training' | 'demo' | 'online',
--        cpu = {false|level, false|level}, stage = key, arcade = {...state for the ladder}}
-- online: the match session (gf_online / gf_net) owns the simulation; this scene feeds it the
-- local input each tick, re-binds the views after a rollback and plays each event once.
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

local S = {}
S.__index = S

local C = Sim.C

function S.new(app, args)
    local self = setmetatable({app = app, args = args, state = 'load', t = 0, shake = 0, shakeT = 0, zoomPunch = 0,
                               camX = 0, zoom = 1, slow = 0, banners = {}, paused = false, endT = 0}, S)
    local L = app.layers
    app:dropBackdrop()
    self.mode = args.mode or 'versus'
    self.tier = app.quality == 'lo' and 'lo' or 'hi'
    local chars = {Art.byKey[args.chars[1]], Art.byKey[args.chars[2]]}
    self.chars = chars
    self.stageKey = args.stage or Stage.order[1]
    local net = args.online and app.net
    if net and net.match then
        -- online: the session's state is the simulation; events come through onNetFrame
        self.online = net
        self.side = net.match.side
        self.sim = net.match.session.state
        self.seenEv, self.netEvents = {}, {}
        net.onFrame = function(state, f, resim) self:onNetFrame(state, f, resim) end
    else
        self.sim = Sim.new({chars = chars, rounds = args.rounds or app.settings.rounds, time = args.time or app.settings.time,
                            seed = args.seed or (math.floor(app.t * 1000) % 100000 + 7), training = self.mode == 'training',
                            infinite = args.infinite})
    end
    -- loading curtain
    self.curtain = G.layer(L.curtain)
    -- groups
    self.stage = Stage.new(app, L.back, self.mode == 'training' and 'training' or self.stageKey)
    self.worldG = G.group(L.world)
    self.lay = {shadow = G.group(self.worldG), ghost = G.group(self.worldG), body = G.group(self.worldG),
                proj = G.group(self.worldG), fx = G.group(self.worldG)}
    self.prep = {Art.prepare(chars[1].key, self.tier), Art.prepare(chars[2].key, self.tier)}
    self.loadStep = 0
    return self
end

------------------------------------------------------------------ loading
function S:loadTick()
    self.loadStep = self.loadStep + 1
    local app = self.app
    local done = true
    for _, j in ipairs(self.prep) do
        if not j:step(9000) then done = false end
    end
    if not self.stage:buildStep(160) then done = false end
    if done and not self.views then
        self.views = {FView.new(app, self.lay, self.sim.f[1], self.tier), FView.new(app, self.lay, self.sim.f[2], self.tier)}
        self.fx = FX.new(app, self.lay.fx, app.layers.top, 220, 30, 18)
        for _, v in ipairs(self.views) do v.fx = self.fx end
        self.projL = G.layer(self.lay.proj)
        self.hud = Hud.new(app, app.layers.hud, self.sim)
        self.annL = G.layer(app.layers.top)
        self:touchControls()
        self.cut = {L = G.layer(app.layers.top), bmp = G.bitmap(app.layers.top)}
        self.cut.bmp.node:on(false)
        self.warm = 0
        return false
    end
    if self.views then
        -- warm-up: write the first poses of both fighters before showing the fight
        self.warm = self.warm + 1
        for _, v in ipairs(self.views) do v:draw(900) end
        self:camera(true)
        if self.warm >= 4 then
            self:setupAI()
            self.state = 'run'
            self:curtainOpen()
            return true
        end
    end
    return false
end

-- phones (or the touch setting) get on-screen controls for player 1
function S:touchControls()
    local app = self.app
    local want = app.settings.touch == 'on' or (app.settings.touch == 'auto' and app.input:device() == 'touch')
    if not want or self.mode == 'demo' then return end
    if self.touch then self.touch:layout() return end
    self.hud.compact = true
    self.touch = require('gf_touch').new(app, app.layers.top, self.sim.f[self.side or 1], function() if not self.paused then self:openPause() end end)
end

function S:setupAI()
    local cpu = (not self.online) and self.args.cpu or {}
    self.ai = {}
    for i = 1, 2 do
        if cpu[i] then self.ai[i] = AI.new(self.sim, i, cpu[i], 97 + i * 31) end
    end
end

function S:curtainDraw(a)
    local app = self.app
    local L = self.curtain
    L:begin()
    if a > 0.01 then
        L:rect(0, 0, app.W + 40, app.H + 40, {6, 8, 16}, a)
        local c1, c2 = self.chars[1], self.chars[2]
        local k = self.loadStep
        local dots = ('.'):rep(1 + (k // 10) % 3)
        L:label('载入中' .. dots, 0, -app.H / 2 + 90, 400, 40, 26, UI.GOLD2, 'c', nil, a)
        -- spinning element diamond
        local ec = K.elementColor[c1.element]
        L:shape(G.RECT, 0, -app.H / 2 + 150, 30, 30, ec, a, k * 6)
        L:shape(G.RECT, 0, -app.H / 2 + 150, 30, 30, K.elementColor[c2.element], a * 0.7, -k * 6)
    end
    L:finish()
end

function S:curtainOpen() self.curtainA = 1 end

------------------------------------------------------------------ inputs
function S:inputs()
    local app = self.app
    local sim = self.sim
    local ins = {0, 0}
    for i = 1, 2 do
        if self.ai[i] then
            ins[i] = self.ai[i]:tick()
        else
            local pad = app.input:pad(i)
            ins[i] = pad.now or 0
            -- single human vs CPU: the controller / P2 keys also drive P1
            if i == 1 and self.ai[2] then ins[i] = ins[i] | (app.input:pad(2).now or 0) end
        end
    end
    if self.mode == 'training' then
        local d = self.dummy or 'stand'
        local p2 = sim.f[2]
        local away = (p2.foe.x > p2.x) and Sim.B.L or Sim.B.R
        if d == 'block' then ins[2] = away
        elseif d == 'crouch' then ins[2] = Sim.B.D
        elseif d == 'cblock' then ins[2] = away | Sim.B.D
        elseif d == 'jump' then ins[2] = (sim.tick % 60 < 2) and Sim.B.U or 0
        elseif d == 'cpu' then ins[2] = self.ai[2] and ins[2] or 0
        else ins[2] = 0 end
    end
    return ins[1], ins[2]
end

------------------------------------------------------------------ events
local REACT_COL = {vaporize = {255, 150, 80}, melt = {255, 170, 120}, overload = {255, 120, 200}, frozen = {170, 235, 255},
                   electro = {200, 140, 255}, superconduct = {180, 170, 255}, swirl = {120, 255, 220}, crystal = {255, 210, 90},
                   bloom = {120, 230, 120}, aggravate = {190, 120, 255}, burning = {255, 110, 60}}

-- online: every simulated frame reports its events; a rollback replays frames, and only
-- events not already shown for that frame are played (a predicted hit that did not happen
-- stays on screen briefly; that is the usual rollback trade-off)
local function evKey(e)
    return e.type .. ':' .. tostring(e.move or e.kind or '') .. ':' .. (e.p or 0) .. ':' .. (e.by or 0)
end

function S:onNetFrame(state, f, resim)
    local seen = self.seenEv
    local slot = seen[f]
    if not slot then slot = {}; seen[f] = slot; seen[f - 240] = nil end
    for _, e in ipairs(state.events) do
        local k = evKey(e)
        if not (resim and slot[k]) then
            slot[k] = true
            self.netEvents[#self.netEvents + 1] = e
        end
    end
end

-- after a rollback the session holds a new state table: point everything at it
function S:rebind(st)
    self.sim = st
    if self.views then for i, v in ipairs(self.views) do v.f = st.f[i] end end
    if self.hud then self.hud.sim = st end
    if self.touch then self.touch.f = st.f[self.side or 1] end
end

function S:events(list)
    local app, sim, fx = self.app, self.sim, self.fx
    local au = app.audio
    for _, e in ipairs(list or sim.events) do
        local ty = e.type
        if ty == 'hit' then
            local a, d = sim.f[e.by], sim.f[e.p]
            local x, y = e.x / C, e.y / C
            fx:hitSpark(x, y, e.element, e.heavy or e.kind == 'skill', a.face, e.kind)
            if e.kind ~= 'throw' and a.move and a.move.fx and e.kind ~= 'skill' and e.kind ~= 'burst' then
                -- no extra arc on hit (the swing already drew it)
            end
            self.views[e.p]:onHit(e)
            self.hud:onHit(e)
            fx:number(x, y + 60, e.dmg, e.element, e.heavy)
            self:addShake(e.shake or 3)
            if e.heavy or e.kind == 'burst' then self.zoomPunch = math.max(self.zoomPunch, e.kind == 'burst' and 0.06 or 0.035) end
            if e.kind == 'burst' then au:hit(e.element, 'boom')
            elseif e.kind == 'skill' then au:hit(e.element, 'elem')
            elseif a.weapon == 'claymore' or a.weapon == 'polearm' then au:play(e.heavy and au.ID.blunt or au.ID.blade)
            elseif a.weapon == 'catalyst' then au:hit(e.element, 'elem')
            else au:play(e.heavy and au.ID.punch[2] or au.ID.punch[1]) end
        elseif ty == 'block' then
            local d = sim.f[e.p]
            fx:blockSpark(e.x / C, e.y / C, -d.face, e.heavy)
            self.views[e.p]:onBlock()
            au:play(au.ID.guard)
            self:addShake(e.heavy and 3 or 1)
        elseif ty == 'armor' then
            fx:blockSpark(e.x / C, e.y / C, 0, true)
            fx:number(e.x / C, e.y / C + 60, '霸体', 'geo', true, '霸体')
            au:play(au.ID.shield)
        elseif ty == 'swing' then
            local p = sim.f[e.p]
            local m = p.airMove or p.move
            if m and m.fx then
                self.pendingArc = self.pendingArc or {}
                self.pendingArc[#self.pendingArc + 1] = {p = p, m = m, at = (m.startup or 5)}
            end
            au:swing(e.weapon, e.heavy)
        elseif ty == 'skill' then
            local p = sim.f[e.p]
            local ec = K.elementColor[p.element]
            fx:spawn(fx.world, {shape = G.RING, x = p.x / C, y = p.y / C + 160, w = 80, col = ec, a = 1, to = {s = 6, a = 0}, dur = 0.35})
            fx:spawn(fx.world, {shape = G.STAR4, x = p.x / C, y = p.y / C + 170, w = 140, col = {255, 255, 255}, a = 1, to = {s = 0.1, rot = 180, a = 0}, dur = 0.3})
            au:play(au.ID.ecast[p.element])
            self:announceSmall(e.p, p.char.skill, ec)
        elseif ty == 'skillActive' then
            local p = sim.f[e.p]
            self:skillFx(p, e)
        elseif ty == 'burst' then
            self:burstStart(e)
        elseif ty == 'burstActive' then
            self:burstHitFx(e)
        elseif ty == 'reaction' then
            local col = REACT_COL[e.r] or {255, 255, 255}
            fx:number(e.x / C, e.y / C + 90, 0, 'anemo', true, K.reactionName[e.r] .. '！')
            local tn = fx.text.txt[fx.text.i]
            tn:color(col[1], col[2], col[3], 255)
            fx:spawn(fx.world, {shape = G.RING, x = e.x / C, y = e.y / C, w = 120, col = col, a = 1, to = {s = 5, a = 0}, dur = 0.45})
            fx:spawn(fx.world, {shape = G.ELLIPSE, x = e.x / C, y = e.y / C, w = 160, col = col, a = 0.8, soft = 0.5, to = {s = 2.5, a = 0}, dur = 0.4})
            au:play(au.ID.eboom[sim.f[e.by].element])
            self:addShake(5)
        elseif ty == 'dot' then
            fx:number(e.x / C, e.y / C, e.dmg, sim.f[e.p].foe.element, false)
        elseif ty == 'shieldHit' then
            fx:spawn(fx.world, {shape = G.RING, x = e.x / C, y = e.y / C, w = 160, h = 220, col = {255, 210, 90}, a = 1, to = {s = 1.3, a = 0}, dur = 0.25})
        elseif ty == 'clash' then
            fx:hitSpark(e.x / C, e.y / C, 'geo', true, 1)
            au:play(au.ID.parry)
        elseif ty == 'throw' then
            au:play(au.ID.dash)
        elseif ty == 'dash' then
            local p = sim.f[e.p]
            fx:dust(p.x / C, 0, false)
            fx:wind(p.x / C, p.y / C, e.back and -p.face or p.face, p.element)
            au:play(au.ID.dash)
        elseif ty == 'jump' then
            local p = sim.f[e.p]
            fx:dust(p.x / C, 0, false)
            au:play(au.ID.jump)
        elseif ty == 'land' then
            fx:dust(e.x / C, 0, e.hard)
            if e.hard then self:addShake(4); au:play(au.ID.fall) else au:play(au.ID.land) end
        elseif ty == 'ko' then
            self:koFx(e)
        elseif ty == 'announce' then
            if e.what == 'round' then self:announceRound(e.round) else self:announceFight() end
        elseif ty == 'roundEnd' then
            self:roundEndFx(e)
        elseif ty == 'victoryPose' then
            if e.p then self:announceWinner(e.p) end
        elseif ty == 'matchEnd' then
            self.endT = 150
            self.winner = e.winner
        elseif ty == 'second' then
            if e.left <= 5 and e.left > 0 then au:play(au.ID.tick) end
        end
    end
end

function S:addShake(n)
    if not self.app.settings.shake then n = math.min(n, 2) end
    self.shake = math.max(self.shake, n)
end

-- arcs appear at the first active frame of the swing
function S:arcs()
    local list = self.pendingArc
    if not list then return end
    for i = #list, 1, -1 do
        local a = list[i]
        local p = a.p
        local m = p.airMove or p.move
        local t = p.airMove and (p.airT or 0) or p.t
        if m ~= a.m then table.remove(list, i)
        elseif t >= a.at then
            self.fx:slash(p.x / C, p.y / C, p.face, m.fx, p.element, p.kit.weapon.reach or 1)
            table.remove(list, i)
        end
    end
end

function S:skillFx(p, e)
    local fx = self.fx
    local ec = K.elementColor[p.element]
    local x, y = p.x / C, p.y / C
    if e.style == 'rising' then
        for i = 1, 6 do
            local ang = math.rad(60 * i)
            fx:spawn(fx.world, {shape = G.TRI, x = x + math.cos(ang) * 60, y = y + 40, w = 50, h = 160, rot = 60 * i - 90, col = ec, a = 0.9,
                                to = {y = y + 300, a = 0, s = 0.4}, dur = 0.4})
        end
        fx:spawn(fx.world, {shape = G.ELLIPSE, x = x, y = y + 20, w = 320, h = 80, col = ec, a = 0.8, soft = 0.4, to = {s = 1.8, a = 0}, dur = 0.45})
    elseif e.style == 'rush' then
        fx:wind(x, y, p.face, p.element)
        fx:spawn(fx.world, {shape = G.ELLIPSE, x = x + p.face * 120, y = y + 150, w = 360, h = 160, col = ec, a = 0.7, soft = 0.5,
                            to = {x = x + p.face * 520, a = 0}, dur = 0.3})
    elseif e.style == 'pillar' then
        fx:dust(x + p.face * 200, 0, true)
    end
end

------------------------------------------------------------------ bursts (cinematic)
function S:burstStart(e)
    local app, fx = self.app, self.fx
    local p = self.sim.f[e.p]
    local ec = K.elementColor[p.element]
    self.cine = {p = e.p, t = 0, ec = ec, name = p.char.burst, char = p.char}
    fx:flash(ec, 0.6, 0.25)
    fx:speedLines(ec, 22, 0.8)
    app.audio:play(app.audio.ID.ecircle[p.element])
    app.audio:play(app.audio.ID.shock)
    -- portrait cut-in
    local img = Art.portrait(p.char.key)
    local bmp = self.cut.bmp
    bmp:drawMany({{img = img, ox = 0, oy = 0, s = 1}})
    local side = (e.p == 1) and -1 or 1
    bmp.node:stop()
    bmp.node:pos(side * (app.W / 2 + 300), -40):scale(5.2, 5.2):on(true)
    bmp.node:front()
    bmp.node:tween({anchoredPositionX = side * (app.W / 2 - 330)}, 0.28, 'OutCubic')
    self.zoomPunch = 0.12
end

function S:cineDraw()
    local c = self.cine
    local L = self.cut.L
    L:begin()
    if c then
        local app = self.app
        c.t = c.t + 1
        local fz = self.sim.freeze
        local a = U.clamp(math.min(c.t / 6, fz / 8), 0, 1)
        if fz <= 0 then a = 0 end
        local side = (c.p == 1) and -1 or 1
        L:rect(0, 0, app.W + 40, app.H + 40, {4, 4, 12}, 0.72 * a)
        -- diagonal banner
        local k = U.ease.outCubic(U.clamp(c.t / 14, 0, 1))
        local bx = -side * (1 - k) * app.W
        L:rect(bx, -40, app.W * 1.6, 230, c.ec, 0.85 * a, -8 * side)
        L:rect(bx, -40, app.W * 1.6, 200, {10, 10, 24}, 0.75 * a, -8 * side)
        L:rect(bx, 40, app.W * 1.6, 6, {255, 255, 255}, 0.8 * a, -8 * side)
        L:rect(bx, -120, app.W * 1.6, 6, {255, 255, 255}, 0.8 * a, -8 * side)
        -- burst name
        local nx = -side * 140 + bx * 0.4
        L:label('元素爆发', nx, 30, 400, 40, 24, c.ec, 'c', {0, 0, 0}, a)
        L:label(c.name, nx, -40, 900, 110, 64, {255, 255, 255}, 'c', {c.ec[1] // 3, c.ec[2] // 3, c.ec[3] // 3}, a)
        L:label(c.char.name, nx, -100, 400, 40, 26, {255, 236, 190}, 'c', {0, 0, 0}, a)
        if fz <= 0 and c.t > 4 then
            self.cine = nil
            self.cut.bmp.node:stop()
            self.cut.bmp.node:on(false)
        end
    end
    L:finish()
end

function S:burstHitFx(e)
    local fx = self.fx
    local p = self.sim.f[e.p]
    local ec = K.elementColor[p.element]
    local x, y = p.x / C, p.y / C
    fx:flash({255, 255, 255}, 0.7, 0.2)
    self:addShake(14)
    if e.style == 'aoe' or e.style == 'rain' then
        for i = 1, 3 do
            fx:spawn(fx.world, {shape = G.RING, x = x, y = y + 160, w = 120, col = i == 2 and {255, 255, 255} or ec, a = 1,
                                to = {s = 9 + i * 2, a = 0}, dur = 0.5 + i * 0.12})
        end
        fx:spawn(fx.world, {shape = G.ELLIPSE, x = x, y = y + 160, w = 400, col = ec, a = 0.8, soft = 0.5, to = {s = 4, a = 0}, dur = 0.6})
        if e.style == 'rain' then
            local tx = p.foe.x / C
            for i = 1, 8 do
                local ox = (fx:rand() - 0.5) * 500
                fx:spawn(fx.world, {shape = G.RECT, x = tx + ox, y = 900, w = 30, h = 260, col = ec, a = 1, to = {y = 100, a = 0}, dur = 0.25 + i * 0.05, ease = 'InQuad'})
            end
        end
    elseif e.style == 'beam' then
        fx:spawn(fx.world, {shape = G.RECT, x = x + p.face * 600, y = y + 160, w = 1300, h = 160, col = ec, a = 0.95,
                            to = {sy = 0.05, a = 0}, dur = 0.7, ease = 'InQuad'})
        fx:spawn(fx.world, {shape = G.RECT, x = x + p.face * 600, y = y + 160, w = 1300, h = 50, col = {255, 255, 255}, a = 1,
                            to = {sy = 0.05, a = 0}, dur = 0.6, ease = 'InQuad'})
    elseif e.style == 'rush' then
        fx:speedLines(ec, 14, 0.4)
    end
end

------------------------------------------------------------------ announcements
function S:banner(text, sub, col, life, size, y)
    self.banners[#self.banners + 1] = {text = text, sub = sub, col = col or UI.GOLD2, t = 0, life = life or 70, size = size or 120, y = y or 60}
end

function S:announceRound(n)
    local CN = {'一', '二', '三', '四', '五', '六', '七', '八', '九'}
    local final = self.sim.f[1].wins == self.sim.winsNeeded - 1 and self.sim.f[2].wins == self.sim.winsNeeded - 1
    self:banner(final and '决胜局' or ('第' .. (CN[n] or n) .. '回合'), final and 'FINAL ROUND' or ('ROUND ' .. n), UI.GOLD2, 80, 104)
    self.app.audio:play(self.app.audio.ID.bell)
end

function S:announceFight()
    self:banner('开战！', 'FIGHT', {255, 120, 90}, 50, 150)
    self.fx:flash({255, 240, 210}, 0.35, 0.2)
    self.app.audio:play(self.app.audio.ID.okBig)
end

function S:announceSmall(p, text, col)
    self.smalls = self.smalls or {}
    self.smalls[p] = {text = text, col = col, t = 0}
end

function S:koFx(e)
    local fx, app = self.fx, self.app
    fx:flash({255, 255, 255}, 0.95, 0.4)
    fx:speedLines({255, 255, 255}, 26, 0.9)
    for i = 1, 3 do
        fx:spawn(fx.world, {shape = G.RING, x = e.x / C, y = e.y / C, w = 100, col = i == 2 and {255, 80, 80} or {255, 255, 255}, a = 1,
                            to = {s = 10 + i * 3, a = 0}, dur = 0.6 + i * 0.15})
    end
    self:addShake(18)
    self.zoomPunch = 0.14
    app.audio:play(app.audio.ID.eboom.pyro)
    app.audio:play(app.audio.ID.heart)
end

function S:roundEndFx(e)
    if e.reason == 'time' then self:banner('时间到', 'TIME UP', {255, 220, 140}, 90, 110)
    elseif e.reason == 'double' then self:banner('双败', 'DOUBLE K.O.', {255, 90, 90}, 90, 120)
    else self:banner('K.O.', e.perfect and 'PERFECT' or nil, {255, 70, 70}, 110, 170) end
end

function S:announceWinner(p)
    local f = self.sim.f[p]
    self:banner(f.char.name .. ' 胜', f.hp == f.maxhp and '完美胜利 · PERFECT' or 'WIN', K.elementColor[f.element], 100, 96)
end

function S:drawBanners()
    local L = self.annL
    L:begin()
    for i = #self.banners, 1, -1 do
        local b = self.banners[i]
        b.t = b.t + 1
        local t = b.t
        if t > b.life then table.remove(self.banners, i)
        else
            -- Genshin-style title card with a fighting-game punch: soft dark band, thin cream
            -- rules with diamonds, small caps sub line above, big text slamming in with an
            -- afterimage and a light sweep
            local W = self.app.W
            local inK = U.ease.outBack(U.clamp(t / 10, 0, 1))
            local lineK = U.ease.outCubic(U.clamp((t - 3) / 14, 0, 1))
            local outK = U.clamp((b.life - t) / 10, 0, 1)
            local a = math.min(U.clamp(t / 4, 0, 1), outK)
            local s = (1.9 - 0.9 * inK) * (1 + (1 - outK) * 0.25)
            local y = b.y
            local hs = b.size * 0.55
            L:shape(G.ELLIPSE, 0, y, W * 1.3, b.size * 2.6, {6, 8, 18}, 0.62 * a, 0, 0.5)
            L:shape(G.ELLIPSE, 0, y, W * 0.7, b.size * 1.4, b.col, 0.16 * a, 0, 0.5)
            -- light sweep
            local sw = U.clamp(t / 22, 0, 1)
            L:rect(-W * 0.6 + sw * W * 1.2, y, 90, b.size * 2.2, {255, 255, 255}, (1 - sw) * 0.35 * a, -14)
            -- rules + diamonds
            local lw = 980 * lineK
            local ty, by = y + hs + 50, y - hs - 22
            for _, ly in ipairs({ty, by}) do
                L:rect(0, ly, lw, 2, UI.CREAM, 0.85 * a)
                L:shape(G.RECT, -lw / 2 - 8, ly, 9, 9, UI.CREAM, a, 45)
                L:shape(G.RECT, lw / 2 + 8, ly, 9, 9, UI.CREAM, a, 45)
            end
            L:shape(G.RECT, 0, by, 16, 16, b.col, a * lineK, 45)
            L:shape(G.RECT, 0, by, 8, 8, UI.WHITE, a * lineK, 45)
            L:shape(G.STAR4, -lw / 2 - 30, ty, 26, 26, UI.WHITE, a * lineK, t * 6)
            L:shape(G.STAR4, lw / 2 + 30, by, 26, 26, UI.WHITE, a * lineK, -t * 6)
            -- afterimage then the text itself
            local ak = U.clamp(t / 16, 0, 1)
            local g = L:label(b.text, 0, y + 6, 1400, b.size * 1.4, b.size, UI.WHITE, 'c', nil, (1 - ak) * 0.55 * a)
            g:scale(g.sx * (1 + ak * 0.7), g.sy * (1 + ak * 0.7))
            local n = L:label(b.text, 0, y + 6, 1400, b.size * 1.4, b.size, b.col, 'c', U.mix(b.col, {12, 8, 20}, 0.82), a)
            n:scale(n.sx * s, n.sy * s)
            L:label(b.sub or '', 0, y + hs + 22, 800, 34, 24, UI.CREAM, 'c', {0, 0, 0, 180}, b.sub and a * lineK or 0)
        end
    end
    -- skill names under the casters
    if self.smalls then
        for p, s in pairs(self.smalls) do
            s.t = s.t + 1
            if s.t > 70 then self.smalls[p] = nil
            else
                local f = self.sim.f[p]
                local sx = (f.x / C - self.camX) * self.zoom
                local a = U.clamp(math.min(s.t / 5, (70 - s.t) / 10), 0, 1)
                L:label(s.text, sx, self.floorY + 360 * self.zoom, 420, 40, 26, s.col, 'c', {10, 6, 20}, a)
            end
        end
    end
    L:finish()
end

------------------------------------------------------------------ camera
function S:camera(snap)
    local app, sim = self.app, self.sim
    local a, b = sim.f[1], sim.f[2]
    local x1, x2 = a.x / C, b.x / C
    local mid = (x1 + x2) / 2
    local dist = math.abs(x2 - x1)
    local W = app.W
    local zoom = U.clamp((W - 520) / math.max(dist, 300), 0.78, 1.12)
    if self.cine then
        local p = sim.f[self.cine.p]
        mid = p.x / C
        zoom = 1.25
    end
    zoom = zoom + self.zoomPunch
    self.zoomPunch = self.zoomPunch * 0.85
    -- keep the view inside the stage
    local half = W / 2 / zoom
    local lim = Sim.WALL / C + 180
    mid = U.clamp(mid, -lim + half, lim - half)
    if half > lim then mid = 0 end
    if snap then self.camX, self.zoom = mid, zoom
    else
        self.camX = self.camX + (mid - self.camX) * 0.18
        self.zoom = self.zoom + (zoom - self.zoom) * 0.12
    end
    -- highest fighter: lift the camera a little
    local hy = math.max(a.y, b.y) / C
    local lift = U.clamp(hy - 220, 0, 260) * 0.45
    local sx, sy = 0, 0
    if self.shake > 0 then
        local s = self.shake
        sx = ((self.app.frame % 2 == 0) and 1 or -1) * s * 1.4
        sy = ((self.app.frame % 4 < 2) and 1 or -1) * s * 0.9
        self.shake = self.shake * 0.82
        if self.shake < 0.5 then self.shake = 0 end
    end
    self.floorY = -app.H / 2 + 150 - lift
    self.worldG:pos(-self.camX * self.zoom + sx, self.floorY + sy):scale(self.zoom, self.zoom)
    self.stage:camera(self.camX, self.zoom, self.floorY, sx, sy)
end

------------------------------------------------------------------ projectiles
function S:drawProj()
    local L = self.projL
    L:begin()
    local t = self.app.frame
    for _, pr in ipairs(self.sim.proj) do
        local x, y = pr.x / C, pr.y / C
        local ec = K.elementColor[pr.element] or {255, 255, 255}
        local st = pr.style
        local w, h = pr.w / C, pr.h / C
        local live = pr.t > pr.delay
        if pr.zone then
            -- telegraph during the delay, strike after
            if not live then
                local k = pr.t / math.max(1, pr.delay)
                L:shape(G.ELLIPSE, x, 6, w * (1.2 - 0.4 * k), 30, ec, 0.4 + 0.4 * k)
                L:shape(G.RING, x, 6, w * (1.6 - 0.8 * k), 44, ec, 0.8)
                if st == 'eye' then L:shape(G.ELLIPSE, x, 560, 120, 70, ec, 0.6 * k); L:shape(G.ELLIPSE, x, 560, 40, 40, {255, 255, 255}, k) end
                if st == 'sakura' then L:shape(G.TRI, x - 40, 60, 30, 120, {255, 170, 210}, 0.9) end
            else
                local k = (pr.t - pr.delay) / math.max(1, pr.life - pr.delay)
                local a = 1 - k
                if st == 'pillar' then
                    local hh = h * U.clamp((pr.t - pr.delay) / 5, 0, 1)
                    L:rect(x, hh / 2, w, hh, {170, 130, 70}, 1)
                    L:rect(x, hh / 2, w * 0.7, hh, {220, 180, 100}, 1)
                    L:rect(x, hh - 10, w * 1.1, 24, {255, 210, 120}, 1)
                else
                    L:rect(x, h / 2, w * 0.35 * a + 8, h, ec, 0.9 * a)
                    L:rect(x, h / 2, w * 0.12 * a + 4, h, {255, 255, 255}, a)
                    L:shape(G.ELLIPSE, x, 10, w * 1.4, 60, ec, 0.7 * a, 0, 0.4)
                end
            end
        else
            if st == 'arrow' then
                L:rect(x - pr.face * 30, y, w, 6, {255, 255, 255}, 1)
                L:rect(x - pr.face * 80, y, w * 1.4, 18, ec, 0.45)
                L:shape(G.TRI, x + pr.face * (w / 2), y, 22, 34, ec, 1, -90 * pr.face)
            elseif st == 'ushi' then
                L:shape(G.ELLIPSE, x, y, w, h * 0.8, {150, 80, 40}, 1)
                L:shape(G.ELLIPSE, x + pr.face * 40, y + 30, 70, 60, {180, 100, 50}, 1)
                L:shape(G.TRI, x + pr.face * 40 - 22, y + 70, 16, 34, {255, 240, 220}, 1, 20)
                L:shape(G.TRI, x + pr.face * 40 + 22, y + 70, 16, 34, {255, 240, 220}, 1, -20)
                L:shape(G.RING, x, y, w * 1.2, h, ec, 0.6)
            elseif st == 'torrent' then
                L:shape(G.ELLIPSE, x, y, w, h, ec, 0.8, 0, 0.3)
                L:shape(G.ELLIPSE, x, y, w * 0.8, h * 0.4, {220, 245, 255}, 0.9)
                L:shape(G.ELLIPSE, x - pr.face * w * 0.6, y, w * 0.8, h * 0.6, ec, 0.4, 0, 0.5)
            elseif st == 'shards' then
                for i = 0, 4 do
                    L:shape(G.TRI, x + (i - 2) * 30, y + ((i * 37) % 60) - 30, 26, 50, {255, 220, 120}, 1, -90 * pr.face + (i - 2) * 12)
                end
                L:shape(G.ELLIPSE, x, y, w, h * 0.6, ec, 0.4, 0, 0.5)
            elseif st == 'bubble' then
                L:shape(G.ELLIPSE, x, y + math.sin(t * 0.2) * 10, w, h, ec, 0.5, 0, 0.3)
                L:shape(G.RING, x, y + math.sin(t * 0.2) * 10, w, h, {220, 245, 255}, 0.9)
                L:shape(G.ELLIPSE, x - 18, y + 22 + math.sin(t * 0.2) * 10, 22, 16, {255, 255, 255}, 0.9)
            else
                L:shape(G.ELLIPSE, x, y, w * 1.5, h * 1.5, ec, 0.4, 0, 0.5)
                L:shape(G.ELLIPSE, x, y, w * 0.8, h * 0.8, ec, 0.95)
                L:shape(G.ELLIPSE, x, y, w * 0.4, h * 0.4, {255, 255, 255}, 1)
                L:shape(G.STAR4, x, y, w, h, {255, 255, 255}, 0.8, t * 8)
                L:shape(G.ELLIPSE, x - pr.face * w * 0.7, y, w, h * 0.5, ec, 0.35, 0, 0.5)
            end
        end
    end
    L:finish()
end

------------------------------------------------------------------ pause
function S:openPause()
    local app = self.app
    self.paused = true
    self.pauseT = 0
    app.input:clearUI()
    if self.touch then self.touch.L:clear() end
    app.audio:play(app.audio.ID.open)
    self.pauseL = self.pauseL or G.layer(app.layers.ui)
    local items = {
        {id = 'resume', label = '继续战斗'},
        {id = 'moves', label = '出招表'},
        {id = 'restart', label = '重新开始'},
    }
    if self.mode == 'training' then
        local dummies = {'stand', 'block', 'crouch', 'cblock', 'jump', 'cpu'}
        local dn = {stand = '站立', block = '站立防御', crouch = '蹲下', cblock = '蹲下防御', jump = '跳跃', cpu = 'CPU 对打'}
        self.dummy = self.dummy or 'stand'
        table.insert(items, 2, {id = 'dummy', label = '陪练', value = function() return dn[self.dummy] end,
            left = function() local i = 1 for k, v in ipairs(dummies) do if v == self.dummy then i = k end end self.dummy = dummies[(i - 2) % #dummies + 1]; self:trainingAI() end,
            right = function() local i = 1 for k, v in ipairs(dummies) do if v == self.dummy then i = k end end self.dummy = dummies[i % #dummies + 1]; self:trainingAI() end})
        table.insert(items, 3, {id = 'energy', label = '元素能量', value = function() return self.sim.opts.infinite and '无限' or '正常' end,
            left = function() self.sim.opts.infinite = not self.sim.opts.infinite end, right = function() self.sim.opts.infinite = not self.sim.opts.infinite end})
    end
    if self.online then
        items = {{id = 'resume', label = '继续战斗'}, {id = 'moves', label = '出招表'}, {id = 'leave', label = '离开对战'}}
    else
        items[#items + 1] = {id = 'select', label = '重新选择角色'}
        items[#items + 1] = {id = 'quit', label = '返回主菜单'}
    end
    local ec = UI.ECOL[self.sim.f[self.side or 1].element] or UI.GOLD
    self.pauseMenu = UI.menu(app, app.layers.ui, items, {x = -app.W / 2 + 380, y = app.H / 2 - 290, w = 520, h = 70, gap = 8, size = 32,
        numbers = true, accent = ec,
        onPick = function(id) self:pausePick(id) end, onBack = function() self:closePause() end})
end

function S:trainingAI()
    if self.dummy == 'cpu' then self.ai[2] = AI.new(self.sim, 2, 2, 51) else self.ai[2] = nil end
end

function S:closePause()
    self.paused = false
    if self.pauseMenu then self.pauseMenu:free(); self.pauseMenu = nil end
    if self.pauseL then self.pauseL:clear() end
    self.app.input:clearUI()
    self.showMoves = nil
    self:touchControls()
end

function S:pausePick(id)
    local app = self.app
    if id == 'resume' then self:closePause()
    elseif id == 'moves' then self.showMoves = not self.showMoves
    elseif id == 'leave' then
        Online.leaveMatch(self.online)
        self.online.onFrame = nil
        app:travel('online')
    elseif id == 'restart' then app:travel('fight', self.args)
    elseif id == 'select' then app:travel('select', {mode = self.mode == 'demo' and 'versus' or self.mode, cpu = self.args.cpu and self.args.cpu[2] and true or false})
    elseif id == 'quit' then app:travel('menu')
    end
end

function S:drawPause()
    local app = self.app
    local W, H = app.W, app.H
    local L = self.pauseL
    local f = self.sim.f[self.side or 1]
    local ec = UI.ECOL[f.element] or K.elementColor[f.element]
    self.pauseT = (self.pauseT or 0) + 1
    local k = U.ease.outCubic(U.clamp(self.pauseT / 12, 0, 1))
    L:begin()
    L:rect(0, 0, W + 40, H + 40, {4, 6, 14}, 0.55 * k)
    -- left slab with the menu
    UI.leftPanel(L, W, H, k, ec, k)
    UI.screenTitle(L, W, H, '暂停', UI.track('PAUSE') .. (self.online and '　·　联机对局不会暂停' or ''), k)
    -- move list: right slanted panel with hairline rows
    local ma = self.showMoves and k or 0
    local px = W / 2 - 420
    UI.slab(L, px + 40, 0, 900, H * 1.9, UI.NAVY, 0.92 * ma, -UI.SLANT)
    UI.slab(L, px + 40 - 450 / math.cos(math.rad(UI.SLANT)), 0, 3, H * 2, UI.GOLD, 0.7 * ma, -UI.SLANT)
    local rows = {
        {'移动', 'W A S D　·　W / 空格 跳跃　·　双击前冲刺'},
        {'防御', '按住后方向（蹲防：后下）'},
        {'轻攻击', 'J　连按三段　·　↓J 下段'},
        {'重攻击', 'K　挑空　·　↓K 扫腿'},
        {'元素战技', 'L　或 ↓↘→ + 攻击　「' .. f.char.skill .. '」'},
        {'元素爆发', 'I　能量满时　「' .. f.char.burst .. '」'},
        {'冲刺 / 投技', 'U 冲刺（后 + U 后撤）　·　O 或 →K 投'},
        {'基本连段', 'J → J → J → K → L → I'},
    }
    L:label(f.char.name, px + 120, H / 2 - 110, 560, 60, 44, UI.WHITE, 'l', nil, ma)
    L:label(UI.track('COMMAND LIST'), px + 120, H / 2 - 156, 560, 24, 14, UI.GOLD, 'l', nil, ma)
    UI.badge(L, f.element, px - 210, H / 2 - 112, 52, ma)
    for i, r in ipairs(rows) do
        local y = H / 2 - 220 - (i - 1) * 58
        L:label(r[1], px - 150, y, 180, 50, 20, ec, 'l', nil, ma)
        L:label(r[2], px + 170, y, 560, 50, 19, UI.WHITE, 'l', nil, ma)
        L:rect(px + 40, y - 27, 700, 1, UI.WHITE, 0.14 * ma)
    end
    L:finish()
    if self.pauseMenu then self.pauseMenu:draw(k) end
end

------------------------------------------------------------------ main
function S:tick()
    local app = self.app
    if self.state == 'load' then
        self:loadTick()
        return
    end
    local menu = app.input:menu()
    if self.paused then
        if self.showMoves then
            for _, a in ipairs(menu) do if a == 'back' or a == 'ok' or a == 'pause' then self.showMoves = nil end end
        elseif self.pauseMenu then
            for _, a in ipairs(menu) do if a == 'pause' then self:closePause() return end end
            self.pauseMenu:input(menu)
        end
        -- an online match cannot pause: the menu floats over the running fight
        if self.online and self.state == 'run' and self.online.match then self:netTick(true) end
        return
    end
    for _, a in ipairs(menu) do
        if a == 'pause' then self:openPause() return end
        if a == 'debug' then app.debug = not app.debug end
    end
    if self.online then
        if not self:netTick(false) then return end
    else
        local in1, in2 = self:inputs()
        self.sim:step(in1, in2)
        self:events()
    end
    local sim = self.sim
    -- stormy stage: lightning now and then
    if self.stage.L.lightning and sim.tick % 420 == 200 then
        if self.stage:thunder() then app.audio:play(app.audio.ID.ehit.electro) end
    end
    if self.endT > 0 then
        self.endT = self.endT - 1
        if self.endT == 0 then self:finish() end
    end
end

-- one online tick: local input in, frames out (with rollbacks), events once; false = left
function S:netTick(idle)
    local o = self.online
    local m = o.match
    if not m then return false end
    local app = self.app
    local mask = 0
    if not idle then mask = (app.input:pad(1).now or 0) | (app.input:pad(2).now or 0) end
    self.netEvents = {}
    Online.matchStep(o, mask)
    local st = m.session.state
    if st ~= self.sim then self:rebind(st) end
    if #self.netEvents > 0 then self:events(self.netEvents) end
    -- the other side vanished or the states differ: end the match here
    if not self.netEnd then
        local why
        if m.session.desync then why = '同步异常，对局中止'
        elseif Online.peerGone(o) or Online.hostLost(o) then why = '对手已断开连接' end
        if why then
            self.netEnd = why
            self:banner('对局结束', why, UI.CREAM, 150, 90)
            if self.endT <= 0 then self.endT = 160 end
        end
    end
    return true
end

function S:finish()
    local app = self.app
    local sim = self.sim
    if self.online then
        if self.netEnd and not self.winner then self.winner = self.side end
        Online.leaveMatch(self.online)
        self.online.onFrame = nil
    end
    local res = {winner = self.winner, chars = self.args.chars, mode = self.mode, args = self.args, side = self.side,
                 stats = {sim.f[1].stats, sim.f[2].stats}, wins = {sim.f[1].wins, sim.f[2].wins}}
    app:travel('result', res, K.elementColor[self.chars[self.winner or 1].element])
end

function S:draw()
    local app = self.app
    if self.state == 'load' then
        self:curtainDraw(1)
        return
    end
    if self.curtainA and self.curtainA > 0 then
        self.curtainA = self.curtainA - 0.08
        self:curtainDraw(math.max(0, self.curtainA))
    end
    local urgent = self.sim.phase ~= 'intro'
    for _, v in ipairs(self.views) do v:draw(urgent and 520 or 300) end
    self:arcs()
    self:camera(false)
    self:drawProj()
    self.hud:draw()
    if self.touch and not self.paused then self.touch:draw() end
    self.fx:update()
    self:cineDraw()
    self:drawBanners()
    if self.paused then self:drawPause() end
end

function S:exit()
    local app = self.app
    if self.views then for _, v in ipairs(self.views) do v:free() end end
    if self.hud then self.hud:free() end
    if self.touch then self.touch:free() end
    if self.projL then self.projL:free() end
    if self.annL then self.annL:free() end
    if self.cut then self.cut.L:free(); self.cut.bmp:free() end
    if self.pauseMenu then self.pauseMenu:free() end
    if self.pauseL then self.pauseL:free() end
    if self.fx then
        for _, n in ipairs(self.fx.world.img) do G.release(n) end
        for _, n in ipairs(self.fx.screen.img) do G.release(n) end
        for _, n in ipairs(self.fx.text.txt) do G.release(n) end
    end
    self.stage:free()
    self.curtain:free()
    for _, g in pairs(self.lay) do G.release(g) end
    G.release(self.worldG)
end

return S
