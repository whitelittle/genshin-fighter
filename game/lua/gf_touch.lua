-- Touch controls for phones, laid out like Genshin's mobile combat buttons: a floating stick
-- on the left half, an arc of round buttons on the right (轻 big, 重 / 技 / 爆 / 冲 / 跳 around
-- it) and a pause button. Each control is its own pooled preset button, so the stick and a
-- button can be held at the same time (each button only hears its own pointer).
local G = require('gf_gfx')
local K = require('gf_kits')
local U = require('gf_util')

local T = {}
T.__index = T

local B = {U = 1, D = 2, L = 4, R = 8, LP = 16, HP = 32, SK = 64, BU = 128, DA = 256}
local WHITE, SLATE, CREAM = {255, 255, 255}, {30, 34, 50}, {236, 229, 216}

function T.new(app, parent, fighter, onPause)
    local self = setmetatable({app = app, f = fighter, held = {}, stick = {on = false, ox = 0, oy = 0, x = 0, y = 0}, onPause = onPause}, T)
    self.L = G.layer(parent)
    self:layout()
    return self
end

function T:layout()
    local app = self.app
    local W, H = app.W, app.H
    -- 轻 is the big thumb button; the rest sit on an arc around it (angles in degrees)
    local rx, ry = W / 2 - 200, -H / 2 + 210
    local function at(deg, R) local r = math.rad(deg) return rx + math.cos(r) * R, ry + math.sin(r) * R end
    local hx, hy = at(205, 175)
    local sx, sy = at(158, 175)
    local bx, by = at(112, 178)
    local dx, dy = at(68, 172)
    local jx, jy = at(24, 142)
    self.buttons = {
        {id = 'LP', bit = B.LP, label = '轻', x = rx, y = ry, r = 80},
        {id = 'HP', bit = B.HP, label = '重', x = hx, y = hy, r = 54},
        {id = 'SK', bit = B.SK, label = '技', x = sx, y = sy, r = 54},
        {id = 'BU', bit = B.BU, label = '爆', x = bx, y = by, r = 58},
        {id = 'DA', bit = B.DA, label = '冲', x = dx, y = dy, r = 44},
        {id = 'UP', bit = B.U, label = '跳', x = jx, y = jy, r = 44},
    }
    local inp = app.input
    local pad = inp:pad(1)
    for _, b in ipairs(self.buttons) do
        local btn = b
        inp:area(b.x, b.y, b.r * 2.2, b.r * 2.2, {
            down = function() pad.touch = pad.touch | btn.bit; self.held[btn.id] = 6 end,
            up = function() pad.touch = pad.touch & ~btn.bit end,
        })
    end
    -- stick: the whole lower-left quarter
    self.stickArea = {x = -W / 4 - 40, y = -H / 4 + 40, w = W / 2 - 80, h = H / 2 + 80}
    local st = self.stick
    local function dirs(x, y)
        local dx, dy = x - st.ox, y - st.oy
        st.x, st.y = dx, dy
        local m = 0
        if dx > 28 then m = m | B.R elseif dx < -28 then m = m | B.L end
        if dy > 46 then m = m | B.U elseif dy < -36 then m = m | B.D end
        pad.touch = (pad.touch & ~15) | m
    end
    inp:area(self.stickArea.x, self.stickArea.y, self.stickArea.w, self.stickArea.h, {
        down = function(x, y) st.on = true; st.ox, st.oy = x, y; dirs(x, y) end,
        drag = function(x, y) dirs(x, y) end,
        up = function() st.on = false; st.x, st.y = 0, 0; pad.touch = pad.touch & ~15 end,
    })
    inp:area(0, H / 2 - 222, 90, 70, {click = function() if self.onPause then self.onPause() end end})
end

function T:draw()
    local app = self.app
    local L = self.L
    local f = self.f
    local ec = K.elementColor[f.element]
    L:begin()
    for _, b in ipairs(self.buttons) do
        local held = (app.input:pad(1).touch & b.bit) ~= 0
        local ready, fillK, txt = true, 0, nil
        if b.id == 'BU' then
            ready = f.energy >= 100
            fillK = U.clamp(f.energy / 100, 0, 1)
        elseif b.id == 'SK' then
            ready = f.skillCd <= 0
            fillK = ready and 1 or 0
            if not ready then txt = ('%.1f'):format(f.skillCd / 60) end
        end
        local elem = b.id == 'BU' or b.id == 'SK'
        local s = held and 0.9 or 1
        local d = b.r * 2 * s
        L:shape(G.ELLIPSE, b.x, b.y - 4, d + 8, d + 8, {0, 0, 0}, 0.28)
        L:shape(G.ELLIPSE, b.x, b.y, d, d, held and ec or SLATE, held and 0.55 or 0.5)
        -- element fill grows with energy; full = bright and pulsing
        local pulse = (b.id == 'BU' and ready) and (0.5 + 0.5 * math.sin(app.t * 8)) or 0
        local fd = d * 0.86 * math.sqrt(fillK)
        L:shape(G.ELLIPSE, b.x, b.y, fd, fd, ec, elem and (ready and (0.75 + 0.2 * pulse) or 0.45) or 0)
        L:shape(G.ELLIPSE, b.x, b.y, d * 1.25, d * 1.25, ec, (b.id == 'BU' and ready) and 0.35 * pulse or 0, 0, 0.5)
        L:shape(G.RING, b.x, b.y, d, d, WHITE, ready and 0.75 or 0.35)
        L:label(txt or b.label, b.x, b.y, d, d, txt and b.r * 0.62 or b.r * 0.78, WHITE, 'c', {0, 0, 0, 170}, ready and 1 or 0.75)
    end
    -- stick
    local st = self.stick
    local bx, by = st.on and st.ox or (-app.W / 2 + 230), st.on and st.oy or (-app.H / 2 + 200)
    local kx = U.clamp(st.x, -70, 70)
    local ky = U.clamp(st.y, -70, 70)
    L:shape(G.ELLIPSE, bx, by, 200, 200, WHITE, st.on and 0.18 or 0.1)
    L:shape(G.RING, bx, by, 196, 196, WHITE, st.on and 0.6 or 0.35)
    L:shape(G.ELLIPSE, bx + kx, by + ky, 86, 86, WHITE, st.on and 0.7 or 0.4)
    -- pause: small slate disc under the round capsule
    local py = app.H / 2 - 222
    L:shape(G.ELLIPSE, 0, py, 54, 54, SLATE, 0.55)
    L:shape(G.RING, 0, py, 54, 54, WHITE, 0.5)
    L:rect(-7, py, 6, 20, WHITE, 0.85)
    L:rect(7, py, 6, 20, WHITE, 0.85)
    L:finish()
end

function T:free() self.L:free() end

return T
