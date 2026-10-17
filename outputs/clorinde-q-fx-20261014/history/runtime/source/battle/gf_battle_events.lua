__loaders['gf_battle_events']=function()
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
local REACT_COL = {vaporize = {255, 150, 80}, melt = {255, 170, 120}, overload = {255, 120, 200}, frozen = {170, 235, 255},
                   electro = {200, 140, 255}, superconduct = {180, 170, 255}, swirl = {120, 255, 220}, crystal = {255, 210, 90},
                   bloom = {120, 230, 120}, aggravate = {190, 120, 255}, burning = {255, 110, 60}}

-- Online effects and sound are dispatched from confirmed snapshots in netTick.

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
        if ty == 'skillFeedback' then
            self.hud:skillFeedback(e)
        elseif ty == 'hit' then
            local a, d = sim.f[e.by], sim.f[e.p]
            local x, y = e.x / C, e.y / C
            if a.key=='clorinde' and e.projectileShot then
                self.views[e.by].confirmedImpact={x=x,y=y,face=a.face,untilTime=app.t+.12}
            end
            fx:hitSpark(x, y, e.element, e.heavy or e.kind == 'skill', a.face, e.kind)
            if e.kind ~= 'throw' and a.move and a.move.fx and e.kind ~= 'skill' and e.kind ~= 'burst' then
                -- no extra arc on hit (the swing already drew it)
            end
            self.views[e.p]:onHit(e)
            self.hud:onHit(e)
            fx:number(x, y + 60, e.dmg, e.element, e.heavy or e.kind=='burst', nil, e.kind=='burst' and 1.3 or nil)
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
            if p.key~='nahida' and p.key~='furina' and p.key~='kamisatoayaka' then
            fx:spawn(fx.world, {shape = G.RING, x = p.x / C, y = p.y / C + 160, w = 80, col = ec, a = 1, to = {s = 6, a = 0}, dur = 0.35})
            fx:spawn(fx.world, {shape = G.STAR4, x = p.x / C, y = p.y / C + 170, w = 140, col = {255, 255, 255}, a = 1, to = {s = 0.1, rot = 180, a = 0}, dur = 0.3})
            end
            au:play(au.ID.ecast[p.element])
            self:announceSmall(e.p, p.char.skill, ec)
        elseif ty == 'skillActive' then
            local p = sim.f[e.p]
            self:skillFx(p, e)
        elseif ty == 'burst' then
            self:burstStart(e)
        elseif (ty == 'furinaCinematic' or ty == 'ayakaCinematic' or ty=='clorindeCinematic' or ty=='arlecchinoCinematic') then
            self.banners={};self.annL:clear()
            au:play(au.ID.ecircle[sim.f[e.p].element])
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
            G.requestImageRetirement()
            self:roundEndFx(e)
        elseif ty == 'victoryPose' then
            if e.p then self:announceWinner(e.p) end
        elseif ty == 'matchEnd' then
            G.requestImageRetirement()
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
    self.banners={};self.annL:clear()
    self.cine = {p = e.p, t = 0, ec = ec, name = p.char.burst, char = p.char}
    fx:flash(ec, 0.6, 0.25)
    fx:speedLines(ec, 22, 0.8)
    app.audio:play(app.audio.ID.ecircle[p.element])
    app.audio:play(app.audio.ID.shock)
    -- portrait cut-in
    local img = Art.portrait(p.char.key)
    local bmp = self.legacyCuts and self.legacyCuts[p.key] or self.cut.bmp
    self.cut.bmp=bmp
    -- Warmed portrait geometry is immutable; cinematic motion is one parent write.
    if bmp.key~=p.key..':legacyPortrait' then bmp:start(img,p.key..':legacyPortrait');bmp:step(160) end
    local side = (e.p == 1) and -1 or 1
    bmp.node:stop()
    bmp.node:pos(side * (app.W / 2 + 300), -40):scale(5.2, 5.2):on(true)
    bmp.node:front()
    bmp.node:tween({anchoredPositionX = side * (app.W / 2 - 330)}, 0.28, 'OutCubic')
    self.zoomPunch = p.key=='raidenshogun' and 0 or 0.12
end

function S:cineDraw()
    if require('gf_character_cinematic_view').cut(self) then return end
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
        app:cover(L,{4,4,12},0.72*a)
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
    -- Round / fight / KO / victory share one announcement slot.
    -- Replace immediately: animation age is render-frame based, simulation advances independently.
    self.annL:clear()
    self.banners = {}; self.bannerNext=nil
    self.banners[1] = {text = text, sub = sub, col = col or UI.GOLD2, t = 0, tick=self.sim.tick, life = life or 70, size = size or 120, y = y or 60}
end

function S:announceRound(n)
    self.smalls=nil;self.cine=nil;self.cut.L:clear();self.cut.bmp.node:on(false)
    local CN = {'一', '二', '三', '四', '五', '六', '七', '八', '九'}
    local final = self.sim.f[1].wins == self.sim.winsNeeded - 1 and self.sim.f[2].wins == self.sim.winsNeeded - 1
    self:banner(final and '决胜局' or ('第' .. (CN[n] or n) .. '回合'), final and 'FINAL ROUND' or ('ROUND ' .. n), UI.GOLD2, 40, 72)
    self.app.audio:play(self.app.audio.ID.bell)
end

function S:announceFight()
    self:banner('开战！', 'FIGHT', {255, 120, 90}, 20, 72)
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
    self.smalls=nil
    if e.reason == 'time' then self:banner('时间到', 'TIME UP', {255, 220, 140}, 90, 110)
    elseif e.reason == 'double' then self:banner('双败', 'DOUBLE K.O.', {255, 90, 90}, 90, 120)
    else self:banner('K.O.', e.perfect and 'PERFECT' or nil, {255, 70, 70}, 110, 170) end
end

function S:announceWinner(p)
    local f = self.sim.f[p]
    self:banner(f.char.name .. ' 胜', f.hp == f.maxhp and '完美胜利 · PERFECT' or 'WIN', K.elementColor[f.element], 100, 96, nil, true)
end

function S:drawBanners()
    if #self.banners==0 and self.bannerNext then
        self.banners={self.bannerNext};self.bannerNext=nil
    end
    local L = self.annL
    L:begin()
    for i = #self.banners, 1, -1 do
        local b = self.banners[i]
        b.t = math.max(0,self.sim.tick-(b.tick or self.sim.tick))
        local t = b.t
        if t >= b.life then table.remove(self.banners,i)
        else
            -- Fixed geometry and font size; only opacity changes.
            local a=math.min(1,(t+1)/4,(b.life-t)/4)
            L:rect(0,b.y,1080,170,{6,8,18},0.7*a)
            L:rect(0,b.y-84,1080,3,b.col,a)
            L:label(b.text,0,b.y+6,1400,220,b.size,b.col,'c',nil,a)
            L:label(b.sub or '',0,b.y-57,800,60,24,UI.CREAM,'c',nil,a)
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

end
end
