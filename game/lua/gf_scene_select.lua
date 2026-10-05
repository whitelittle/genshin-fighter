-- Character select, fighting-game layout: both sides' fighters stand large on the left and
-- right over slanted element-coloured slabs with a giant ghost name; names, element badges and
-- skills sit at the top; the roster is an 8 x 2 strip of portrait cards on a dark band at the
-- bottom with tilted 1P / 2P / CPU tags. Then a stage picker whose backdrop is the stage itself.
-- Modes: arcade (pick yourself, the ladder picks the rest), versus vs CPU (pick both),
-- versus 2P (both players pick at once), training.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Art = require('gf_art')
local Show = require('gf_show')
local Stage = require('gf_stage')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local COLS = 8
local CARD_W, CARD_H = 104, 128
local GAP = 8
local PCOL = {{255, 196, 92}, {98, 200, 255}}     -- 1P gold, 2P / CPU cyan

function S.new(app, args)
    local self = setmetatable({app = app, args = args or {}, t = 0, phase = 'chars'}, S)
    local n = #Art.roster
    self.cur = {1, math.min(n, 8)}
    self.done = {false, false}
    self.who = 1                            -- in "pick both" modes: whose pick it is
    self.mode = self.args.mode or 'versus'
    self.twoP = (self.mode == 'versus' and self.args.cpu == false)
    self.stageI = 1
    self.tier = app.quality == 'lo' and 'lo' or 'hi'
    local key = Paint.available.inazuma and 'inazuma' or next(Paint.available)
    if key then self.bd = app:backdrop(key) end
    self.shows = {Show.new(app.layers.world), Show.new(app.layers.world)}
    self.Lback = G.layer(app.layers.back)          -- slabs and card backs: behind the fighters
    self.cardsG = G.group(app.layers.world)
    self.cards = {}
    self.built = 0
    self.L = G.layer(app.layers.ui)
    self:bindAreas()
    self.shown = {nil, nil}
    return self
end

function S:cardPos(i)
    local app = self.app
    local row = (i - 1) // COLS
    local col = (i - 1) % COLS
    local totalW = COLS * CARD_W + (COLS - 1) * GAP
    local x = -totalW / 2 + CARD_W / 2 + col * (CARD_W + GAP)
    local y = -app.H / 2 + 272 - row * (CARD_H + GAP)
    return x, y
end

-- one small bitmap per card, built two per frame (keeps every frame under the budget)
function S:buildCards()
    local n = #Art.roster
    local k = 0
    while self.built < n and k < 2 do
        self.built = self.built + 1
        local i = self.built
        local c = Art.roster[i]
        local x, y = self:cardPos(i)
        local b = G.bitmap(self.cardsG)
        b:drawMany({{img = Art.face(c.key), ox = 0, oy = -40, s = 2.9}})
        b.node:pos(x, y):on(true)
        self.cards[i] = b
        k = k + 1
    end
end

function S:bindAreas()
    local app = self.app
    for i in ipairs(Art.roster) do
        local x, y = self:cardPos(i)
        local idx = i
        app.input:area(x, y, CARD_W, CARD_H, {down = function()
            local p = self:activePlayer()
            if self.phase == 'chars' and p then
                if self.cur[p] == idx then self:confirm(p) else self.cur[p] = idx; app.audio:play(app.audio.ID.move) end
            end
        end})
    end
end

function S:activePlayer()
    if self.twoP then
        if not self.done[1] then return 1 end
        if not self.done[2] then return 2 end
        return nil
    end
    if not self.done[1] then return 1 end
    if self.mode == 'versus' and not self.done[2] then return 2 end
    return nil
end

local function move(i, dx, dy, n)
    local row, col = (i - 1) // COLS, (i - 1) % COLS
    local rows = math.ceil(n / COLS)
    col = (col + dx) % COLS
    row = (row + dy) % rows
    local j = row * COLS + col + 1
    if j > n then j = n end
    return j
end

function S:confirm(p)
    local app = self.app
    self.done[p] = true
    app.audio:play(app.audio.ID.okBig)
    local c = Art.roster[self.cur[p]]
    app.audio:play(app.audio.ID.ecast[c.element])
    self.flash = self.flash or {0, 0}
    self.flash[p] = 16
    if not self:activePlayer() then self:afterChars() end
end

