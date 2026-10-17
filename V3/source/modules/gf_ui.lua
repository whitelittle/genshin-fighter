__loaders['gf_ui'] = function()
local G = require('gf_gfx')
local U = require('gf_util')

local UI = {}

UI.CREAM = {236, 229, 216}
UI.CREAM2 = {248, 244, 236}
UI.TEXT = {37, 42, 60}           -- dark navy text on cream
UI.SLATE = {40, 45, 62}
UI.SLATE2 = {58, 64, 84}
UI.NAVY = {11, 15, 31}
UI.NAVY2 = {22, 28, 52}
UI.WHITE = {255, 255, 255}
UI.GREY = {214, 208, 196}
UI.DIM = {150, 156, 176}
UI.GOLD = {211, 188, 142}        -- Genshin's ornament gold (hairlines, small caps)
UI.GOLD_HI = {255, 222, 150}     -- warm highlight (stars, rewards)
UI.GOLD_EDGE = {255, 228, 160}
UI.SHADOW = {0, 0, 0, 150}
UI.SLANT = 12                    -- the layout's diagonal, degrees
UI.GOLD2 = {255, 236, 180}
UI.INK = {10, 12, 24}

function UI.rrect(L, x, y, w, h, r, col, am)
    r = math.min(r, w / 2, h / 2)
    L:rect(x, y, w - 2 * r, h, col, am)
    L:rect(x - w / 2 + r / 2, y, r, h - 2 * r, col, am)
    L:rect(x + w / 2 - r / 2, y, r, h - 2 * r, col, am)
    for _, cx in ipairs({x - w / 2 + r, x + w / 2 - r}) do
        for _, cy in ipairs({y - h / 2 + r, y + h / 2 - r}) do
            L:shape(G.ELLIPSE, cx, cy, r * 2, r * 2, col, am)
        end
    end
end

function UI.capsule(L, x, y, w, h, col, am)
    L:rect(x, y, math.max(0, w - h), h, col, am)
    L:shape(G.ELLIPSE, x - w / 2 + h / 2, y, h, h, col, am)
    L:shape(G.ELLIPSE, x + w / 2 - h / 2, y, h, h, col, am)
end

function UI.slate(L, x, y, w, h, am)
    UI.rrect(L, x, y, w, h, 8, UI.SLATE, 0.72 * (am or 1))
end

function UI.card(L, x, y, w, h, on, am)
    am = am or 1
    L:shape(G.ELLIPSE, x, y, w * 1.08, h * 1.6, UI.GOLD, (on and 0.28 or 0) * am, 0, 0.5)
    UI.rrect(L, x, y - 3, w + 4, h + 4, 7, {0, 0, 0}, 0.25 * am)
    UI.rrect(L, x, y, w + 4, h + 4, 7, on and UI.GOLD_EDGE or UI.CREAM, (on and 1 or 0) * am)
    UI.rrect(L, x, y, w, h, 6, on and UI.CREAM2 or UI.CREAM, am)
end

function UI.slab(L, x, y, w, h, col, am, rot)
    return L:rect(x, y, w, h, col, am, rot or UI.SLANT)
end

function UI.stripes(L, x, y, w, h, n, col, am, rot)
    rot = rot or UI.SLANT
    for i = 1, n do
        L:rect(x - w / 2 + (i - 0.5) * w / n, y, 2, h, col, am, rot)
    end
end

function UI.chevron(L, x, y, s, col, am, dir)
    dir = dir or 1
    L:rect(x, y + s * 0.25, s * 0.62, s * 0.16, col, am, -dir * 40)
    L:rect(x, y - s * 0.25, s * 0.62, s * 0.16, col, am, dir * 40)
end

function UI.constellation(L, x, y, r, t, col, am)
    col = col or UI.WHITE
    L:shape(G.RING, x, y, r * 2, r * 2, col, 0.22 * am, t * 4)
    L:shape(G.RING, x, y, r * 1.36, r * 1.36, col, 0.12 * am, -t * 6)
    for k = 0, 5 do
        local a = math.rad(t * 5 + k * 60 + (k % 2) * 17)
        local rr = (k % 2 == 0) and r or r * 0.68
        local s = (k % 3 == 0) and 22 or 12
        L:shape(G.STAR4, x + math.cos(a) * rr, y + math.sin(a) * rr, s, s, col, (0.35 + 0.25 * math.sin(t * 2 + k)) * am, t * 20)
    end
end

