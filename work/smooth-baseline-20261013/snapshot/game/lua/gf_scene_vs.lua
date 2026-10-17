-- VS screen: the screen splits on a diagonal in both element colours, big portraits slide in,
-- names and titles land, a giant VS strikes, the stage title appears in Genshin's area-title
-- style. While it plays both fighters' art is decoded, so the fight starts without a wait.
-- args: fight args, or {arcade = state} (the ladder picks the opponent and stage).
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Art = require('gf_art')
local Stage = require('gf_stage')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local CN = {'一', '二', '三', '四', '五', '六', '七'}

function S.new(app, args)
    local self = setmetatable({app = app, t = 0}, S)
    app:dropBackdrop()
    if args.arcade then
        local ar = args.arcade
        local opp = ar.ladder[ar.step]
        local st = Stage.order[(ar.step - 1) % #Stage.order + 1]
        local boss = ar.step == #ar.ladder
        args = {chars = {ar.player, opp}, stage = st, mode = 'arcade', arcade = ar,
                cpu = {false, boss and 4 or math.min(4, 1 + (ar.step + 1) // 2)}}
        self.label = boss and '最终决战' or ('第' .. CN[ar.step] .. '战')
    end
    self.args = args
    self.chars = {Art.byKey[args.chars[1]], Art.byKey[args.chars[2]]}
    self.tier = app.quality == 'lo' and 'lo' or 'hi'
    self.jobs = {Art.prepare(args.chars[1], self.tier), Art.prepare(args.chars[2], self.tier)}
    self.back = G.layer(app.layers.back)
    self.ports = {G.bitmap(app.layers.world), G.bitmap(app.layers.world)}
    self.L = G.layer(app.layers.ui)
    self.portDone = 0
    app.audio:play(app.audio.ID.shock)
    return self
end

function S:buildPortrait(i)
    local app = self.app
    local p = self.ports[i]
    local img = Art.portrait(self.chars[i].key)
    p:drawMany({{img = img, ox = 0, oy = 0, s = 1}})
    local side = i == 1 and -1 or 1
    p.node:pos(side * (app.W / 2 + 400), i == 1 and 70 or -150):scale(6.2, 6.2):on(true)
    p.node:tween({anchoredPositionX = side * (app.W / 2 - 420)}, 0.45, 'OutCubic')
end

function S:tick()
    local app = self.app
    if self.portDone < 2 then
        self.portDone = self.portDone + 1
        self:buildPortrait(self.portDone)
        return
    end
    self.t = self.t + 1 / 60
    local ready = true
    for _, j in ipairs(self.jobs) do if not j:step(5000) then ready = false end end
    if self.t > 0.9 and not self.vsPlayed then
        self.vsPlayed = true
        app.audio:play(app.audio.ID.eboom.electro)
    end
    for _, a in ipairs(app.input:menu()) do if a == 'ok' and self.t > 1.2 then self.t = math.max(self.t, 2.9) end end
    if ready and self.t >= 3.2 and not self.left then
        self.left = true
        app:travel('fight', self.args, K.elementColor[self.chars[1].element])
    end
end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    local t = self.t
    local B = self.back
    local c1, c2 = self.chars[1], self.chars[2]
    local e1 = UI.ECOL[c1.element] or K.elementColor[c1.element]
    local e2 = UI.ECOL[c2.element] or K.elementColor[c2.element]
    B:begin()
    B:rect(0, 0, W + 60, H + 60, UI.NAVY)
    local k = U.ease.outCubic(U.clamp(t / 0.35, 0, 1))
    -- two halves meet on a diagonal: element-tinted slabs, hatch, a gold seam
    local d = (1 - k) * W
    UI.slab(B, -W * 0.52 - d, 0, W * 1.1, H * 2.2, U.mix(e1, UI.NAVY, 0.55), 1, -UI.SLANT)
    UI.slab(B, W * 0.52 + d, 0, W * 1.1, H * 2.2, U.mix(e2, UI.NAVY, 0.55), 1, -UI.SLANT)
    UI.stripes(B, -W * 0.3 - d, 0, W * 0.6, H * 2.2, 26, UI.WHITE, 0.035, -UI.SLANT)
    UI.stripes(B, W * 0.3 + d, 0, W * 0.6, H * 2.2, 26, UI.WHITE, 0.035, -UI.SLANT)
    B:shape(G.ELLIPSE, -W / 2 + 320, -60, 1100, 1100, e1, 0.35, 0, 0.5)
    B:shape(G.ELLIPSE, W / 2 - 320, 60, 1100, 1100, e2, 0.35, 0, 0.5)
    -- streaks racing along the diagonal
    for i = 1, 12 do
        local side = i % 2 == 0 and -1 or 1
        local yy = -H / 2 + i * H / 12
        local off = ((t * (900 + (i % 3) * 300) + i * 173) % (W * 1.6)) - W * 0.8
        B:rect(side * off, yy, 260 + (i % 3) * 140, i % 4 == 0 and 4 or 2, UI.WHITE, 0.14, -UI.SLANT)
    end
    -- seam: white core, gold hairlines, element bars either side
    B:rect(0, 0, 10 * k, H * 2.4, UI.WHITE, 0.95, -UI.SLANT)
    B:rect(-16, 0, 3, H * 2.4, UI.GOLD, 0.9 * k, -UI.SLANT)
    B:rect(16, 0, 3, H * 2.4, UI.GOLD, 0.9 * k, -UI.SLANT)
    B:rect(-38, 0, 14, H * 2.4, e1, 0.8 * k, -UI.SLANT)
    B:rect(38, 0, 14, H * 2.4, e2, 0.8 * k, -UI.SLANT)
    -- giant ghost names behind the portraits
    B:label((K.en[c1.key] or ''):upper(), -W / 2 + 420 - (1 - k) * 300, H / 2 - 170, 1500, 260, 200, UI.WHITE, 'c', nil, 0.08 * k)
    B:label((K.en[c2.key] or ''):upper(), W / 2 - 420 + (1 - k) * 300, -H / 2 + 170, 1500, 260, 200, UI.WHITE, 'c', nil, 0.08 * k)
    B:finish()
    local L = self.L
    L:begin()
    -- names: 1P bottom-left, 2P top-right
    local nk = U.ease.outBack(U.clamp((t - 0.3) / 0.35, 0, 1))
    local na = U.clamp((t - 0.3) / 0.15, 0, 1)
    for i, c in ipairs({c1, c2}) do
        local side = i == 1 and -1 or 1
        local ec = i == 1 and e1 or e2
        local al = i == 1 and 'l' or 'r'
        local ex = side * (W / 2 - 80)
        local bx = ex - side * 360 + side * (1 - nk) * -260
        local y = i == 1 and (-H / 2 + 200) or (H / 2 - 170)
        L:shape(G.ELLIPSE, ex - side * 300, y - 10, 900, 330, UI.NAVY, 0.5 * na, 0, 0.5)
        L:label(UI.track((K.en[c.key] or ''):upper()), bx, y + 74, 720, 28, 18, UI.GOLD, al, nil, na)
        L:label(c.name, bx, y + 6, 720, 120, 104, UI.WHITE, al, {0, 0, 0, 90}, na)
        L:rect(ex - side * 240, y - 58, 480 * na, 3, ec, na)
        L:label((K.title[c.key] or '') .. '　·　' .. (K.elementName[c.element] or '') .. '元素　·　' .. (K.weaponName[c.weapon] or ''),
                bx, y - 88, 720, 30, 20, UI.CREAM, al, nil, na)
        UI.badge(L, c.element, ex - side * ((utf8.len(c.name) or 3) * 104 + 60), y + 6, 72, na)
    end
    -- portraits fade out at their lower edge (busts)
    for i, py in ipairs({70, -150}) do
        local side = i == 1 and -1 or 1
        local ec = i == 1 and e1 or e2
        local base = U.mix(ec, UI.NAVY, 0.55)
        for j = 0, 2 do
            L:shape(G.ELLIPSE, side * (W / 2 - 420), py - 30 - j * 20, 820, 150 + j * 50, base, 0.5 + j * 0.2, 0, 0.5)
        end
    end
    -- VS: slams in big, shards burst, white flash
    local vk = U.clamp((t - 0.8) / 0.22, 0, 1)
    local vs = U.ease.outBack(vk)
    local after = U.clamp((t - 1.02) / 0.5, 0, 1)
    L:shape(G.ELLIPSE, 0, 0, 900, 900, UI.WHITE, (vk > 0 and (1 - after) * 0.5 or 0), 0, 0.5)
    for j = 0, 7 do
        local a = math.rad(j * 45 + 20)
        local r = 120 + after * 520
        L:shape(G.TRI, math.cos(a) * r, math.sin(a) * r, 26, 70, j % 2 == 0 and UI.WHITE or UI.GOLD, (vk > 0 and (1 - after)) and (1 - after) * 0.9 or 0, j * 45 - 70)
    end
    UI.slab(L, 0, 0, 760 * vs, 26, UI.WHITE, 0.9 * vk * (1 - after * 0.6), -UI.SLANT)
    local v = L:label('VS', 0, 8, 420, 240, 210, UI.WHITE, 'c', {40, 30, 70}, vk)
    v:scale(v.sx * (2.2 - 1.2 * vs), v.sy * (2.2 - 1.2 * vs))
    -- stage strip at the bottom centre, ladder label at the top centre
    local sk = U.ease.outCubic(U.clamp((t - 1.4) / 0.4, 0, 1))
    local st = self.args.stage
    local sdata = st and Paint.available[st] and require('gf_bg_' .. st)
    L:rect(0, -H / 2 + 60, 760 * sk, 64, UI.NAVY, 0.85 * sk)
    L:rect(0, -H / 2 + 93, 760 * sk, 2, UI.GOLD, 0.8 * sk)
    L:label(UI.track('STAGE'), -300, -H / 2 + 60, 120, 30, 14, UI.GOLD, 'l', nil, sk)
    L:label(sdata and sdata.name or '训练场', 30, -H / 2 + 62, 560, 50, 30, UI.WHITE, 'c', nil, sk)
    L:rect(0, H / 2 - 40, 360 * sk, 46, UI.GOLD_HI, (self.label and 0.95 or 0) * sk, 0)
    L:label(self.label or '', 0, H / 2 - 40, 360, 46, 26, UI.TEXT, 'c', nil, self.label and sk or 0)
    L:finish()
end

function S:exit()
    self.back:free()
    for _, p in ipairs(self.ports) do p:free() end
    self.L:free()
end

return S
