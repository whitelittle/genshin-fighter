__loaders['gf_hud'] = function()
-- Fight HUD: fighting-game structure dressed in Genshin's UI language.
--   structure (fighting games): thick health bars draining toward the portraits with a red
--   lag chunk and a slanted inner end, a big centre timer, win stars, a long super meter
--   (元素爆发) along the bottom, big combo numbers;
--   dress (Genshin, checked against in-game screens): translucent slate tracks, cream
--   hairlines, small gold stars / diamonds, element-coloured accents, round E / Q buttons with
--   a thin white rim and cream key-hint tags, cream capsule labels with dark-slate text.
-- Every frame issues the same calls (alpha 0 instead of skipping) so layer slots stay put.
local G = require('gf_gfx')
local Art = require('gf_art')
local K = require('gf_kits')
local UI = require('gf_ui')
local U = require('gf_util')

local H = {}
H.__index = H

local WHITE = {255, 255, 255}
local CREAM = {236, 229, 216}
local GREY = {216, 210, 196}
local SLATE = {30, 34, 50}
local SLATE2 = {52, 58, 80}
local SHADOW = {0, 0, 0}
local TEXT = {73, 83, 102}
local GOLD = {255, 214, 120}
local HP = {{255, 240, 150}, {255, 210, 74}, {242, 160, 40}}
local HP_LOW = {{255, 170, 140}, {244, 96, 70}, {214, 56, 44}}
local LAG = {232, 72, 58}

function H.new(app, parent, sim)
    local self = setmetatable({app = app, sim = sim}, H)
    self.root = G.group(parent)
    self.under = G.layer(self.root)
    self.faces = G.bitmap(self.root)
    self.L = G.layer(self.root)
    self.trail = {sim.f[1].hp, sim.f[2].hp}
    self.trailHold = {0, 0}
    self.combo = {{n = 0, t = 0, dmg = 0, punch = 0}, {n = 0, t = 0, dmg = 0, punch = 0}}
    self.lastHp = {sim.f[1].hp, sim.f[2].hp}
    self.shakeHp = {0, 0}
    return self
end

-- Desktop E/Q orbs are real click buttons, using the same virtual bits as touch.
function H:bindSkillButtons(index)
    local input = self.app.input
    local pad = input:pad(1)
    self.skillSide = index == 1 and -1 or 1
    self.skillGen = input.gen
    self.skillAreas = {}
    for _, bit in ipairs({64, 128}) do
        self.skillAreas[#self.skillAreas + 1] = input:area(0, 0, 1, 1, {
            click = function() pad.pulse = (pad.pulse or 0) | bit end,
        })
    end
end

function H:onHit(e)
    local c = self.combo[e.by]
    if c and e.combo >= 2 then
        c.n, c.t, c.punch = e.combo, 110, 9
        c.dmg = self.sim.f[e.p].comboDmg
    end
    self.shakeHp[e.p] = e.heavy and 10 or 5
end

local PR = 56                       -- portrait radius

