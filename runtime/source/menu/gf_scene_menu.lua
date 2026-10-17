__loaders['gf_scene_menu'] = function()
-- Main menu, fighting-game style in Genshin colours: a slanted night-navy slab on the left
-- holds the mode list (big type, numbered, the selected mode sweeps in on a cream slab);
-- a giant ghost word of the selected mode drifts behind; the right side shows a rotating
-- character large with a constellation ring, element badge and name. Streaks keep moving.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Art = require('gf_art')
local Show = require('gf_show')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local MODES = {
    arcade = {en = 'ARCADE', col = {255, 138, 74}},
    versus = {en = 'VERSUS', col = {190, 132, 255}},
    training = {en = 'TRAINING', col = {98, 214, 172}},
    howto = {en = 'MOVES', col = {250, 190, 70}},
    options = {en = 'OPTIONS', col = {120, 196, 245}},
    vcpu = {en = 'VS CPU', col = {190, 132, 255}},
    team = {en = 'TEAM SELECT', col = {190, 132, 255}},
    modes = {en = 'GAME MODE', col = {190,132,255}},
    solo = {en = 'SINGLE PLAYER', col = {190,132,255}},
    net = {en = 'ONLINE', col = {72,186,245}},
    single = {en = 'SINGLE BATTLE', col = {190,132,255}},
    tutorial = {en = 'TUTORIAL', col = {98,214,172}},
    quit = {en = 'EXIT', col = {211,188,142}},
    online = {en = 'ONLINE', col = {72, 186, 245}},
    back = {en = 'BACK', col = {211, 188, 142}},
}

function S.new(app, args)
    local pair=app:getMenuPair()
    local self = setmetatable({app = app, t = 0, showT = 0, showI = pair[1], showPairSlot=1, sub = nil,
                               ghostT = 0}, S)
    local key = Paint.available.mondstadt and 'mondstadt' or next(Paint.available)
    if key then self.bd = app:backdrop(key) end
    self.tier = app.quality == 'lo' and 'lo' or 'hi'
    self.back = G.layer(app.layers.back)
    self.show = Show.new(app.layers.world)
    self.L = G.layer(app.layers.ui)
    self.info = G.layer(app.layers.ui)
    self:mainMenu(args and args.sel)
    self:showChar()
    return self
end

local function menuOpts(self, sel, onPick, onBack)
    local app = self.app
    local main=not self.sub
    return {x = -app.W / 2 + 380, y = app.H / 2 - (main and 270 or 290), w = 560, h = main and 72 or 88, gap = main and 8 or 10, size = main and 34 or 40, sel = sel, numbers = true,
            accent = UI.GOLD, onPick = onPick, onBack = onBack}
end

function S:mainMenu(sel)
    local app = self.app
    if self.menu then self.menu:free() end
    app.input:clearUI()
    self.items = {
        {id = 'solo', label = '单人模式', sub = '单角色对战 · 多角色对战'},
        {id = 'net', label = '联机模式', sub = '单角色对战 · 多角色对战'},
        {id = 'tutorial', label = '教学模式', sub = '基础操作指引'},
        {id = 'training', label = '训练模式', sub = '练习连段与技能'},
        {id = 'howto', label = '出招与系统', sub = '操作、连段、元素战技与爆发'},
        {id = 'options', label = '设置', sub = '震动、难度、回合'},
        {id = 'quit', label = '退出游戏', sub = '服务端结算并关闭游戏界面'},
    }
    self.sub = nil
    self.menu = UI.menu(app, app.layers.ui, self.items, menuOpts(self, sel, function(id) self:pick(id) end))
    self.ghostT = 0
end

function S:modeMenu(kind)
    local app=self.app
    if self.menu then self.menu:free() end
    app.input:clearUI()
    self.items=kind and {
        {id='single',label='单角色对战',sub='选择一名角色 · 三回合两胜'},
        {id='team',label='多角色对战',sub='选择三名角色 · 固定顺序 · 隐藏阵容'},
        {id='back',label='返回'},
    } or {
        {id='solo',label='单人模式',sub='与电脑对战'},
        {id='net',label='联机模式',sub='与同关卡玩家对战'},
        {id='back',label='返回'},
    }
    self.sub=kind or 'modes'
    local function back() self:mainMenu(kind=='net' and 2 or 1) end
    self.menu=UI.menu(app,app.layers.ui,self.items,menuOpts(self,1,function(id)
        if id=='back' then back()
        elseif id=='solo' or id=='net' then self:modeMenu(id)
        elseif id=='single' then
            if kind=='net' then app:travel('online') else app:travel('select',{mode='versus',cpu=true}) end
        elseif id=='team' then
            if kind=='net' then app:travel('online',{teamOnline=true})
            else app:travel('select',{teamPreview=true}) end
        end
    end,back))
    self.ghostT=0
