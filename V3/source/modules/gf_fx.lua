__loaders['gf_fx'] = function()
local G = require('gf_gfx')
local U = require('gf_util')
local K = require('gf_kits')

local FX = {}
FX.__index = FX

local RECT, ELLIPSE, TRI, STAR4, STAR5, RING = G.RECT, G.ELLIPSE, G.TRI, G.STAR4, G.STAR5, G.RING
local WHITE = {255, 255, 255}

function FX.new(app, parentWorld, parentScreen, nWorld, nScreen, nText)
    local self = setmetatable({app = app, seed = 1234567, level = 2}, FX)
    self.world = {parent = parentWorld, img = {}, i = 0}
    self.screen = {parent = parentScreen, img = {}, i = 0}
    self.text = {parent = parentWorld, txt = {}, i = 0}
    for _ = 1, nWorld or 220 do
        local n = G.image(parentWorld, ELLIPSE)
        n:on(false)
        self.world.img[#self.world.img + 1] = n
    end
    for _ = 1, nScreen or 40 do
        local n = G.image(parentScreen, RECT)
        n:on(false)
        self.screen.img[#self.screen.img + 1] = n
    end
    for _ = 1, nText or 18 do
        local t = G.textNode(parentWorld)
        t:on(false)
        self.text.txt[#self.text.txt + 1] = t
    end
    return self
end

function FX:rand()
    self.seed = (self.seed * 1103515245 + 12345) & 0x7fffffff
    return (self.seed % 100000) / 100000
end

local function nextNode(pool)
    pool.i = pool.i % #pool.img + 1
    return pool.img[pool.i]
end

function FX:spawn(pool, o)
    local n = nextNode(pool)
    n:stop()
    local col = o.col or WHITE
    n:shape(o.shape or ELLIPSE):pos(o.x, o.y):size(o.w or 40, o.h or o.w or 40):rot(o.rot or 0)
     :scale(o.sx or o.s or 1, o.sy or o.s or 1):soft(o.soft or 0)
     :color(col[1], col[2], col[3], 255 * (o.a or 1)):on(true)
    if o.front ~= false then n:front() end
    local to = o.to or {}
    local fields = {}
    if to.x then fields.anchoredPositionX = to.x end
    if to.y then fields.anchoredPositionY = to.y end
    if to.w then fields.sizeDeltaX = to.w end
    if to.h then fields.sizeDeltaY = to.h end
    if to.s or to.sx then fields.localScaleX = to.sx or to.s end
    if to.s or to.sy then fields.localScaleY = to.sy or to.s end
    if to.rot then fields.localRotationZ = to.rot end
    local tc = to.col or col
    fields.imageColor = G.col(tc[1], tc[2], tc[3], 255 * (to.a or 0))
    n:tween(fields, o.dur or 0.3, o.ease or 'OutCubic', function() n:on(false) end)
    return n
end

function FX:hitSpark(x, y, element, heavy, dir, kind)
    local ec = K.elementColor[element] or WHITE
    local W = self.world
    local s = heavy and 1.35 or 1
    if kind == 'burst' then s = 1.7 end
    self:spawn(W, {shape = ELLIPSE, x = x, y = y, w = 70 * s, col = WHITE, a = 1, soft = 0.35,
                   to = {s = 2.6, a = 0}, dur = 0.14, ease = 'OutQuad'})
    self:spawn(W, {shape = RING, x = x, y = y, w = 50 * s, col = ec, a = 1,
                   to = {s = 5.2, a = 0}, dur = 0.28, ease = 'OutCubic'})
    if heavy then
        self:spawn(W, {shape = RING, x = x, y = y, w = 40 * s, col = WHITE, a = 0.9,
                       to = {s = 7.5, a = 0}, dur = 0.36, ease = 'OutExpo'})
    end
    local n = heavy and 9 or 6
    for i = 1, n do
        local ang = (self:rand() - 0.5) * 160 + (dir > 0 and 0 or 180)
        if i % 3 == 0 then ang = self:rand() * 360 end
        local rad = math.rad(ang)
        local len = (70 + self:rand() * 110) * s
        local d = (60 + self:rand() * 90) * s
        local cx, cy = x + math.cos(rad) * 20, y + math.sin(rad) * 20
        local col = (i % 2 == 0) and ec or WHITE
        self:spawn(W, {shape = RECT, x = cx, y = cy, w = len, h = 7 * s, rot = ang, col = col, a = 1,
                       to = {x = cx + math.cos(rad) * d, y = cy + math.sin(rad) * d, sy = 0.1, sx = 0.4, a = 0},
                       dur = 0.16 + self:rand() * 0.08, ease = 'OutQuad'})
    end
    for i = 1, heavy and 6 or 3 do
        local ang = self:rand() * math.pi * 2
        local d = (90 + self:rand() * 140) * s
        self:spawn(W, {shape = STAR4, x = x, y = y, w = (22 + self:rand() * 20) * s, col = (i % 2 == 0) and WHITE or ec, a = 1,
                       rot = self:rand() * 90,
                       to = {x = x + math.cos(ang) * d, y = y + math.sin(ang) * d - 30, s = 0.2, rot = 180, a = 0},
                       dur = 0.35 + self:rand() * 0.2, ease = 'OutCubic'})
    end
end

function FX:blockSpark(x, y, dir, heavy)
    local W = self.world
    local c = {150, 215, 255}
    self:spawn(W, {shape = RING, x = x + dir * 30, y = y, w = 90, h = 150, col = c, a = 1, to = {s = 1.8, a = 0}, dur = 0.2})
    self:spawn(W, {shape = ELLIPSE, x = x + dir * 30, y = y, w = 60, h = 120, col = WHITE, a = 0.9, soft = 0.4, to = {s = 1.6, a = 0}, dur = 0.12})
    for i = 1, heavy and 7 or 4 do
        local ang = math.rad((self:rand() - 0.5) * 120 + (dir > 0 and 180 or 0))
        local d = 70 + self:rand() * 70
        self:spawn(W, {shape = RECT, x = x + dir * 30, y = y + (self:rand() - 0.5) * 80, w = 30, h = 5, rot = math.deg(ang), col = c, a = 1,
                       to = {x = x + dir * 30 + math.cos(ang) * d, y = y + math.sin(ang) * d, a = 0, sx = 0.3}, dur = 0.18})
    end
end

local ARCS = {
    arc = {r = 120, a0 = 70, a1 = -50, w = 26, oy = 150},
    arcLow = {r = 115, a0 = -40, a1 = 60, w = 24, oy = 130},
    arcHeavy = {r = 140, a0 = 80, a1 = -60, w = 34, oy = 150},
    arcLowHeavy = {r = 140, a0 = -50, a1 = 70, w = 32, oy = 140},
    rise = {r = 150, a0 = -60, a1 = 95, w = 36, oy = 140},
    smash = {r = 170, a0 = 110, a1 = -70, w = 44, oy = 160},
    fall = {r = 130, a0 = 60, a1 = -100, w = 30, oy = 60},
    fallHeavy = {r = 150, a0 = 70, a1 = -110, w = 40, oy = 60},
    spin = {r = 130, a0 = 200, a1 = -160, w = 28, oy = 150},
    sweep = {r = 170, a0 = -20, a1 = -5, w = 22, oy = 40, flat = true},
    sweepLow = {r = 140, a0 = -15, a1 = -5, w = 18, oy = 35, flat = true},
}

function FX:slash(x, y, face, style, element, scale)
    local W = self.world
    local ec = K.elementColor[element] or WHITE
    scale = scale or 1
    if style == 'thrust' or style == 'thrustLow' then
        local yy = y + (style == 'thrust' and 160 or 40)
        self:spawn(W, {shape = RECT, x = x + face * 120, y = yy, w = 220 * scale, h = 16, col = WHITE, a = 1,
                       to = {x = x + face * 200, sy = 0.1, a = 0}, dur = 0.14})
        self:spawn(W, {shape = TRI, x = x + face * 240, y = yy, w = 40, h = 70, rot = -90 * face, col = ec, a = 1,
                       to = {x = x + face * 300, a = 0}, dur = 0.14})
        self:spawn(W, {shape = RECT, x = x + face * 110, y = yy, w = 260 * scale, h = 36, col = ec, a = 0.6,
                       to = {sy = 0.2, a = 0}, dur = 0.18})
        return
    end
    if style == 'burst' or style == 'burstSmall' or style == 'burstLow' then
        local yy = y + (style == 'burstLow' and 40 or 150)
        local s = style == 'burstSmall' and 0.8 or 1
        self:spawn(W, {shape = ELLIPSE, x = x + face * 150, y = yy, w = 120 * s, col = ec, a = 0.9, soft = 0.4, to = {s = 1.8, a = 0}, dur = 0.2})
        self:spawn(W, {shape = STAR4, x = x + face * 150, y = yy, w = 120 * s, col = WHITE, a = 1, to = {s = 0.2, rot = 90, a = 0}, dur = 0.22})
        return
    end
    if style == 'kick' then
        self:spawn(W, {shape = RING, x = x + face * 120, y = y + 130, w = 140, h = 90, col = WHITE, a = 0.8, to = {s = 1.4, a = 0}, dur = 0.15})
        return
    end
    local a = ARCS[style] or ARCS.arc
    local segs = 9
    local cx, cy = x + face * 30, y + a.oy
    for i = 0, segs - 1 do
        local k = i / (segs - 1)
        local ang = a.a0 + (a.a1 - a.a0) * k
        local rad = math.rad(ang)
        local r = a.r * scale
        local px, py = cx + face * math.cos(rad) * r, cy + math.sin(rad) * r * (a.flat and 0.35 or 1)
        local w = a.w * scale * (0.35 + math.sin(k * math.pi) * 0.9)
        local len = r * 0.42
        local rot = (ang + 90) * face + (face < 0 and 180 or 0)
        local delay = k
        local col = (i % 3 == 1) and WHITE or ec
        self:spawn(W, {shape = ELLIPSE, x = px, y = py, w = len, h = w, rot = rot, col = col, a = 0.95,
                       to = {sy = 0.15, a = 0}, dur = 0.12 + delay * 0.08, ease = 'InQuad'})
    end
    local rad = math.rad((a.a0 + a.a1) / 2)
    self:spawn(W, {shape = ELLIPSE, x = cx + face * math.cos(rad) * a.r * 0.8, y = cy + math.sin(rad) * a.r * 0.8 * (a.flat and 0.35 or 1),
                   w = a.r * 1.6 * scale, h = 10, rot = ((a.a0 + a.a1) / 2 + 90) * face, col = WHITE, a = 0.7,
                   to = {sy = 0.2, a = 0}, dur = 0.16})
end

function FX:dust(x, y, big)
    local W = self.world
    for i = 1, big and 5 or 3 do
        local dx = (self:rand() - 0.5) * 2
        self:spawn(W, {shape = ELLIPSE, x = x + dx * 40, y = y + 10, w = 60, h = 30, col = {200, 190, 170}, a = 0.55, soft = 0.4,
                       to = {x = x + dx * 160, y = y + 30 + self:rand() * 30, s = 2.2, a = 0}, dur = 0.5, ease = 'OutQuad'})
    end
end

function FX:wind(x, y, face, element)
    local W = self.world
    local ec = K.elementColor[element] or WHITE
    for i = 1, 3 do
        local yy = y + 60 + i * 60
        self:spawn(W, {shape = RECT, x = x - face * 40, y = yy, w = 120, h = 4, col = i == 2 and ec or WHITE, a = 0.7,
                       to = {x = x - face * 240, sx = 0.2, a = 0}, dur = 0.22})
    end
end

function FX:number(x, y, value, element, big, label, hold)
    local P = self.text
    P.i = P.i % #P.txt + 1
    local t = P.txt[P.i]
    t:stop()
    local ec = K.elementColor[element] or WHITE
    local s = tostring(value)
    if label then s = label end
    local size = label and 44 or (big and 40 or 30)
    local visualScale=size/20
    t:size(400/visualScale, math.max(40,70/visualScale)):pos(x + (self:rand() - 0.5) * 60, y):scale(visualScale*(label and 0.6 or 0.8))
    t:font(20, 'c'):text(s)
    t:color(ec[1], ec[2], ec[3], 255):outline(20, 14, 30, 255):on(true)
    t:front()
    t.ty = y + (label and 90 or 70)
    t:tween({anchoredPositionY = t.ty, localScaleX = visualScale, localScaleY = visualScale}, 0.25, 'OutBack')
    local app = self.app
    t.fadeAt = app.t + (hold or (label and 0.9 or 0.6))
    self.fading = self.fading or {}
    self.fading[#self.fading + 1] = t
end

function FX:update()
    local list = self.fading
    if not list then return end
    local now = self.app.t
    for i = #list, 1, -1 do
        local t = list[i]
        if t.fadeAt and now >= t.fadeAt then
            t.fadeAt = nil
            t:tween({fontColor = G.col(255, 255, 255, 0), anchoredPositionY = (t.ty or 0) + 40}, 0.25, 'InQuad', function() t:on(false) end)
            table.remove(list, i)
        end
    end
end

function FX:flash(col, a, dur)
    local S = self.screen
    local app = self.app
    col = col or WHITE
    self:spawn(S, {shape = RECT, x = 0, y = 0, w = app.W + 40, h = app.H + 40, col = col, a = a or 0.8, to = {a = 0}, dur = dur or 0.18, ease = 'OutQuad'})
end

function FX:speedLines(col, n, dur)
    local S = self.screen
    local app = self.app
    col = col or WHITE
    for i = 1, n or 18 do
        local ang = self:rand() * 360
        local rad = math.rad(ang)
        local r0 = 420 + self:rand() * 200
        local len = 300 + self:rand() * 260
        self:spawn(S, {shape = TRI, x = math.cos(rad) * r0, y = math.sin(rad) * r0, w = 26 + self:rand() * 20, h = len,
                       rot = ang + 90, col = col, a = 0.85,
                       to = {x = math.cos(rad) * (r0 + 300), y = math.sin(rad) * (r0 + 300), a = 0}, dur = (dur or 0.5) * (0.6 + self:rand() * 0.6)})
    end
end

return FX
end