function H:drawFaces()
    local W, Hh = self.app.W, self.app.H
    local list = {}
    for i, f in ipairs(self.sim.f) do
        local side = i == 1 and -1 or 1
        list[#list + 1] = {img = Art.round(f.key), ox = side * (W / 2 - 86), oy = Hh / 2 - 82 - PR, s = PR * 2 / 34}
    end
    self.faces:drawMany(list)
    self.faces.node:on(true)
    self.facesW = W
end

-- horizontal fill anchored at the outer end, three gradient bands
local function fill(L, side, outer, cy, w, h, cols, am)
    local cx = side * (outer - w / 2)
    local a = (w > 0.5) and (am or 1) or 0
    local bh = h / #cols
    for k, c in ipairs(cols) do
        L:rect(cx, cy + h / 2 - bh * (k - 0.5), w, bh + 0.5, c, a)
    end
end

local function keyTag(L, x, y, s, label, a)
    a = a or 1
    L:rect(x, y - 2, s + 4, s + 4, SHADOW, 0.35 * a)
    L:rect(x, y, s, s, CREAM, 0.96 * a)
    L:label(label, x, y, s, s, s * 0.72, TEXT, 'c', nil, a)
end

function H:draw()
    local app, sim = self.app, self.sim
    local W, Hh = app.W, app.H
    local top = Hh / 2
    local L, B = self.L, self.under
    if self.facesW ~= W then self:drawFaces() end
    L:begin()
    B:begin()
    local barY = top - 70
    local barH = 30
    local inner = 92
    local outer = W / 2 - 150
    local barW = outer - inner
    if self.skillAreas and self.skillGen == app.input.gen then
        local gw = math.min(460, W / 2 - 260)
        local gOuter, gy = W / 2 - 170, -Hh / 2 + 70
        app.input:moveArea(self.skillAreas[1], self.skillSide * (gOuter - gw - 66), gy - 8, 94, 130)
        app.input:moveArea(self.skillAreas[2], self.skillSide * (W / 2 - 104), gy, 126, 166)
    end

    for i, f in ipairs(sim.f) do
        local side = i == 1 and -1 or 1
        local ec = K.elementColor[f.element]
        local align = i == 1 and 'l' or 'r'
        local hpK = U.clamp(f.hp / f.maxhp, 0, 1)
        local trK = U.clamp(self.trail[i] / f.maxhp, 0, 1)
        local jit = 0
        if self.shakeHp[i] > 0 then
            jit = ((self.shakeHp[i] % 2 == 0) and 1 or -1) * self.shakeHp[i] * 0.4
            self.shakeHp[i] = self.shakeHp[i] - 1
        end
        local y = barY + jit
        local cxBar = side * (inner + barW / 2)
        -- shadow, cream frame, slate track, slanted inner cap
        B:shape(G.ELLIPSE, cxBar, y - 6, barW + 120, 90, SHADOW, 0.45, 0, 0.5)
        L:rect(cxBar, y, barW + 10, barH + 10, CREAM, 0.95)
        L:rect(cxBar, y, barW + 6, barH + 6, SLATE, 0.92)
        L:shape(G.TRI, side * (inner - 10), y, barH + 10, 26, CREAM, 0.95, side * 90)
        L:shape(G.TRI, side * (inner - 8), y, barH + 4, 20, SLATE, 0.92, side * 90)
        -- lag chunk then health
        local low = hpK <= 0.25
        local blink = low and (app.frame % 24 < 12)
        fill(L, side, outer, y, barW * trK, barH, {LAG}, 1)
        fill(L, side, outer, y, barW * hpK, barH, (low and blink) and HP_LOW or HP, 1)
        -- segment ticks + element line under the bar
        for k = 1, 4 do L:rect(side * (outer - barW * k / 5), y, 2, barH, SLATE, 0.45) end
        L:rect(cxBar, y - barH / 2 - 8, barW + 10, 4, ec, 0.95)
        -- crystal shield over the bar
        local sk = U.clamp(f.shield / 300, 0, 1)
        fill(L, side, outer, y + barH / 2 + 7, barW * sk, 5, {{255, 230, 140}}, sk > 0 and 1 or 0)
        -- portrait: element ring + cream ring + face (bitmap above this layer's under part)
        local px, py = side * (W / 2 - 86), top - 82
        B:shape(G.ELLIPSE, px, py - 4, PR * 2 + 30, PR * 2 + 30, SHADOW, 0.5, 0, 0.4)
        B:shape(G.ELLIPSE, px, py, PR * 2 + 16, PR * 2 + 16, ec, 1)
        B:shape(G.ELLIPSE, px, py, PR * 2 + 8, PR * 2 + 8, CREAM, 1)
        B:shape(G.ELLIPSE, px, py, PR * 2 + 2, PR * 2 + 2, SLATE, 1)
        -- name under the bar, title in grey
        local nx = side * (outer - 2)
        local tw = 520
        local tx = nx + (i == 1 and tw / 2 or -tw / 2)
        L:label(f.char.name, tx, y - 44, tw, 36, 28, WHITE, align, {0, 0, 0, 170})
        L:label((K.title[f.key] or ''), tx + side * -((utf8.len(f.char.name) or 3) * 30 + 12), y - 46, tw, 24, 16, GREY, align, {0, 0, 0, 140})
        -- win stars near the timer
        for r = 1, 3 do
            local on = r <= sim.winsNeeded
            local won = f.wins >= r
            local sx = side * (inner + 18 + (r - 1) * 34)
            L:shape(G.STAR4, sx, y - 44, 30, 30, SHADOW, on and 0.5 or 0)
            L:shape(G.STAR4, sx, y - 42, 28, 28, won and GOLD or SLATE2, on and 1 or 0, won and (app.t * 30) or 0)
        end

        -- super meter (元素爆发) along the bottom with the Q orb at its outer end; on phones
        -- (compact) it sits under the name instead, since the touch buttons own the bottom corners
        -- and already show E / Q readiness
        local cm = self.compact
        local gy = cm and (barY - 84) or (-Hh / 2 + 70)
        local gw = cm and math.min(360, barW * 0.5) or math.min(460, W / 2 - 260)
        local gOuter = cm and (outer + 4) or (W / 2 - 170)
        local gcx = side * (gOuter - gw / 2)
        local ek = U.clamp(f.energy / 100, 0, 1)
        local ready = f.energy >= 100
        local pulse = ready and (0.5 + 0.5 * math.sin(app.t * 8)) or 0
        local gh = cm and 12 or 18
        B:shape(G.ELLIPSE, gcx, gy - 4, gw + 120, 70, SHADOW, cm and 0 or 0.45, 0, 0.5)
        L:rect(gcx, gy, gw + 8, gh + 4, CREAM, 0.9)
        L:rect(gcx, gy, gw + 4, gh, SLATE, 0.92)
        L:shape(G.TRI, side * (gOuter - gw - 6), gy, gh + 4, 16, CREAM, 0.9, -side * 90)
        fill(L, side, gOuter, gy, gw * ek, gh - 4, {U.mix(ec, WHITE, 0.35), ec, U.mix(ec, SHADOW, 0.25)}, 1)
        fill(L, side, gOuter, gy, gw * ek, gh - 4, {WHITE}, ready and 0.35 * pulse or 0)
        for k = 1, 3 do L:rect(side * (gOuter - gw * k / 4), gy, 2, gh, SLATE, 0.6) end
        if cm then
            L:label('爆发就绪', side * (gOuter - gw - 70), gy, 120, 24, 16, ec, 'c', {0, 0, 0, 170}, ready and (0.6 + 0.4 * pulse) or 0)
        else
            L:label(ready and '元素爆发 · 就绪' or '元素爆发', side * (gOuter - gw / 2), gy + 26, gw, 26, 18,
                    ready and ec or GREY, align, {0, 0, 0, 160})
        end
        -- Q orb
        local qa = cm and 0 or 1
        local qx, qy = side * (W / 2 - 104), gy + 18
        B:shape(G.ELLIPSE, qx, qy, 170, 170, ec, ready and (0.3 + 0.35 * pulse) * qa or 0, 0, 0.5)
        L:shape(G.ELLIPSE, qx, qy - 4, 108, 108, SHADOW, 0.4 * qa)
        L:shape(G.ELLIPSE, qx, qy, 102, 102, WHITE, 0.9 * qa)
        L:shape(G.ELLIPSE, qx, qy, 96, 96, SLATE, 0.9 * qa)
        L:shape(G.ELLIPSE, qx, qy, 84 * math.sqrt(ek), 84 * math.sqrt(ek), ec, (ready and 0.95 or 0.7) * qa)
        UI.element(L, f.element, qx, qy, 54, (ready and 1 or 0.65) * qa, ready and WHITE or nil, ready and ec or nil)
        keyTag(L, qx, qy - 64, 24, 'Q', qa)
        -- E orb at the inner end of the meter
        local ea = cm and 0 or 1
        local ex, ey = side * (gOuter - gw - 66), gy + 10
        local cdLeft = f.kit.skill and f.skillCd or 0
        local up = cdLeft <= 0
        L:shape(G.ELLIPSE, ex, ey - 3, 76, 76, SHADOW, 0.4 * ea)
        L:shape(G.ELLIPSE, ex, ey, 72, 72, WHITE, 0.9 * ea)
        L:shape(G.ELLIPSE, ex, ey, 66, 66, up and ec or SLATE, 0.92 * ea)
        UI.element(L, f.element, ex, ey, 38, up and ea or 0, WHITE, ec)
        L:label(up and '' or ('%.1f'):format(cdLeft / 60), ex, ey, 70, 40, 24, WHITE, 'c', {0, 0, 0, 170}, ea)
        keyTag(L, ex, ey - 48, 20, 'E', ea)

        -- combo counter
        local c = self.combo[i]
        local ca = 0
        if c.t > 0 then c.t = c.t - 1; ca = U.clamp(c.t / 18, 0, 1) end
        local s = 1 + c.punch * 0.04
        if c.punch > 0 then c.punch = c.punch - 1 end
        local cx = side * (W / 2 - 260)
        L:rect(cx, 112, 280, 46, SLATE, 0.55 * ca, side * 6)
        L:rect(cx, 90, 300, 4, ec, ca, side * 6)
        local num = L:label(tostring(c.n), cx - side * 50, 150, 220, 110, 96, WHITE, 'c', U.mix(ec, SHADOW, 0.45), ca)
        num:scale(num.sx * s, num.sy * s)
        L:label('连击', cx + side * 70, 150, 120, 46, 36, ec, 'c', {0, 0, 0, 200}, ca)
        L:label('HITS', cx + side * 72, 120, 120, 26, 18, CREAM, 'c', {0, 0, 0, 160}, ca)
        L:label(('伤害 %d'):format(c.dmg), cx + side * 20, 64, 260, 28, 20, GOLD, 'c', {0, 0, 0, 160}, ca)
    end
    -- timer: slate diamond with a cream rim, big white numbers, cream round capsule
    local secs = math.max(0, math.ceil(sim.timer / 60))
    local tstr = (sim.opts.training or sim.timeLimit >= 999) and '∞' or tostring(secs)
    local low = (not sim.opts.training) and secs <= 10 and sim.phase == 'fight'
    local tc = low and ((app.frame % 30 < 15) and {255, 110, 96} or WHITE) or WHITE
    local ty = top - 74
    B:shape(G.ELLIPSE, 0, ty - 6, 200, 170, SHADOW, 0.5, 0, 0.5)
    L:shape(G.RECT, 0, ty, 112, 112, CREAM, 0.95, 45)
    L:shape(G.RECT, 0, ty, 104, 104, SLATE, 0.95, 45)
    L:shape(G.RECT, 0, ty, 88, 88, SLATE2, 0.6, 45)
    L:shape(G.RECT, 0, ty + 80, 12, 12, GOLD, 1, 45)
    L:label(tstr, 0, ty + 2, 130, 80, 64, tc, 'c', {0, 0, 0, 200})
    L:rect(0, ty - 92, 120, 26, CREAM, 0.95)
    L:shape(G.ELLIPSE, -60, ty - 92, 26, 26, CREAM, 0.95)
    L:shape(G.ELLIPSE, 60, ty - 92, 26, 26, CREAM, 0.95)
    L:label(('ROUND %d'):format(sim.round), 0, ty - 92, 140, 26, 17, TEXT, 'c')
    L:finish()
    B:finish()
    -- lag chunk drains after a short hold (stays while the combo continues)
    for i, f in ipairs(sim.f) do
        if f.hp < self.lastHp[i] then self.trailHold[i] = 36 end
        self.lastHp[i] = f.hp
        if self.trailHold[i] > 0 then
            if f.combo == 0 or self.trailHold[i] > 1 then self.trailHold[i] = self.trailHold[i] - 1 end
        elseif self.trail[i] > f.hp then
            self.trail[i] = math.max(f.hp, self.trail[i] - f.maxhp * 0.012)
        end
        if self.trail[i] < f.hp then self.trail[i] = f.hp end
    end
end

function H:free()
    self.L:free()
    self.under:free()
    self.faces:free()
    G.release(self.root)
end

return H
end