local ECOL = {pyro = {255, 138, 74}, hydro = {72, 186, 245}, anemo = {98, 214, 172}, electro = {190, 132, 255},
              dendro = {150, 210, 60}, cryo = {160, 226, 240}, geo = {250, 190, 70}}
UI.ECOL = ECOL
function UI.element(L, el, x, y, s, am, col, core)
    col = col or ECOL[el] or UI.WHITE
    core = core or UI.WHITE
    am = am or 1
    if el == 'pyro' then
        L:shape(G.TRI, x, y + s * 0.16, s * 0.5, s * 0.72, col, am)
        L:shape(G.ELLIPSE, x, y - s * 0.14, s * 0.56, s * 0.56, col, am)
        L:shape(G.TRI, x, y + s * 0.02, s * 0.24, s * 0.4, core, 0.85 * am)
        L:shape(G.ELLIPSE, x, y - s * 0.17, s * 0.26, s * 0.26, core, 0.85 * am)
    elseif el == 'hydro' then
        L:shape(G.TRI, x, y + s * 0.2, s * 0.44, s * 0.56, col, am)
        L:shape(G.ELLIPSE, x, y - s * 0.12, s * 0.58, s * 0.58, col, am)
        L:shape(G.ELLIPSE, x - s * 0.1, y - s * 0.06, s * 0.16, s * 0.24, core, 0.85 * am, 20)
    elseif el == 'anemo' then
        local bg = UI.NAVY
        L:shape(G.ELLIPSE, x, y, s * 0.8, s * 0.8, col, am)
        L:shape(G.ELLIPSE, x + s * 0.1, y + s * 0.07, s * 0.6, s * 0.6, bg, am)
        L:shape(G.ELLIPSE, x - s * 0.02, y - s * 0.02, s * 0.36, s * 0.36, col, am)
        L:shape(G.ELLIPSE, x + s * 0.04, y + s * 0.03, s * 0.18, s * 0.18, bg, am)
        L:shape(G.TRI, x + s * 0.34, y - s * 0.24, s * 0.16, s * 0.3, col, am, 135)
    elseif el == 'electro' then
        L:shape(G.TRI, x, y + s * 0.02, s * 0.9, s * 0.8, col, am)
        L:shape(G.TRI, x, y - s * 0.1, s * 0.46, s * 0.4, UI.NAVY, am, 180)
        L:shape(G.RECT, x, y - s * 0.03, s * 0.16, s * 0.16, core, 0.9 * am, 45)
    elseif el == 'dendro' then
        for k = 0, 2 do
            local ang = k * 120 + 90
            local r = math.rad(ang)
            L:shape(G.ELLIPSE, x + math.cos(r) * s * 0.2, y + math.sin(r) * s * 0.2, s * 0.3, s * 0.56, col, am, ang - 90)
        end
        L:shape(G.ELLIPSE, x, y, s * 0.2, s * 0.2, core, 0.9 * am)
    elseif el == 'cryo' then
        for k = 0, 2 do L:rect(x, y, s * 0.9, s * 0.1, col, am, k * 60) end
        for k = 0, 5 do
            local a = math.rad(k * 60)
            L:shape(G.RECT, x + math.cos(a) * s * 0.4, y + math.sin(a) * s * 0.4, s * 0.16, s * 0.16, col, am, 45 + k * 60)
        end
        L:shape(G.RECT, x, y, s * 0.24, s * 0.24, core, 0.9 * am, 45)
    else -- geo
        L:shape(G.RECT, x, y, s * 0.66, s * 0.66, col, am, 45)
        L:shape(G.RECT, x, y, s * 0.36, s * 0.36, core, 0.85 * am, 45)
        L:shape(G.RECT, x, y, s * 0.16, s * 0.16, col, am, 45)
    end
end

function UI.badge(L, el, x, y, s, am)
    am = am or 1
    local col = ECOL[el] or UI.WHITE
    L:shape(G.ELLIPSE, x, y, s * 1.5, s * 1.5, col, 0.25 * am, 0, 0.5)
    L:shape(G.ELLIPSE, x, y, s, s, UI.NAVY, 0.85 * am)
    L:shape(G.RING, x, y, s, s, col, 0.9 * am)
    UI.element(L, el, x, y, s * 0.62, am)
end

