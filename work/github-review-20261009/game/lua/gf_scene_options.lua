-- Settings: quality, screen shake, sound, CPU level, rounds to win, round time, touch buttons.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local function cycle(list, cur, d)
    local i = 1
    for k, v in ipairs(list) do if v == cur then i = k end end
    return list[(i - 1 + d) % #list + 1]
end

function S.new(app)
    local self = setmetatable({app = app, t = 0}, S)
    local key = Paint.available.mondstadt and 'mondstadt' or next(Paint.available)
    if key then self.bd = app:backdrop(key) end
    local st = app.settings
    local QN = {auto = '自动', hi = '高', lo = '低（手机推荐）'}
    local CN = {'简单', '普通', '困难', '噩梦'}
    local TN = {[60] = '60 秒', [99] = '99 秒', [999] = '不限时'}
    local items = {
        {id = 'quality', label = '画质', value = function() return QN[st.quality] end,
         left = function() st.quality = cycle({'auto', 'hi', 'lo'}, st.quality, -1); app.quality = app:detectQuality() end,
         right = function() st.quality = cycle({'auto', 'hi', 'lo'}, st.quality, 1); app.quality = app:detectQuality() end},
        {id = 'shake', label = '屏幕震动', value = function() return st.shake and '开' or '关' end,
         left = function() st.shake = not st.shake end, right = function() st.shake = not st.shake end},
        {id = 'sfx', label = '音效', value = function() return st.sfx and '开' or '关' end,
         left = function() st.sfx = not st.sfx; app.audio.on = st.sfx end, right = function() st.sfx = not st.sfx; app.audio.on = st.sfx end},
        {id = 'cpu', label = '电脑难度', value = function() return CN[st.cpu] end,
         left = function() st.cpu = (st.cpu - 2) % 4 + 1 end, right = function() st.cpu = st.cpu % 4 + 1 end},
        {id = 'rounds', label = '获胜局数', value = function() return st.rounds .. ' 局' end,
         left = function() st.rounds = (st.rounds - 2) % 3 + 1 end, right = function() st.rounds = st.rounds % 3 + 1 end},
        {id = 'time', label = '回合时间', value = function() return TN[st.time] end,
         left = function() st.time = cycle({60, 99, 999}, st.time, -1) end, right = function() st.time = cycle({60, 99, 999}, st.time, 1) end},
        {id = 'touch', label = '触屏按键', value = function() return ({auto = '自动', on = '开', off = '关'})[st.touch] end,
         left = function() st.touch = cycle({'auto', 'on', 'off'}, st.touch, -1) end, right = function() st.touch = cycle({'auto', 'on', 'off'}, st.touch, 1) end},
        {id = 'back', label = '返回'},
    }
    self.items = items
    self.L = G.layer(app.layers.ui)            -- under the menu
    self.menu = UI.menu(app, app.layers.ui, items, {x = -app.W / 2 + 380, y = app.H / 2 - 260, w = 560, h = 64, gap = 6, size = 30,
        accent = {120, 196, 245},
        onPick = function(id) if id == 'back' then app:travel('menu', {sel = 5}) end end,
        onBack = function() app:travel('menu', {sel = 5}) end})
    return self
end

function S:tick()
    self.t = self.t + 1 / 60
    if self.bd then self.bd:step(300) end
    self.menu:input(self.app.input:menu())
end

local INFO = {
    quality = {'QUALITY', '画质', '自动：手机用低画质、电脑用高画质。低画质减少角色与背景的图元数量，帧率更稳。'},
    shake = {'SCREEN SHAKE', '屏幕震动', '重击、元素爆发与击倒时的镜头震动。'},
    sfx = {'SOUND', '音效', '游戏内音效开关。'},
    cpu = {'CPU LEVEL', '电脑难度', '对战电脑时对手的反应速度、防御与连段长度。'},
    rounds = {'ROUNDS', '获胜局数', '先赢下这么多回合的一方获胜。'},
    time = {'TIME', '回合时间', '时间到时，剩余体力比例高的一方赢下回合。'},
    touch = {'TOUCH', '触屏按键', '自动：只在手机上显示屏幕按键。'},
    back = {'BACK', '返回', '回到主菜单。'},
}

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    self.t = self.t
    if self.bd then self.bd:draw(0.5, {10, 14, 32}) end
    local L = self.L
    local k = U.ease.outCubic(U.clamp(self.t / 0.4, 0, 1))
    local it = self.items[self.menu.sel]
    local inf = INFO[it.id] or INFO.back
    if self.lastSel ~= self.menu.sel then self.lastSel, self.infoT = self.menu.sel, 0 end
    self.infoT = (self.infoT or 0) + 1
    local ik = U.ease.outCubic(U.clamp(self.infoT / 12, 0, 1))
    L:begin()
    UI.leftPanel(L, W, H, k, {120, 196, 245}, 1)
    UI.screenTitle(L, W, H, '设置', UI.track('OPTIONS'), k)
    -- right: the selected setting, large
    local rx = W / 2 - 420
    L:label(inf[1], rx + 140 + (1 - ik) * 80, H / 2 - 220, 1200, 200, 150, UI.WHITE, 'c', nil, 0.06 * ik)
    L:label(UI.track(inf[1]), rx, 120, 640, 26, 15, UI.GOLD, 'l', nil, ik)
    L:label(inf[2], rx + (1 - ik) * 40, 64, 640, 80, 60, UI.WHITE, 'l', nil, ik)
    L:rect(rx - 120, 10, 400 * ik, 2, {120, 196, 245}, ik)
    L:label(it.value and it.value() or '', rx, -40, 640, 60, 40, UI.CREAM, 'l', nil, it.value and ik or 0)
    L:label(inf[3], rx, -120, 640, 90, 20, UI.GREY, 'l', nil, ik)
    UI.prompt(L, -W / 2 + 120, -H / 2 + 50, 'J', '确认', 1, 'ok')
    UI.prompt(L, -W / 2 + 290, -H / 2 + 50, 'K', '返回', 1, 'back')
    UI.prompt(L, -W / 2 + 460, -H / 2 + 50, 'A', '调整', 1, 'left')
    L:finish()
    self.menu:draw(1)
end

function S:exit()
    self.menu:free()
    self.L:free()
end

return S