end

function S:tutorialMenu()
    local app=self.app
    self.menu:free();app.input:clearUI()
    self.items={
        {id='howto',label='基础操作',sub='移动、防御、攻击与技能'},
        {id='back',label='返回'},
    }
    self.sub='tutorial'
    self.menu=UI.menu(app,app.layers.ui,self.items,menuOpts(self,1,function(id)
        if id=='back' then self:mainMenu(3) else self:pick(id) end
    end,function()self:mainMenu(3)end))
    self.ghostT=0
end

function S:versusMenu()
    local app = self.app
    self.menu:free()
    app.input:clearUI()
    self.items = {
        {id = 'vcpu', label = '对战电脑', sub = '自选角色与对手'},
        {id = 'team', label = '3v3 选人预览', sub = '原选人布局 · 三人编号标签 · 本地界面预览'},
        {id = 'online', label = '联机对决', sub = '与同一关卡里的另一位玩家对战（回滚联机）'},
        {id = 'back', label = '返回'},
    }
    self.sub = 'versus'
    self.menu = UI.menu(app, app.layers.ui, self.items, menuOpts(self, 1,
        function(id)
            if id == 'back' then self:mainMenu(2)
            elseif id == 'vcpu' then app:travel('select', {mode = 'versus', cpu = true})
            elseif id == 'team' then app:travel('select', {teamPreview=true})
            elseif id == 'online' then app:travel('online')
            end
        end,
        function() self:mainMenu(2) end))
    self.ghostT = 0
end

function S:accent()
    local it = self.items and self.menu and self.items[self.menu.sel]
    local m = it and MODES[it.id]
    return m and m.col or UI.GOLD
end

function S:pick(id)
    local app = self.app
    if id == 'arcade' then app:travel('select', {mode = 'arcade', cpu = true})
    elseif id == 'versus' then self:versusMenu()
    elseif id == 'training' then app:travel('select', {mode = 'training', cpu = false})
    elseif id == 'howto' then app:travel('howto')
    elseif id == 'options' then app:travel('options')
    elseif id == 'modes' then self:modeMenu()
    elseif id == 'solo' or id == 'net' then self:modeMenu(id)
    elseif id == 'tutorial' then self:tutorialMenu()
    elseif id == 'quit' then
        app:quitGame()
    end
end

function S:showChar()
    local app = self.app
    local c = Art.roster[self.showI]
    self.show:set(c.key, self.tier, 'idle', app.W / 2 - 600, -app.H / 2 + 40, 1.75, -1, 0)
    local n = self.show.bmp.node
    local x0 = n.x
    n:pos(x0 + 160, n.y)
    n:tween({anchoredPositionX = x0}, 0.5, 'OutCubic')
    self.showT = 0
    self.infoT = 0
end

function S:tick()
    local app = self.app
    self.t = self.t + 1 / 60
    self.showT = self.showT + 1 / 60
    if self.bd then self.bd:step(300) end
    if self.showT > 6 then
        self.showPairSlot=self.showPairSlot%2+1
        self.showI=app:getMenuPair()[self.showPairSlot]
        self:showChar()
    end
    local acts = app.input:menu()
    for _, a in ipairs(acts) do
        if a == 'back' and not self.sub then app:travel('title') return end
    end
    local before = self.menu.sel
    self.menu:input(acts)
    if self.menu.sel ~= before then self.ghostT = 0 end
    self.menu.o.accent = self:accent()