function UI.header(L, title, en, x, y, am, col)
    am = am or 1
    col = col or UI.GOLD
    UI.slab(L, x - 40, y - 2, 10, 74, col, am, UI.SLANT)
    L:label(title, x + 230, y + 10, 460, 64, 50, UI.WHITE, 'l', nil, am)
    L:label(en or '', x + 230, y - 34, 460, 26, 15, col, 'l', nil, am)
end

function UI.leftPanel(L, W, H, k, acc, am)
    am = am or 1
    local sx = -W / 2 + 300 - (1 - k) * 500
    UI.slab(L, sx, 0, 980, H * 1.9, UI.NAVY, 0.88 * am, -UI.SLANT)
    UI.stripes(L, sx - 120, 0, 700, H * 1.9, 18, UI.WHITE, 0.025 * am, -UI.SLANT)
    local ex = sx + 490 / math.cos(math.rad(UI.SLANT))
    UI.slab(L, ex, 0, 3, H * 2, UI.GOLD, 0.75 * am, -UI.SLANT)
    UI.slab(L, ex + 30, 0, 12, H * 2, acc or UI.GOLD, 0.55 * am, -UI.SLANT)
    return ex
end

function UI.screenTitle(L, W, H, title, en, am)
    L:label(title, -W / 2 + 338, H / 2 - 92, 420, 70, 54, UI.WHITE, 'l', nil, am)
    L:label(en, -W / 2 + 388, H / 2 - 140, 520, 26, 15, UI.GOLD, 'l', nil, am)
    L:rect(-W / 2 + 330, H / 2 - 164, 400, 2, UI.GOLD, 0.6 * am)
end

function UI.track(s)
    return (s:gsub('(.)', '%1 '):sub(1, -2))
end

