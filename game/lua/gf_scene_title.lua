-- Title screen, fighting-game style: two fighters face off over the painted backdrop with
-- element light behind each; the logo sits on a huge white slash with element bars, the
-- English name on a dark slanted plate, a giant ghost word behind; "press any button" strip.
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
    app.audio:play(app.audio.ID.open)
    return self
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
    if self.frameN >= 2 then self:buildFighters() end
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
    local y = 170
    local sk = U.ease.outCubic(U.clamp((t - 0.15) / 0.4, 0, 1))
    UI.slab(L, 0, y + 4, 1300 * sk, 150, UI.NAVY, 0.6 * sk, 6)
    UI.slab(L, 0, y + 70, 1200 * sk, 6, e1, 0.95 * sk, 6)
    UI.slab(L, 0, y - 62, 1200 * sk, 6, e2, 0.95 * sk, 6)
    UI.slab(L, 0, y + 4, 1000 * sk, 18, UI.WHITE, 0.85 * sk * (1 - 0.6 * U.clamp((t - 0.6) / 0.6, 0, 1)), 6)
    local lk = U.ease.outBack(U.clamp((t - 0.35) / 0.4, 0, 1))
    local logo = L:label('原神格斗', 0, y + 10, 1100, 220, 168, UI.WHITE, 'c', {16, 20, 44, 220}, U.clamp((t - 0.35) / 0.15, 0, 1))
    logo:scale(logo.sx * (1.4 - 0.4 * lk), logo.sy * (1.4 - 0.4 * lk))
    L:shape(G.STAR4, 380, y + 92, 48 * lk, 48 * lk, UI.WHITE, lk, t * 30)
    L:shape(G.STAR4, 380, y + 92, 18 * lk, 18 * lk, UI.GOLD_HI, lk, -t * 50)
    local pk = U.ease.outCubic(U.clamp((t - 0.6) / 0.4, 0, 1))
    UI.slab(L, 0, y - 112, 560 * pk, 44, UI.NAVY, 0.92 * pk, 6)
    UI.slab(L, -282 * pk, y - 112, 10, 50, UI.GOLD, pk, 6)
    L:label(UI.track('GENSHIN  FIGHTER'), 0, y - 112, 560, 44, 22, UI.GOLD, 'c', nil, pk)
    L:label('七国之巅　·　元素激斗', 0, y - 166, 700, 34, 22, UI.GREY, 'c', {0, 0, 0, 120}, pk)
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
end

function S:exit()
    self.back:free()
    self.left:free()
    self.right:free()
    self.L:free()
end

return S
