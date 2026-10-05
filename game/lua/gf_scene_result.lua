-- Results, fighting-game style: the winner large in a victory pose on the left over an
-- element slab; on the right a slanted panel with VICTORY, the winner's name huge, the score,
-- hairline stat rows counting up, and the next step (rematch / next arcade fight / menu).
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Art = require('gf_art')
local Show = require('gf_show')
local Paint = require('gf_paint')

local S = {}
S.__index = S

function S.new(app, res)
    local self = setmetatable({app = app, res = res, t = 0}, S)
    local fa = res.args or {}
    local st = fa.stage and Paint.available[fa.stage] and fa.stage or (Paint.available.mondstadt and 'mondstadt' or next(Paint.available))
    if st then self.bd = app:backdrop(st) end
    self.win = res.winner
    local wkey = res.chars[self.win or 1]
    self.show = Show.new(app.layers.world)
    self.show:set(wkey, app.quality == 'lo' and 'lo' or 'hi', self.win and 'special' or 'hurt', -app.W / 2 + 430, -app.H / 2 + 60, 1.7, 1, 0)
    self.back = G.layer(app.layers.back)
    self.L = G.layer(app.layers.ui)
    self.arcade = fa.arcade
    local items
    local humanWon = self.win == 1 or (fa.cpu and not fa.cpu[1] and not fa.cpu[2] and self.win ~= nil)
    if self.arcade then
        if self.win == 1 then
            self.arcade.score = self.arcade.score + 1000 + (res.stats[1].maxCombo or 0) * 50
            if self.arcade.step >= #self.arcade.ladder then
                self.cleared = true
                items = {{id = 'menu', label = '返回主菜单', sub = '七国之巅，已经登顶'}}
            else
                items = {{id = 'next', label = '下一战', sub = ('第 %d / %d 战'):format(self.arcade.step + 1, #self.arcade.ladder)},
                         {id = 'menu', label = '返回主菜单'}}
            end
        else
            items = {{id = 'retry', label = '再次挑战', sub = '从这一战重新开始'}, {id = 'menu', label = '返回主菜单'}}
        end
    elseif res.mode == 'online' then
        local won = self.win == res.side
        items = {{id = 'lobby', label = '返回联机大厅', sub = won and '胜利！对手可以在大厅里再次准备' or '在大厅里准备，再战一局'},
                 {id = 'menu', label = '返回主菜单'}}
    else
        items = {{id = 'again', label = '再战一局'}, {id = 'select', label = '重新选择角色'}, {id = 'menu', label = '返回主菜单'}}
    end
    self.menu = UI.menu(app, app.layers.ui, items, {x = app.W / 2 - 340, y = -170, w = 460, h = 64, gap = 8, size = 28,
        accent = UI.ECOL[(Art.byKey[wkey] or {}).element] or UI.GOLD,
        onPick = function(id) self:pick(id) end})
    app.audio:play(self.win == 1 and app.audio.ID.okBig or app.audio.ID.close)
    return self
end

function S:pick(id)
    local app = self.app
    local fa = self.res.args or {}
    if id == 'menu' then app:travel('menu')
    elseif id == 'lobby' then app:travel('online')
    elseif id == 'again' then app:travel('vs', fa)
    elseif id == 'select' then app:travel('select', {mode = fa.mode == 'arcade' and 'arcade' or fa.mode, cpu = fa.cpu and fa.cpu[2] and true or false})
    elseif id == 'next' then
        self.arcade.step = self.arcade.step + 1
        app:travel('vs', {arcade = self.arcade})
    elseif id == 'retry' then app:travel('vs', {arcade = self.arcade})
    end
end

function S:tick()
    self.t = self.t + 1 / 60
    if self.bd then self.bd:step(300) end
    self.menu:input(self.app.input:menu())
end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    if self.bd then self.bd:draw(0.5, {10, 14, 32}) end
    local t = self.t
    local k = U.ease.outCubic(U.clamp(t / 0.5, 0, 1))
    local res = self.res
    local wch = self.win and Art.byKey[res.chars[self.win]]
    local ec = wch and (UI.ECOL[wch.element] or K.elementColor[wch.element]) or UI.GOLD
    -- background: winner slab on the left, navy panel on the right, streaks, constellation
    local B = self.back
    B:begin()
    UI.slab(B, -W / 2 + 330 - (1 - k) * 600, 0, 760, H * 1.9, U.mix(ec, UI.NAVY, 0.7), 0.7, UI.SLANT)
    UI.stripes(B, -W / 2 + 330 - (1 - k) * 600, 0, 620, H * 1.9, 16, UI.WHITE, 0.03, UI.SLANT)
    UI.slab(B, W / 2 - 300 + (1 - k) * 700, 0, 900, H * 1.9, UI.NAVY, 0.84, UI.SLANT)
    local ex = W / 2 - 300 - 450 / math.cos(math.rad(UI.SLANT)) + (1 - k) * 700
    UI.slab(B, ex, 0, 3, H * 2, UI.GOLD, 0.8, UI.SLANT)
    UI.slab(B, ex - 28, 0, 12, H * 2, ec, 0.6, UI.SLANT)
    UI.constellation(B, -W / 2 + 430, -H / 2 + 330, 300, t * 6, UI.WHITE, 0.8)
    B:shape(G.ELLIPSE, -W / 2 + 430, -H / 2 + 300, 760, 760, ec, 0.22, 0, 0.5)
    for i = 1, 7 do
        local yy = -H / 2 + i * H / 7.5
        local xx = ((t * (420 + (i % 3) * 200) + i * 300) % (W + 600)) - W / 2 - 300
        B:rect(xx, yy, 240 + (i % 3) * 120, 2, i % 2 == 0 and UI.WHITE or ec, 0.1, UI.SLANT)
    end
    B:label(self.win and 'VICTORY' or 'DRAW', -W / 2 + 520, H / 2 - 120, 1400, 260, 210, UI.WHITE, 'l', nil, 0.07 * k)
    B:finish()
    -- right panel: title block
    local L = self.L
    L:begin()
    local px = W / 2 - 340
    local ty = H / 2 - 130
    local head = self.cleared and 'CHALLENGE CLEAR' or (self.win == nil and 'DRAW GAME' or 'VICTORY')
    local nm = self.cleared and '挑战完成' or (self.win == nil and '平局' or wch.name)
    L:label(UI.track(head), px, ty + 70, 520, 28, 18, UI.GOLD, 'l', nil, k)
    local n = L:label(nm, px + (1 - k) * 80, ty + 4, 520, 110, 92, UI.WHITE, 'l', nil, k)
    if wch then UI.badge(L, wch.element, px - 260 + (utf8.len(nm) or 3) * 92 + 56, ty + 4, 60, k) end
    L:rect(px, ty - 54, 520 * k, 3, ec, k)
    L:label(self.arcade and ('街机得分　%d'):format(self.arcade.score) or ('比分　%d : %d'):format(res.wins[1], res.wins[2]),
            px, ty - 84, 520, 30, 22, UI.CREAM, 'l', nil, k)
    -- stats: hairline rows, numbers count up
    local st = res.stats[self.win or 1]
    local rows = {{'最大连击', st.maxCombo}, {'造成伤害', st.damage}, {'元素反应', st.reactions}, {'元素爆发', st.bursts}, {'成功防御', st.blocks}}
    for i, r in ipairs(rows) do
        local y = ty - 140 - (i - 1) * 40
        local a = U.ease.outCubic(U.clamp((t - 0.25 - i * 0.06) / 0.3, 0, 1))
        local v = r[2] or 0
        local shown = math.floor(v * U.clamp((t - 0.35 - i * 0.06) / 0.6, 0, 1) + 0.5)
        L:label(r[1], px + (1 - a) * 40, y, 520, 36, 20, UI.GREY, 'l', nil, a)
        L:label(tostring(shown), px + (1 - a) * 40, y, 520, 36, 24, UI.WHITE, 'r', nil, a)
        L:rect(px, y - 19, 520, 1, UI.WHITE, 0.14 * a)
    end
    UI.prompt(L, W / 2 - 300, -H / 2 + 40, 'J', '确认', 1, 'ok')
    L:finish()
    self.menu:draw(k)
end

function S:exit()
    self.show:free()
    self.back:free()
    self.L:free()
    self.menu:free()
end

return S
