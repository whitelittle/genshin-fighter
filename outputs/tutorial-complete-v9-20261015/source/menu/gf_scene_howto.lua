__loaders['gf_scene_howto'] = function()
-- Four device-specific pages: controls, combos, skills and advanced inputs.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local function pagesFor(app)
 local dev=app.input:device()
 local mobile=dev=='touch';local pad=dev=='pad'
 local p=app.input.controllerLayout
 local light=mobile and '轻按钮' or pad and p.light or 'J'
 local heavy=mobile and '重按钮' or pad and p.heavy or 'K'
 local skill=mobile and 'E按钮' or pad and p.skill or 'E'
 local burst=mobile and 'Q按钮' or pad and p.burst or 'Q'
 return {
  {title='基础操作',lines={
   {'移动 / 跳跃',mobile and '摇杆移动；点跳按钮起跳' or pad and '左摇杆移动；'..p.jump..' 跳跃' or 'A / D 左右；W或空格跳跃；S蹲下'},
   {'防御','按住远离对手的方向；后下为蹲防'},
   {'轻攻击',light..' · 可接后续轻攻；蹲下可出蹲轻'},
   {'重攻击',heavy..' · 角色重攻；蹲下可出蹲重'},
   {'元素战技',skill..' · 冷却结束后发动'},
   {'元素爆发',burst..' · 能量满时发动'},
   {'冲刺',mobile and '冲按钮；按住后方向可后撤' or pad and p.dash..'；后方向＋冲刺为后撤' or 'U；后方向＋U为后撤'},
   {'投技',mobile and '近身前方向＋重按钮' or pad and p.throw..'；需近身且目标可投' or 'L；需近身且目标可投'},
  }},
  {title='连段规则',lines={
   {'轻攻连段','连续轻攻可接下一段，招式随角色不同'},
   {'取消窗口','命中或被防后，在允许窗口接后续招式'},
   {'技能衔接','战技 / 爆发需满足资源与当前动作条件'},
   {'空中招式','起跳后可出空轻 / 空重，动作随角色不同'},
   {'伤害递减','同一连段越长，后续伤害越低'},
   {'练习入口','主菜单进入训练，分别选择自己与陪练'},
  }},
  {title='元素技能',lines={
   {'元素战技',skill..' · 有冷却，效果与范围随角色不同'},
   {'元素爆发',burst..' · 需要满能量；发动时消耗能量'},
   {'命中确认','满足首击命中条件后，进入完整爆发演出'},
   {'未命中','取消后续演出并收招，已消耗能量不退回'},
   {'被防住','显示格挡提示，按角色防御分支处理'},
   {'命中限制','距离、朝向、有效时间与对手无敌状态都会影响命中'},
   {'失败提示','能量不足 / 战技冷却中 / 当前动作不能释放'},
  }},
  {title='进阶操作',lines={
   {'战技备用',mobile and '使用E按钮；方向指令放在后续招式教学' or pad and '使用 '..p.skill..'；可配合方向输入' or 'I也可发动战技；默认主键为E'},
   {'爆发备用',mobile and '使用Q按钮' or pad and '使用 '..p.burst or 'O也可发动爆发；默认主键为Q'},
   {'方向指令','↓↘→＋攻击为进阶战技输入'},
   {'近身投技','前方向＋重攻；对手状态不允许时会落空'},
   {'打开菜单',mobile and '点画面上方菜单按钮' or pad and p.pause..'；平台技能3绑定此键' or 'P打开战斗菜单'},
   {'连段示例','实际能否衔接取决于角色、距离和取消窗口'},
  }},
 }
end

function S.new(app)
    local self = setmetatable({app = app, page = 1, t = 0, pt = 0}, S)
    local key = Paint.available.liyue and 'liyue' or next(Paint.available)
    if key then self.bd = app:backdrop(key) end
    self.L = G.layer(app.layers.ui)
    self.pages=pagesFor(app);self.device=app.input:device()
    return self
end

function S:tick()
    local app = self.app
    self.t = self.t + 1 / 60
    self.pt = self.pt + 1 / 60
    if self.device~=app.input:device() then self.device=app.input:device();self.pages=pagesFor(app) end
    if self.bd then self.bd:step(300) end
    for _, a in ipairs(app.input:menu()) do
        local direct=type(a)=='string' and tonumber(a:match('^howto:(%d+)$'))
        if direct and direct>=1 and direct<=#self.pages then self.page=direct;self.pt=0;app.audio:play(app.audio.ID.move)
        elseif a == 'left' then self.page = (self.page - 2) % #self.pages + 1; self.pt = 0; app.audio:play(app.audio.ID.move)
        elseif a == 'right' or a == 'ok' then self.page = self.page % #self.pages + 1; self.pt = 0; app.audio:play(app.audio.ID.move)
        elseif a == 'back' then app:travel('menu', {sel = 4}) end
    end
end

local EN = {'CONTROLS', 'COMBOS', 'SKILLS', 'ADVANCED'}

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
    for i, pg in ipairs(self.pages) do
        local tx = -W / 2 + 550 + (i - 1) * 250
        local on = i == self.page
        UI.slab(L, tx, H / 2 - 100, 210, 56, on and UI.CREAM or UI.NAVY, on and 0.96 or 0.7, 6)
        L:label(pg.title, tx, H / 2 - 92, 210, 40, 24, on and UI.TEXT or UI.WHITE, 'c', nil, on and 1 or 0.7)
        L:label(EN[i], tx, H / 2 - 118, 210, 20, 11, on and {110, 116, 136} or UI.GOLD, 'c', nil, on and 1 or 0.6)
        UI.tap(L, 'tab' .. i, tx, H / 2 - 100, 210, 60, 'howto:'..i, i ~= self.page)
    end
    -- rows: gold label, white text, hairline
    local pg = self.pages[self.page]
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
    local mobile=app.input:device()=='touch'
    local pad=app.input:device()=='pad'
    if pad then L:label('推荐布局：Xbox / PlayStation；平台绑定需对应设置',0,-H/2+80,1300,30,19,UI.GOLD,'c') end
    UI.prompt(L, W / 2 - 460, -H / 2 + 40, mobile and '‹' or pad and '←' or 'A', '上一页', 1, 'left')
    UI.prompt(L, W / 2 - 300, -H / 2 + 40, mobile and '›' or pad and '→' or 'D', '下一页', 1, 'right')
    UI.prompt(L, W / 2 - 140, -H / 2 + 40, mobile and '返' or pad and 'B/○' or 'K', '返回', 1, 'back')
    L:finish()
end

function S:exit() self.L:free() end

return S
end