function UI.tap(L, id, x, y, w, h, action, on)
    local inp = UI.app and UI.app.input
    if not inp then return end
    L.taps = L.taps or {}
    local pa = L.taps[id]
    if not on then
        if pa and pa.gen == inp.gen and pa.on then inp:moveArea(pa.b, 0, -5000, 1, 1); pa.on = false end
        return
    end
    if pa and pa.gen == inp.gen and pa.b then
        if pa.x ~= x or pa.y ~= y or not pa.on then inp:moveArea(pa.b, x, y, w, h) end
    else
        pa = {b = inp:area(x, y, w, h, {click = function() inp.menuQ[#inp.menuQ + 1] = action end}), gen = inp.gen}
        L.taps[id] = pa
    end
    pa.x, pa.y, pa.on = x, y, true
end

function UI.prompt(L, x, y, key, label, am, action)
    am = am or 1
    if action then UI.tap(L, 'prompt' .. key, x + 50, y, 180, 54, action, am > 0.5) end
    L:rect(x, y - 3, 34, 34, {0, 0, 0}, 0.35 * am)
    L:rect(x, y, 32, 32, UI.CREAM, am)
    L:label(key, x, y, 32, 32, 17, UI.TEXT, 'c', nil, am)
    L:label(label, x + 24 + 60, y, 120, 30, 18, UI.WHITE, 'l', {0, 0, 0, 90}, am)
end

function UI.title(L, s, x, y, size, col, am, _)
    return L:label(s, x, y, size * ((utf8.len(s) or #s) + 2), size * 1.5, size, col or UI.WHITE, 'c', {0, 0, 0, 120}, am)
end

function UI.areaTitle(L, s, sub, x, y, am)
    am = am or 1
    local w = 120 + (utf8.len(s) or 4) * 40
    L:label(s, x, y, w + 200, 70, 46, UI.WHITE, 'c', {0, 0, 0, 140}, am)
    for _, side in ipairs({-1, 1}) do
        local lx = x + side * (w / 2 + 70)
        L:rect(lx, y, 120, 2, UI.WHITE, 0.8 * am)
        L:shape(G.RECT, lx + side * 64, y, 8, 8, UI.WHITE, am, 45)
    end
    if sub then L:label(sub, x, y - 46, 600, 30, 20, UI.GREY, 'c', {0, 0, 0, 120}, am) end
end

local Menu = {}
Menu.__index = Menu

function UI.menu(app, parent, items, o)
    local self = setmetatable({app = app, items = items, o = o, sel = o.sel or 1, hl = o.sel or 1,
                               L = G.layer(parent), areas = {}, t = 0, blink = 0}, Menu)
    self:bind()
    return self
end

function Menu:rowY(i) return self.o.y - (i - 1) * (self.o.h + (self.o.gap or 10)) end

function Menu:bind()
    local app = self.app
    for i in ipairs(self.items) do
        local idx = i
        self.areas[i] = app.input:area(self.o.x, self:rowY(i), self.o.w, self.o.h, {
            down = function() if self.sel ~= idx then self.sel = idx; app.audio:play(app.audio.ID.move) end end,
            click = function() self.sel = idx; self:pick() end,
        })
    end
end

function Menu:pick()
    local it = self.items[self.sel]
    if not it or it.disabled then self.app.audio:play(self.app.audio.ID.fail) return end
    self.blink = 12
    self.app.audio:play(self.app.audio.ID.ok)
    if self.o.onPick then self.o.onPick(it.id, it) end
end

function Menu:input(actions)
    local app = self.app
    for _, a in ipairs(actions) do
        if a == 'up' then self.sel = (self.sel - 2) % #self.items + 1; app.audio:play(app.audio.ID.move)
        elseif a == 'down' then self.sel = self.sel % #self.items + 1; app.audio:play(app.audio.ID.move)
        elseif a == 'left' or a == 'right' then
            local it = self.items[self.sel]
            local fn = it and it[a]
            if fn then fn(); app.audio:play(app.audio.ID.tick) end
        elseif a == 'ok' then self:pick()
        elseif a == 'back' then if self.o.onBack then app.audio:play(app.audio.ID.back); self.o.onBack() end
        end
    end
end

function Menu:draw(am)
    am = am or 1
    local o = self.o
    local L = self.L
    self.t = self.t + 1
    if self.blink > 0 then self.blink = self.blink - 1 end
    if self.lastSel ~= self.sel then self.lastSel, self.selT = self.sel, 0 end
    self.selT = (self.selT or 0) + 1
    local sweep = U.ease.outCubic(U.clamp(self.selT / 9, 0, 1))
    local acc = o.accent or UI.GOLD
    local size = o.size or 28
    L:begin()
    for i, it in ipairs(self.items) do
        local y = self:rowY(i)
        local on = i == self.sel
        local enter = U.ease.outCubic(U.clamp((self.t - (i - 1) * 3) / 14, 0, 1))
        local a = am
        -- Keep labels readable immediately; retain only the position/sweep animation.
        local x0 = o.x - o.w / 2 - (1 - enter) * 160
        local k = on and sweep or 0
        local flash = (on and self.blink > 0 and self.blink % 4 < 2) and 1 or 0
        local sw = o.w * (0.25 + 0.75 * k)
        L:rect(x0 + sw / 2 + 8, y - 6, sw, o.h, {0, 0, 0}, (on and 0.35 or 0) * a, 2)
        L:rect(x0 + sw / 2, y, sw, o.h, flash > 0 and UI.WHITE or UI.CREAM, (on and 0.96 or 0) * a, 2)
        L:rect(x0 + 6, y, 10, o.h + 6, acc, (on and 1 or 0) * a, 2)
        UI.chevron(L, x0 + sw - 30 + math.sin(self.t * 0.25) * 3, y, 22, UI.TEXT, ((on and not it.value) and k or 0) * a)
        local tx = x0 + 34 + (on and 18 * k or 0)
        L:label(o.numbers and ('%02d'):format(i) or '', tx + 30, y + 1, 60, o.h, 18, on and acc or UI.GOLD, 'l', nil, (o.numbers and (on and 1 or 0.7) or 0) * a)
        if o.numbers then tx = tx + 46 end
        local col = it.disabled and UI.DIM or (on and UI.TEXT or UI.WHITE)
        local la = (it.disabled and 0.5 or (on and 1 or 0.78)) * a
        local ly = y + ((on and it.sub) and size * 0.3 or 0)
        L:label(it.label, tx + (o.w - 120) / 2, ly, o.w - 120, o.h, size, col, 'l', nil, la)
        L:label(it.sub or '', tx + (o.w - 120) / 2, y - size * 0.62, o.w - 120, 22, 15, {92, 100, 124}, 'l', nil, (on and it.sub) and a or 0)
        local v = it.value and it.value() or ''
        local vx = x0 + o.w - 120
        L:label(v, vx, y, 200, o.h, size * 0.8, col, 'c', nil, it.value and la or 0)
        UI.chevron(L, vx - 96, y, 16, col, (it.value and on) and a or 0, -1)
        UI.chevron(L, vx + 96, y, 16, col, (it.value and on) and a or 0, 1)
    end
    L:finish()
end

function Menu:free() self.L:free() end

return UI
end