function S:afterChars()
    local mode = self.mode
    if mode == 'arcade' then
        self:launch()
    elseif mode == 'training' then
        self.cur[2] = (self.cur[1] % #Art.roster) + 1
        self.done[2] = true
        self.phase = 'stage'
    else
        self.phase = 'stage'
    end
end

function S:launch()
    local app = self.app
    local mine = Art.roster[self.cur[1]].key
    if self.mode == 'arcade' then
        -- ladder: 6 random opponents, the last one at boss level
        local pool = {}
        for _, c in ipairs(Art.roster) do if c.key ~= mine then pool[#pool + 1] = c.key end end
        local seed = math.floor(app.t * 1000) % 9973 + 1
        for i = #pool, 2, -1 do
            seed = (seed * 1103515245 + 12345) & 0x7fffffff
            local j = seed % i + 1
            pool[i], pool[j] = pool[j], pool[i]
        end
        local ladder = {}
        for i = 1, 6 do ladder[i] = pool[i] end
        local arcade = {ladder = ladder, step = 1, player = mine, score = 0}
        app:travel('vs', {arcade = arcade})
        return
    end
    local st = Stage.order[self.stageI] or Stage.order[1]
    local args = {chars = {mine, Art.roster[self.cur[2]].key}, stage = st, mode = self.mode}
    if self.mode == 'training' then
        args.mode = 'training'
        args.cpu = {false, false}
    elseif self.args.cpu then
        args.cpu = {false, app.settings.cpu}
    else
        args.cpu = {false, false}
    end
    app:travel('vs', args)
end

function S:tick()
    local app = self.app
    self.t = self.t + 1 / 60
    self.frameN = (self.frameN or 0) + 1
    -- the backdrop builds slowly while the card bitmaps are still being drawn (frame budget)
    if self.bd then self.bd:step(self.built < #Art.roster and 40 or 300) end
    -- stage picker: the backdrop becomes the highlighted stage
    if self.phase == 'stage' then
        local key = Stage.order[self.stageI]
        if key and Paint.available[key] and self.bdKey ~= key then
            self.bdKey = key
            self.bd = app:backdrop(key)
        end
    end
    -- the first frame creates every layer node; cards and fighters start on the next ones
    if self.frameN >= 2 then self:buildCards() end
    local acts = app.input:menu()
    local n = #Art.roster
    if self.phase == 'chars' then
        -- 2P: player 2 uses its own pad edges
        if self.twoP and not self.done[2] then
            local p2 = app.input:pad(2)
            local pr = p2.pressed or 0
            if pr & 4 ~= 0 then self.cur[2] = move(self.cur[2], -1, 0, n); app.audio:play(app.audio.ID.move) end
            if pr & 8 ~= 0 then self.cur[2] = move(self.cur[2], 1, 0, n); app.audio:play(app.audio.ID.move) end
            if pr & 1 ~= 0 then self.cur[2] = move(self.cur[2], 0, -1, n); app.audio:play(app.audio.ID.move) end
            if pr & 2 ~= 0 then self.cur[2] = move(self.cur[2], 0, 1, n); app.audio:play(app.audio.ID.move) end
            if pr & 16 ~= 0 then self:confirm(2) end
        end
        local p = self.twoP and (not self.done[1] and 1 or nil) or self:activePlayer()
        for _, a in ipairs(acts) do
            if p then
                if a == 'left' then self.cur[p] = move(self.cur[p], -1, 0, n); app.audio:play(app.audio.ID.move)
                elseif a == 'right' then self.cur[p] = move(self.cur[p], 1, 0, n); app.audio:play(app.audio.ID.move)
                elseif a == 'up' then self.cur[p] = move(self.cur[p], 0, -1, n); app.audio:play(app.audio.ID.move)
                elseif a == 'down' then self.cur[p] = move(self.cur[p], 0, 1, n); app.audio:play(app.audio.ID.move)
                elseif a == 'ok' then self:confirm(p)
                elseif a == 'alt' then self.cur[p] = (math.floor(self.t * 977) % n) + 1; self:confirm(p) end
            end
            if a == 'back' then
                if self.done[2] and not self.twoP then self.done[2] = false
                elseif self.done[1] then self.done[1] = false
                else app:travel('menu') end
                app.audio:play(app.audio.ID.back)
            end
        end
    elseif self.phase == 'stage' then
        for _, a in ipairs(acts) do
            if a == 'left' then self.stageI = (self.stageI - 2) % #Stage.order + 1; app.audio:play(app.audio.ID.move)
            elseif a == 'right' then self.stageI = self.stageI % #Stage.order + 1; app.audio:play(app.audio.ID.move)
            elseif a == 'ok' then app.audio:play(app.audio.ID.okBig); self:launch(); self.phase = 'go'
            elseif a == 'back' then self.phase = 'chars'; if self.mode == 'training' then self.done[2] = false end; self.done[1] = false; app.audio:play(app.audio.ID.back) end
        end
    end
end

-- at most one fighter bitmap is (re)built per frame (a hi-tier pose is ~1200 rects)
function S:previews()
    local app = self.app
    local built = false
    for p = 1, 2 do
        local show = self.shows[p]
        local visible = (p == 1) or (self.mode ~= 'arcade')
        if self.mode == 'training' and p == 2 then visible = self.done[1] end
        if visible then
            local key = Art.roster[self.cur[p]].key
            local pose = self.done[p] and 'special' or 'idle'
            local want = key .. pose
            if self.shown[p] ~= want and not built then
                built = true
                self.shown[p] = want
                self.swapT = self.swapT or {0, 0}
                self.swapT[p] = 0
                local side = p == 1 and -1 or 1
                show:set(key, self.tier, pose, side * (app.W / 2 - 330), -app.H / 2 + 372, 1.2, -side, 0)
                local n = show.bmp.node
                local x0 = n.x
                n:pos(x0 + side * 120, n.y)
                n:tween({anchoredPositionX = x0}, 0.3, 'OutCubic')
            end
        else
            show:hide()
            self.shown[p] = nil
        end
    end
end

-- name block for one side: tracked English name, huge name, element badge, title, skills
local function nameBlock(L, c, side, W, H, a, done, t)
    local ec = UI.ECOL[c.element] or K.elementColor[c.element]
    local al = side < 0 and 'l' or 'r'
    local ex = side * (W / 2 - 70)
    local bx = ex - side * 330             -- centre of the 660-wide text boxes
    local y = H / 2 - 200
    L:label(UI.track((K.en[c.key] or ''):upper()), bx, y + 70, 660, 26, 16, UI.GOLD, al, nil, a)
    L:label(c.name, bx, y + 8, 660, 100, 84, UI.WHITE, al, nil, a)
    local nw = (utf8.len(c.name) or 3) * 84
    UI.badge(L, c.element, ex - side * (nw + 50), y + 8, 60, a)
    L:rect(ex - side * 200, y - 48, 400, 2, ec, 0.9 * a)
    L:label((K.title[c.key] or '') .. '　·　' .. (K.elementName[c.element] or '') .. '元素　·　' .. (K.weaponName[c.weapon] or ''),
            bx, y - 76, 660, 28, 19, UI.GREY, al, nil, a)
    L:label('E  ' .. c.skill, bx, y - 108, 660, 26, 17, UI.CREAM, al, nil, a * 0.9)
    L:label('Q  ' .. c.burst, bx, y - 136, 660, 26, 17, UI.CREAM, al, nil, a * 0.9)
    -- confirmed: a tilted stamp across the fighter
    local sx = side * (W / 2 - 330)
    local da = done and a or 0
    UI.slab(L, sx, -H / 2 + 560, 330, 50, UI.CREAM, 0.95 * da, side * -8)
    UI.slab(L, sx - side * 160, -H / 2 + 560, 10, 56, ec, da, side * -8)
    L:label('已确定　READY', sx, -H / 2 + 560, 330, 50, 24, UI.TEXT, 'c', nil, da):rot(side * -8)
end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    local t = self.t
    if self.bd then self.bd:draw(self.phase == 'stage' and 0.25 or 0.5, {10, 14, 32}) end
    if (self.frameN or 0) >= 3 then self:previews() end
    local sideOn = {true, self.mode ~= 'arcade' and not (self.mode == 'training' and not self.done[1])}
    -- backdrop graphics: per-side slabs, ghost names, the roster band
    local B = self.Lback
    B:begin()
    for p = 1, 2 do
        local side = p == 1 and -1 or 1
        local c = Art.roster[self.cur[p]]
        local ec = UI.ECOL[c.element] or K.elementColor[c.element]
        local a = sideOn[p] and 1 or 0
        self.swapT = self.swapT or {0, 0}
        self.swapT[p] = (self.swapT[p] or 0) + 1
        local k = U.ease.outCubic(U.clamp(self.swapT[p] / 14, 0, 1))
        local sx = side * (W / 2 - 150)
        UI.slab(B, sx, 0, 520, H * 1.9, U.mix(ec, UI.NAVY, 0.78), 0.72 * a, side * UI.SLANT)
        UI.stripes(B, sx, 0, 420, H * 1.9, 12, UI.WHITE, 0.03 * a, side * UI.SLANT)
        UI.slab(B, sx - side * 270, 0, 3, H * 2, UI.GOLD, 0.7 * a, side * UI.SLANT)
        UI.slab(B, sx - side * 298, 0, 10, H * 2, ec, 0.45 * a, side * UI.SLANT)
        B:shape(G.ELLIPSE, side * (W / 2 - 330), -H / 2 + 560, 560, 620, ec, 0.24 * a, 0, 0.5)
        B:shape(G.ELLIPSE, side * (W / 2 - 330), -H / 2 + 372, 380, 40, {0, 0, 0}, 0.5 * a, 0, 0.5)
        local gname = (K.en[c.key] or ''):upper()
        local g = B:label(gname, side * (W / 2 - 300) + side * (1 - k) * 120, -40, 1400, 260, 190, UI.WHITE, 'c', nil, 0.07 * a * k)
        g:rot(90)
    end
    -- band behind the roster
    local gy = -H / 2 + 272 - (CARD_H + GAP) / 2
    B:rect(0, gy, W + 60, 2 * CARD_H + GAP + 56, UI.NAVY, 0.82)
    B:rect(0, gy + CARD_H + GAP / 2 + 28, W + 60, 2, UI.GOLD, 0.7)
    B:rect(0, gy - CARD_H - GAP / 2 - 28, W + 60, 2, UI.GOLD, 0.4)
    -- card backs
    for i, c in ipairs(Art.roster) do
        local x, y = self:cardPos(i)
        local ec = UI.ECOL[c.element] or K.elementColor[c.element]
        local hot = (i == self.cur[1]) or (sideOn[2] and i == self.cur[2])
        B:rect(x, y, CARD_W, CARD_H, hot and U.mix(ec, UI.NAVY, 0.45) or UI.NAVY2, 1)
        B:rect(x, y + 14, CARD_W, CARD_H - 28, U.mix(ec, UI.NAVY2, 0.7), 1)
        B:shape(G.ELLIPSE, x, y + 24, CARD_W * 1.1, CARD_H * 0.8, ec, hot and 0.45 or 0.18, 0, 0.5)
    end
    B:finish()
    local L = self.L
    L:begin()
    -- card fronts: name band, element mark, dim when not hot
    for i, c in ipairs(Art.roster) do
        local x, y = self:cardPos(i)
        local ec = UI.ECOL[c.element] or K.elementColor[c.element]
        local hot = (i == self.cur[1]) or (sideOn[2] and i == self.cur[2])
        L:rect(x, y - CARD_H / 2 + 14, CARD_W, 28, hot and UI.CREAM or UI.NAVY, hot and 1 or 0.92)
        L:rect(x, y - CARD_H / 2 + 29, CARD_W, 3, ec, 1)
        L:label(c.name, x, y - CARD_H / 2 + 14, CARD_W, 28, 15, hot and UI.TEXT or UI.WHITE, 'c', nil, 1)
        UI.element(L, c.element, x + CARD_W / 2 - 15, y + CARD_H / 2 - 15, 18, 0.95)
        L:rect(x, y + 14, CARD_W, CARD_H - 28, UI.NAVY, hot and 0 or 0.28)
    end
    for i, b in pairs(self.cards) do
        local hot = (i == self.cur[1]) or (sideOn[2] and i == self.cur[2])
        b.node:scale(hot and 1.04 or 1, hot and 1.04 or 1)
    end
    -- cursors: thick frame + tilted tag
    for p = 1, 2 do
        local x, y = self:cardPos(self.cur[p])
        local col = PCOL[p]
        local pulse = 0.75 + 0.25 * math.sin(t * 9 + p)
        local a = sideOn[p] and (self.done[p] and 1 or pulse) or 0
        local off = (p == 2 and self.cur[1] == self.cur[2]) and 5 or 0
        local fw, fh = CARD_W + 8 + off * 2, CARD_H + 8 + off * 2
        L:rect(x, y + fh / 2, fw + 5, 5, col, a)
        L:rect(x, y - fh / 2, fw + 5, 5, col, a)
        L:rect(x - fw / 2, y, 5, fh, col, a)
        L:rect(x + fw / 2, y, 5, fh, col, a)
        local tx = x + (p == 1 and -24 or 24)
        local ty = y + fh / 2 - 12
        UI.slab(L, tx, ty, 58, 26, col, a, 8)
        local tag = p == 1 and '1P' or (self.twoP and '2P' or 'CPU')
        L:label(tag, tx, ty, 58, 26, 16, UI.TEXT, 'c', nil, a)
    end
    -- header (top centre)
    local titles = {arcade = 'ARCADE', versus = self.twoP and 'LOCAL VERSUS' or 'VERSUS CPU', training = 'TRAINING'}
    L:label('选择角色', 0, H / 2 - 56, 400, 56, 40, UI.WHITE, 'c', nil, 1)
    L:label(UI.track(titles[self.mode] or ''), 0, H / 2 - 96, 400, 24, 14, UI.GOLD, 'c', nil, 1)
    L:shape(G.RECT, -150, H / 2 - 96, 7, 7, UI.GOLD, 1, 45)
    L:shape(G.RECT, 150, H / 2 - 96, 7, 7, UI.GOLD, 1, 45)
    -- names
    for p = 1, 2 do
        local side = p == 1 and -1 or 1
        local c = Art.roster[self.cur[p]]
        self.swapT = self.swapT or {0, 0}
        local k = U.ease.outCubic(U.clamp((self.swapT[p] or 0) / 12, 0, 1))
        nameBlock(L, c, side, W, H, (sideOn[p] and 1 or 0) * k, self.done[p], t)
        local fl = self.flash and self.flash[p] or 0
        if fl > 0 then self.flash[p] = fl - 1 end
        local ec = UI.ECOL[c.element] or K.elementColor[c.element]
        L:shape(G.ELLIPSE, side * (W / 2 - 330), -H / 2 + 330, 700, 900, ec, (fl / 16) * 0.55, 0, 0.5)
    end
    -- stage picker
    local sa = (self.phase == 'stage') and 1 or 0
    L:rect(0, 40, W + 40, 230, UI.NAVY, 0.78 * sa)
    L:rect(0, 155, W + 40, 2, UI.GOLD, 0.7 * sa)
    L:rect(0, -75, W + 40, 2, UI.GOLD, 0.4 * sa)
    local st = Stage.order[self.stageI]
    local sname = st and (Paint.available[st] and require('gf_bg_' .. st).name or st) or ''
    local ssub = st and (Paint.available[st] and require('gf_bg_' .. st).sub or '') or ''
    L:label(UI.track('STAGE SELECT') .. ('    %d / %d'):format(self.stageI, #Stage.order), 0, 120, 600, 26, 15, UI.GOLD, 'c', nil, sa)
    L:label(sname, 0, 52, 1000, 90, 64, UI.WHITE, 'c', nil, sa)
    L:label(ssub, 0, -20, 800, 30, 20, UI.GREY, 'c', nil, sa)
    UI.chevron(L, -520 - math.sin(t * 6) * 6, 40, 44, UI.WHITE, sa, -1)
    UI.chevron(L, 520 + math.sin(t * 6) * 6, 40, 44, UI.WHITE, sa, 1)
    UI.tap(L, 'stageL', -520, 40, 160, 160, 'left', sa > 0)
    UI.tap(L, 'stageR', 520, 40, 160, 160, 'right', sa > 0)
    UI.tap(L, 'stageOk', 0, 40, 700, 160, 'ok', sa > 0)
    -- prompts
    UI.prompt(L, W / 2 - 460, -H / 2 + 30, 'J', '确认', 1, 'ok')
    UI.prompt(L, W / 2 - 300, -H / 2 + 30, 'K', '返回', 1, 'back')
    UI.prompt(L, W / 2 - 140, -H / 2 + 30, 'L', '随机', 1, 'alt')
    L:finish()
end

function S:exit()
    for _, b in pairs(self.cards) do b:free() end
    G.release(self.cardsG)
    self.Lback:free()
    self.L:free()
    for _, s in ipairs(self.shows) do s:free() end
end

return S
