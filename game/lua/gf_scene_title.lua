-- Title screen, fighting-game style: two fighters face off over the painted backdrop with
-- element light behind each; the logo is a picture (designed in tools/logo/logo.html, baked by
-- tools/build_logo.py) drawn one tile per frame, tilted and slammed in, then a light sweep;
-- a giant ghost word behind; "press any button" strip.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Art = require('gf_art')
local Show = require('gf_show')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local PAIRS = {{'raidenshogun', 'furina'}, {'zhongli', 'mavuika'}, {'kamisatoayaka', 'tartaglia'}, {'nahida', 'venti'},
               {'arlecchino', 'clorinde'}, {'aratakiitto', 'yaemiko'}, {'neuvillette', 'skirk'}}

function S.new(app)
    local self = setmetatable({app = app, t = 0}, S)
    local key = Paint.available.mondstadt and 'mondstadt' or next(Paint.available)
    if key then self.bd = app:backdrop(key) end
    local pair = PAIRS[(math.floor(app.t * 7) % #PAIRS) + 1]
    self.pair = pair
    self.left = Show.new(app.layers.world)
    self.right = Show.new(app.layers.world)
    self.L = G.layer(app.layers.ui)
    self.tier = app.quality == 'lo' and 'lo' or 'hi'
    self.back = G.layer(app.layers.back)
    self.built = 0
    -- logo picture: one bitmap per tile under a tilted group, shown once every tile is drawn
    local data = require('gf_logo')[app.quality == 'lo' and 'lo' or 'hi']
    self.logoData = data
    self.logoPal = U.palette(data.pal)
    self.logoG = G.group(app.layers.ui)
    self.logoG:pos(0, 205):rot(4):on(false)
    self.logoTiles = {}
    self.over = G.layer(app.layers.ui)       -- light sweep above the logo
    app.audio:play(app.audio.ID.open)
    return self
end

-- logo tiles are built over many frames: first the rect nodes (300 per frame), then the
-- rects themselves (450 per frame); reveal when every tile is complete
function S:buildLogo()
    local d = self.logoData
    local cur = self.logoCur
    if not cur then
        local i = #self.logoTiles + 1
        local tile = d.tiles[i]
        if not tile then return true end
        local b = G.bitmap(self.logoG)
        b.node:scale(d.u, d.u)
        cur = {b = b, i = i, img = {bytes = U.decodeAll(tile.d), n = tile.n, pal = self.logoPal,
                                    ax = d.w / 2 - tile.x, ay = d.h / 2}}
        self.logoCur = cur
        return false
    end
    local b, img = cur.b, cur.img
    if #b.kids < img.n then
        b:ensure(math.min(img.n, #b.kids + 300))
        return false
    end
    if not cur.started then cur.started = true; b:start(img, 'logo' .. cur.i) end
    if not b:step(450) then return false end
    b.node:on(true)
    self.logoTiles[cur.i] = b
    self.logoCur = nil
    if cur.i == #d.tiles then
        self.logoT = 0
        self.logoG:scale(1.5, 1.5):on(true)
        self.logoG:tween({localScaleX = 0.88, localScaleY = 0.88}, 0.35, 'OutBack')
        self.app.audio:play(self.app.audio.ID.eboom.electro)
    end
    return false
end

-- one fighter per frame (a hi-tier pose is ~1200 rects), each slides in when it is ready
function S:buildFighters()
    if self.built >= 2 then return end
    self.built = self.built + 1
    local app = self.app
    local i = self.built
    local side = i == 1 and -1 or 1
    local sh = i == 1 and self.left or self.right
    sh:set(self.pair[i], self.tier, 'idle', side * (app.W / 2 - 360), -app.H / 2 + 30, 1.45, -side, 0)
    local n = sh.bmp.node
    local x0 = n.x
    n:pos(x0 + side * 420, n.y)
    n:tween({anchoredPositionX = x0}, 0.8, 'OutCubic')
end

function S:tick()
    local app = self.app
    self.t = self.t + 1 / 60
    self.frameN = (self.frameN or 0) + 1
    if self.frameN >= 2 then
        if self.built < 2 then self:buildFighters() else self:buildLogo() end
    end
    if self.logoT then self.logoT = self.logoT + 1 / 60 end
    if self.bd then self.bd:step(300) end
    local go = false
    for _, a in ipairs(app.input:menu()) do if a == 'ok' or a == 'pause' or a == 'back' then go = true end end
    local p = app.input:pad(1)
    if p.pressed ~= 0 then go = true end
    if go and self.t > 0.6 and not self.leaving then
        self.leaving = true
        app.audio:play(app.audio.ID.okBig)
        app:travel('menu', nil, {255, 214, 120})
    end
    if not self.area then
        self.area = app.input:area(0, 0, app.W, app.H, {click = function()
            if not self.leaving and self.t > 0.6 then self.leaving = true; app:travel('menu', nil, {255, 214, 120}) end
        end})
    end
end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    if self.bd then self.bd:draw(0.3, {10, 14, 34}) end
    local t = self.t
    local k = U.ease.outCubic(U.clamp(t / 0.9, 0, 1))
    local c1, c2 = Art.byKey[self.pair[1]], Art.byKey[self.pair[2]]
    local e1 = UI.ECOL[c1.element] or K.elementColor[c1.element]
    local e2 = UI.ECOL[c2.element] or K.elementColor[c2.element]
    -- backdrop graphics: element light per fighter, light beams, ghost word, streaks
    local B = self.back
    B:begin()
    B:shape(G.ELLIPSE, -W / 2 + 360, -H / 2 + 300, 760, 900, e1, 0.3 * k, 0, 0.5)
    B:shape(G.ELLIPSE, W / 2 - 360, -H / 2 + 300, 760, 900, e2, 0.3 * k, 0, 0.5)
    for i = 1, 3 do
        B:rect(-W / 2 + 200 + i * 120, 0, 60 + i * 20, H * 2, e1, 0.06 * k, -UI.SLANT - i * 4)
        B:rect(W / 2 - 200 - i * 120, 0, 60 + i * 20, H * 2, e2, 0.06 * k, UI.SLANT + i * 4)
    end
    B:label('七国之巅', 0, 60 - t * 4 % 20, 1800, 360, 300, UI.WHITE, 'c', nil, 0.05 * k)
    for i = 1, 8 do
        local yy = -H / 2 + i * H / 8.5
        local xx = ((t * (500 + (i % 3) * 260) + i * 197) % (W + 700)) - W / 2 - 350
        B:rect(xx, yy, 220 + (i % 3) * 150, 2, UI.WHITE, 0.09, -UI.SLANT)
    end
    B:finish()
    -- logo: slash, element bars, title, English plate
    local L = self.L
    L:begin()
    local y = 205
    local lt = self.logoT or -1
    local lk = U.clamp(lt / 0.3, 0, 1)
    -- dark glow behind the logo, impact flash and ring when it lands
    L:shape(G.ELLIPSE, 0, y - 10, 1500, 520, UI.NAVY, 0.55 * lk, 0, 0.5)
    L:shape(G.ELLIPSE, 0, y, 1300, 420, UI.WHITE, lt >= 0 and math.max(0, 0.5 - lt) or 0, 0, 0.5)
    local rk = U.clamp(lt / 0.6, 0, 1)
    L:shape(G.RING, 0, y, 400 + rk * 1400, 160 + rk * 520, UI.WHITE, lt >= 0 and (1 - rk) * 0.6 or 0, 4)
    local pk = U.ease.outCubic(U.clamp((lt - 0.25) / 0.4, 0, 1))
    L:label('七国之巅　·　元素激斗', 0, y - 250, 700, 34, 22, UI.GREY, 'c', {0, 0, 0, 120}, pk)
    -- press any button
    local blink = 0.55 + 0.45 * math.sin(t * 3.4)
    local by = -H / 2 + 120
    L:rect(0, by, 640 * pk, 46, UI.NAVY, 0.7 * pk)
    L:rect(0, by + 23, 640 * pk, 2, UI.GOLD, 0.6 * pk)
    L:rect(0, by - 23, 640 * pk, 2, UI.GOLD, 0.3 * pk)
    L:label('按任意键开始　PRESS ANY BUTTON', 0, by, 640, 46, 22, UI.WHITE, 'c', nil, blink * pk)
    UI.chevron(L, -350 - math.sin(t * 6) * 6, by, 22, UI.WHITE, blink * pk, -1)
    UI.chevron(L, 350 + math.sin(t * 6) * 6, by, 22, UI.WHITE, blink * pk, 1)
    L:label('非官方同人作品　·　千星奇域', -W / 2 + 220, -H / 2 + 28, 420, 30, 15, UI.DIM, 'l', nil, k)
    L:label('v2.0', W / 2 - 80, -H / 2 + 28, 120, 30, 15, UI.DIM, 'r', nil, k)
    L:finish()
    local O = self.over
    O:begin()
    local sw = lt >= 0 and ((lt - 0.4) % 4.0) / 0.7 or 2
    O:rect(-700 + sw * 1400, y, 70, 330, UI.WHITE, (sw >= 0 and sw <= 1) and 0.22 or 0, 4 - 20)
    O:rect(-640 + sw * 1400, y, 18, 330, UI.WHITE, (sw >= 0 and sw <= 1) and 0.3 or 0, 4 - 20)
    O:finish()
end

function S:exit()
    self.back:free()
    self.over:free()
    for _, b in ipairs(self.logoTiles) do b:free() end
    if self.logoCur then self.logoCur.b:free() end
    G.release(self.logoG)
    self.left:free()
    self.right:free()
    self.L:free()
end

return S
