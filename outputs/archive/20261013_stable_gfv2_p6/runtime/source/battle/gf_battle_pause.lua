__loaders['gf_battle_pause']=function()
local G = require('gf_gfx')
local Art = require('gf_art')
local K = require('gf_kits')
local U = require('gf_util')
local Sim = require('gf_sim')
local AI = require('gf_ai')
local FView = require('gf_fview')
local FX = require('gf_fx')
local Hud = require('gf_hud')
local Stage = require('gf_stage')
local UI = require('gf_ui')
local Online = require('gf_online')


local C=Sim.C
return function(S)
function S:openPause()
    local app = self.app
    self.paused = true
    self.pauseT = 0
    app.input:clearUI()
    if self.touch then self.touch.L:clear() end
    app.audio:play(app.audio.ID.open)
    self.pauseL = self.pauseL or G.layer(app.layers.ui)
    local items = {
        {id = 'resume', label = '继续战斗'},
        {id = 'moves', label = '出招表'},
        {id = 'restart', label = '重新开始'},
    }
    if self.mode == 'training' then
        local dummies = {'stand', 'block', 'crouch', 'cblock', 'jump', 'cpu'}
        local dn = {stand = '站立', block = '站立防御', crouch = '蹲下', cblock = '蹲下防御', jump = '跳跃', cpu = 'CPU 对打'}
        self.dummy = self.dummy or 'stand'
        table.insert(items, 2, {id = 'dummy', label = '陪练', value = function() return dn[self.dummy] end,
            left = function() local i = 1 for k, v in ipairs(dummies) do if v == self.dummy then i = k end end self.dummy = dummies[(i - 2) % #dummies + 1]; self:trainingAI() end,
            right = function() local i = 1 for k, v in ipairs(dummies) do if v == self.dummy then i = k end end self.dummy = dummies[i % #dummies + 1]; self:trainingAI() end})
        table.insert(items, 3, {id = 'energy', label = '元素能量', value = function() return self.sim.opts.infinite and '无限' or '正常' end,
            left = function() self.sim.opts.infinite = not self.sim.opts.infinite end, right = function() self.sim.opts.infinite = not self.sim.opts.infinite end})
    end
    if self.online then
        items = {{id = 'resume', label = '继续战斗'}, {id = 'moves', label = '出招表'}, {id = 'leave', label = '离开对战'}}
    else
        items[#items + 1] = {id = 'select', label = '重新选择角色'}
        items[#items + 1] = {id = 'quit', label = '返回主菜单'}
    end
    local ec = UI.ECOL[self.sim.f[self.side or 1].element] or UI.GOLD
    self.pauseMenu = UI.menu(app, app.layers.ui, items, {x = -app.W / 2 + 380, y = app.H / 2 - 290, w = 520, h = 70, gap = 8, size = 32,
        numbers = true, accent = ec,
        onPick = function(id) self:pausePick(id) end, onBack = function() self:closePause() end})
end

function S:trainingAI()
    if self.dummy == 'cpu' then self.ai[2] = AI.new(self.sim, 2, 2, 51) else self.ai[2] = nil end
end

function S:closePause()
    self.paused = false
    if self.pauseMenu then self.pauseMenu:free(); self.pauseMenu = nil end
    if self.pauseL then self.pauseL:clear() end
    self.app.input:clearUI()
    self.showMoves = nil
    self:touchControls()
end

function S:pausePick(id)
    local app = self.app
    if id == 'resume' then self:closePause()
    elseif id == 'moves' then self.showMoves = not self.showMoves
    elseif id == 'leave' then
        Online.leaveMatch(self.online)
        self.online.onFrame = nil
        app:travel('online')
    elseif id == 'restart' then app:travel('fight', self.args)
    elseif id == 'select' then app:travel('select', {mode = self.mode == 'demo' and 'versus' or self.mode, cpu = self.args.cpu and self.args.cpu[2] and true or false})
    elseif id == 'quit' then app:travel('menu')
    end
end

function S:drawPause()
    local app = self.app
    local W, H = app.W, app.H
    local L = self.pauseL
    local f = self.sim.f[self.side or 1]
    local ec = UI.ECOL[f.element] or K.elementColor[f.element]
    self.pauseT = (self.pauseT or 0) + 1
    local k = U.ease.outCubic(U.clamp(self.pauseT / 12, 0, 1))
    L:begin()
    self.app:cover(L,{4,6,14},0.55*k)
    -- left slab with the menu
    UI.leftPanel(L, W, H, k, ec, k)
    UI.screenTitle(L, W, H, '暂停', UI.track('PAUSE') .. (self.online and '　·　联机对局不会暂停' or ''), k)
    -- move list: right slanted panel with hairline rows
    local ma = self.showMoves and k or 0
    local px = W / 2 - 420
    UI.slab(L, px + 40, 0, 900, H * 1.9, UI.NAVY, 0.92 * ma, -UI.SLANT)
    UI.slab(L, px + 40 - 450 / math.cos(math.rad(UI.SLANT)), 0, 3, H * 2, UI.GOLD, 0.7 * ma, -UI.SLANT)
    if self.showMoves then
    local rows = {
        {'移动', 'W A S D　·　W / 空格 跳跃　·　双击前冲刺'},
        {'防御', '按住后方向（蹲防：后下）'},
        {'轻攻击', 'J　连按三段　·　↓J 下段'},
        {'重攻击', 'K　挑空　·　↓K 扫腿'},
        {'元素战技', 'E / I / E 按钮 / ↓↘→ + 攻击　「' .. f.char.skill .. '」'},
        {'元素爆发', 'Q / O 键 / Q 按钮　能量满时　「' .. f.char.burst .. '」'},
        {'冲刺 / 投技', 'U 冲刺（后 + U 后撤）　·　L 或 →K 投'},
        {'基本连段', 'J → J → J → K → E → Q'},
    }
    L:label(f.char.name, px + 120, H / 2 - 110, 560, 60, 44, UI.WHITE, 'l', nil, ma)
    L:label(UI.track('COMMAND LIST'), px + 120, H / 2 - 156, 560, 24, 14, UI.GOLD, 'l', nil, ma)
    UI.badge(L, f.element, px - 210, H / 2 - 112, 52, ma)
    for i, r in ipairs(rows) do
        local y = H / 2 - 220 - (i - 1) * 58
        L:label(r[1], px - 150, y, 180, 50, 20, ec, 'l', nil, ma)
        L:label(r[2], px + 170, y, 560, 50, 19, UI.WHITE, 'l', nil, ma)
        L:rect(px + 40, y - 27, 700, 1, UI.WHITE, 0.14 * ma)
    end
    end
    L:finish()
    if self.pauseMenu then self.pauseMenu:draw(k) end
end

------------------------------------------------------------------ main

end
end
