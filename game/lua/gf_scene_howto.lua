-- Moves and systems: four pages (controls, combos, elemental reactions, bursts), left / right.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local PAGES = {
    {title = '操作', lines = {
        {'移动', 'A / D 左右，W 或 空格 跳跃，S 蹲下'},
        {'防御', '按住后方向（蹲防：后下）'},
        {'轻攻击', 'J　连按三段；蹲下时为下段攻击'},
        {'重攻击', 'K　挑空，可接空中连段；蹲下时为扫腿'},
        {'元素战技', 'L　或 ↓↘→ + 攻击；有冷却'},
        {'元素爆发', 'I　能量满时释放，带特写演出'},
        {'冲刺 / 投技', 'U 冲刺（按住后方向为后撤步）　O 或 →+K 近身投'},
        {'手柄', '普攻＝轻　交互＝重　技能1＝战技　技能2＝爆发　冲刺＝冲刺'},
    }},
    {title = '连段', lines = {
        {'取消', '攻击命中或被防后，可立刻接下一招'},
        {'基本连段', 'J → J → J → K → L → I'},
        {'下段起手', '↓J → ↓J → ↓K（击倒）'},
        {'空中连段', 'K 挑空 → 跳 → J → K（下砸）'},
        {'伤害递减', '连段越长，后续伤害越低'},
        {'倒地', '被击倒后短暂无敌，起身后再战'},
    }},
    {title = '元素反应', lines = {
        {'元素附着', '施放元素战技或爆发后，自身短时间附着元素'},
        {'触发', '附着期间被异元素击中，触发反应'},
        {'蒸发 / 融化', '水火、冰火：本次伤害 ×1.5'},
        {'超载', '雷火：爆炸击飞'},
        {'冻结', '水冰：冻住片刻，再被击中解除'},
        {'感电 / 燃烧 / 绽放', '持续伤害或延迟爆炸'},
        {'扩散 / 结晶', '风：额外伤害与击退；岩：攻击者获得护盾'},
    }},
    {title = '元素爆发', lines = {
        {'能量', '命中、被击中与施放战技都会积累能量'},
        {'释放', '能量满后按 I，进入角色特写，期间无敌'},
        {'连段收尾', '重攻击或战技命中后可直接取消接爆发'},
        {'防御', '爆发可以被防住，但会削减较多体力'},
    }},
}

function S.new(app)
    local self = setmetatable({app = app, page = 1, t = 0, pt = 0}, S)
    local key = Paint.available.liyue and 'liyue' or next(Paint.available)
    if key then self.bd = app:backdrop(key) end
    self.L = G.layer(app.layers.ui)
    return self
end

function S:tick()
    local app = self.app
    self.t = self.t + 1 / 60
    self.pt = self.pt + 1 / 60
    if self.bd then self.bd:step(300) end
    for _, a in ipairs(app.input:menu()) do
        if a == 'left' then self.page = (self.page - 2) % #PAGES + 1; self.pt = 0; app.audio:play(app.audio.ID.move)
        elseif a == 'right' or a == 'ok' then self.page = self.page % #PAGES + 1; self.pt = 0; app.audio:play(app.audio.ID.move)
        elseif a == 'back' then app:travel('menu', {sel = 4}) end
    end
end

local EN = {'CONTROLS', 'COMBOS', 'REACTIONS', 'BURSTS'}

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    if self.bd then self.bd:draw(0.68, {10, 14, 32}) end
    local L = self.L
    local k = U.ease.outCubic(U.clamp(self.t / 0.4, 0, 1))
    local pk = U.ease.outCubic(U.clamp(self.pt / 0.3, 0, 1))
    local acc = {250, 190, 70}
    L:begin()
    UI.leftPanel(L, W, H, k, acc, 0.5)
    UI.screenTitle(L, W, H, '出招与系统', UI.track('HOW TO PLAY'), k)
    -- tabs across the top right
    for i, pg in ipairs(PAGES) do
        local tx = -W / 2 + 820 + (i - 1) * 230
        local on = i == self.page
        UI.slab(L, tx, H / 2 - 100, 210, 56, on and UI.CREAM or UI.NAVY, on and 0.96 or 0.7, 6)
        L:label(pg.title, tx, H / 2 - 92, 210, 40, 24, on and UI.TEXT or UI.WHITE, 'c', nil, on and 1 or 0.7)
        L:label(EN[i], tx, H / 2 - 118, 210, 20, 11, on and {110, 116, 136} or UI.GOLD, 'c', nil, on and 1 or 0.6)
        UI.tap(L, 'tab' .. i, tx, H / 2 - 100, 210, 60, i < self.page and 'left' or 'right', i ~= self.page)
    end
    -- rows: gold label, white text, hairline
    local pg = PAGES[self.page]
    L:label(EN[self.page], W / 2 - 520, -H / 2 + 120, 1400, 220, 170, UI.WHITE, 'c', nil, 0.05 * pk)
    for i = 1, 8 do
        local ln = pg.lines[i]
        local y = H / 2 - 230 - (i - 1) * 74
        local a = ln and U.ease.outCubic(U.clamp((self.pt - i * 0.04) / 0.25, 0, 1)) or 0
        local x = -W / 2 + 140 + (1 - a) * 60
        L:shape(G.RECT, x - 30, y, 10, 10, acc, a, 45)
        L:label(ln and ln[1] or '', x + 120, y, 240, 60, 26, acc, 'l', nil, a)
        L:label(ln and ln[2] or '', x + 300 + 420, y, 840, 60, 22, UI.WHITE, 'l', nil, a)
        L:rect(x + 600, y - 37, 1200, 1, UI.WHITE, 0.12 * a)
    end
    UI.prompt(L, W / 2 - 460, -H / 2 + 40, 'A', '上一页', 1, 'left')
    UI.prompt(L, W / 2 - 300, -H / 2 + 40, 'D', '下一页', 1, 'right')
    UI.prompt(L, W / 2 - 140, -H / 2 + 40, 'K', '返回', 1, 'back')
    L:finish()
end

function S:exit() self.L:free() end

return S