end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    local t = self.t
    if self.bd then self.bd:draw(0.42, {10, 14, 32}) end
    local acc = self:accent()
    local it = self.items[self.menu.sel]
    local mode = it and MODES[it.id]
    -- background graphics: slab, hairlines, hatch, streaks, ghost word, constellation
    local B = self.back
    B:begin()
    local sx = -W / 2 + 300
    UI.slab(B, sx, 0, 980, H * 1.9, UI.NAVY, 0.86, -UI.SLANT)
    UI.stripes(B, sx - 120, 0, 700, H * 1.9, 18, UI.WHITE, 0.025, -UI.SLANT)
    local ex = sx + 490 / math.cos(math.rad(UI.SLANT))
    UI.slab(B, ex, 0, 3, H * 2, UI.GOLD, 0.75, -UI.SLANT)
    UI.slab(B, ex + 30, 0, 12, H * 2, acc, 0.55, -UI.SLANT)
    UI.slab(B, ex + 64, 0, 3, H * 2, acc, 0.25, -UI.SLANT)
    for i = 1, 9 do
        local sp = 380 + (i % 4) * 170
        local yy = -H / 2 + i * H / 9.5
        local xx = ((t * sp + i * 431) % (W * 0.7 + 600)) - 200
        B:rect(xx, yy, 220 + (i % 3) * 160, i % 3 == 0 and 4 or 2, i % 2 == 0 and UI.WHITE or acc, 0.1, -UI.SLANT)
    end
    -- ghost word of the selected mode: slides in from the right, then drifts
    self.ghostT = self.ghostT + 1 / 60
    local gk = U.ease.outCubic(U.clamp(self.ghostT / 0.5, 0, 1))
    B:label(mode and mode.en or '', W / 2 - 520 + (1 - gk) * 260 - (t * 6) % 40, H / 2 - 250, 1600, 300, 220, UI.WHITE, 'c', nil, 0.07 * gk)
    UI.constellation(B, W / 2 - 600, -H / 2 + 330, 290, t * 6, UI.WHITE, 0.9)
    B:shape(G.ELLIPSE, W / 2 - 600, -H / 2 + 260, 700, 700, acc, 0.16, 0, 0.5)
    B:finish()
    -- logo, prompts
    local L = self.L
    L:begin()
    L:shape(G.STAR4, -W / 2 + 104, H / 2 - 96, 40, 40, UI.WHITE, 1, t * 20)
    L:label('原神格斗', -W / 2 + 338, H / 2 - 90, 420, 70, 54, UI.WHITE, 'l', nil, 1)
    L:label(UI.track('GENSHIN FIGHTER'), -W / 2 + 338, H / 2 - 138, 420, 26, 15, UI.GOLD, 'l', nil, 1)
    L:rect(-W / 2 + 330, H / 2 - 162, 400, 2, UI.GOLD, 0.6)
    local subtitles={versus='对战模式',modes='模式选择',solo='单人模式',net='联机模式',tutorial='教学模式'}
    L:label(subtitles[self.sub] or '', -W / 2 + 338, H / 2 - 196, 420, 28, 20, acc, 'l', nil, 1)
    UI.prompt(L, -W / 2 + 120, -H / 2 + 50, 'J', '确认', 1, 'ok')
    UI.prompt(L, -W / 2 + 290, -H / 2 + 50, 'K', '返回', 1, 'back')
    local menuKey=app:isMobile() and '≡' or app.input:device()=='pad' and '技3' or 'P'
    UI.prompt(L, -W / 2 + 460, -H / 2 + 50, menuKey, '战斗菜单', 1)
    L:finish()
    self.menu:draw(1)
    -- showcase: name block bottom-right
    local I = self.info
    self.infoT = (self.infoT or 0) + 1
    local a = U.ease.outCubic(U.clamp(self.infoT / 22, 0, 1))
    local c = Art.roster[self.showI]
    local ec = UI.ECOL[c.element] or K.elementColor[c.element]
    I:begin()
    local rx = W / 2 - 90
    local ny = -H / 2 + 220
    I:shape(G.ELLIPSE, rx - 260, ny - 40, 900, 380, UI.NAVY, 0.55 * a, 0, 0.5)
    I:label(K.en[c.key] and UI.track(K.en[c.key]:upper()) or '', rx - 300 + (1 - a) * 60, ny + 70, 600, 26, 16, UI.GOLD, 'r', nil, a)
    I:label(c.name, rx - 360 + (1 - a) * 120, ny + 6, 720, 110, 88, UI.WHITE, 'r', nil, a)
    I:rect(rx - 220, ny - 58, 440 * a, 2, ec, 0.9 * a)
    UI.badge(I, c.element, rx - 60 - (utf8.len(c.name) or 3) * 88 - 50, ny + 6, 64, a)
    I:label((K.title[c.key] or '') .. '　·　' .. (K.weaponName[c.weapon] or ''), rx - 300, ny - 88, 600, 30, 20, UI.GREY, 'r', nil, a)
    I:label('E  ' .. c.skill .. '　　Q  ' .. c.burst, rx - 300, ny - 124, 600, 26, 17, UI.CREAM, 'r', nil, a * 0.85)
    I:finish()
end

function S:exit()
    self.menu:free()
    self.back:free()
    self.L:free()
    self.info:free()
    self.show:free()
end

return S
end
