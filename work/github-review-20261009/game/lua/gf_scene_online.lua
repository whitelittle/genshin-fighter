-- Online lobby: two players in the same level meet here. Left / right picks your character,
-- J readies up, the host (lowest relay slot) also picks the stage with up / down. When both
-- are ready the host announces the match; both sides go through the VS screen into the fight
-- with the rollback session (gf_online / gf_net) already created.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local K = require('gf_kits')
local Art = require('gf_art')
local Show = require('gf_show')
local Stage = require('gf_stage')
local Paint = require('gf_paint')
local O = require('gf_online')

local S = {}
S.__index = S

local function stageName(key)
    if Paint.available[key] then return require('gf_bg_' .. key).name end
    return key or ''
end

function S.new(app)
    local self = setmetatable({app = app, t = 0, msg = nil, msgT = 0}, S)
    local key = Paint.available.fontaine and 'fontaine' or next(Paint.available)
    if key then self.bd = app:backdrop(key) end
    self.net = app:netOn()
    if self.net then
        local o = self.net
        if o.match then O.leaveMatch(o) end
        o.me.ready = false
        o.host.rounds, o.host.time = app.settings.rounds, app.settings.time
        o.me.char = o.me.char > #Art.roster and 1 or math.max(1, o.me.char)
    end
    self.tier = app.quality == 'lo' and 'lo' or 'hi'
    self.shows = {Show.new(app.layers.world), Show.new(app.layers.world)}
    self.shown = {}
    self.back = G.layer(app.layers.back)
    self.L = G.layer(app.layers.ui)
    return self
end

-- sim options for a match description (both clients build the same ones)
local function makeSimOpts(chars, setup, seed)
    local a = Art.roster[chars[1]] or Art.roster[1]
    local b = Art.roster[chars[2]] or Art.roster[1]
    return {chars = {a, b}, rounds = setup.rounds, time = setup.time, seed = seed}
end

function S:launch(m)
    local app = self.app
    local r = m.roster
    local a, b = Art.roster[r.chars[1]] or Art.roster[1], Art.roster[r.chars[2]] or Art.roster[1]
    local st = Stage.order[m.setup.stage] or Stage.order[1]
    self.left = true
    app.audio:play(app.audio.ID.okBig)
    app:travel('vs', {chars = {a.key, b.key}, stage = st, mode = 'online', online = true,
                      rounds = m.setup.rounds, time = m.setup.time})
end

function S:say(s) self.msg, self.msgT = s, 2.5 end

function S:tick()
    local app = self.app
    self.t = self.t + 1 / 60
    if self.msgT > 0 then self.msgT = self.msgT - 1 / 60 end
    if self.bd then self.bd:step(300) end
    local o = self.net
    local acts = app.input:menu()
    for _, a in ipairs(acts) do
        if a == 'back' then
            if o then o.me.ready = false end
            app.net = nil          -- stop the heartbeat: the other side sees us leave
            app:travel('menu', {sel = 2})
            return
        end
    end
    if not o or self.left then return end
    local n = #Art.roster
    for _, a in ipairs(acts) do
        if not o.me.ready and a == 'left' then o.me.char = (o.me.char - 2) % n + 1; app.audio:play(app.audio.ID.move)
        elseif not o.me.ready and a == 'right' then o.me.char = o.me.char % n + 1; app.audio:play(app.audio.ID.move)
        elseif O.isHost(o) and (a == 'up' or a == 'down') then
            local d = a == 'up' and -1 or 1
            o.host.stage = (o.host.stage - 1 + d) % #Stage.order + 1
            app.audio:play(app.audio.ID.move)
        elseif a == 'ok' then
            if not o.slot then self:say('还没连上服务器，请稍候')
            else
                o.me.ready = not o.me.ready
                app.audio:play(o.me.ready and app.audio.ID.ok or app.audio.ID.back)
            end
        end
    end
    -- match start
    if O.isHost(o) then
        if O.bothReady(o) then
            local m = O.hostStart(o, function(st, f, re) if o.onFrame then o.onFrame(st, f, re) end end, makeSimOpts)
            if m then self:launch(m) end
        end
    else
        local m = O.checkJoin(o, function(st, f, re) if o.onFrame then o.onFrame(st, f, re) end end, makeSimOpts)
        if m then self:launch(m) end
    end
end

function S:showChar(i, key, x, face)
    if self.shown[i] == key then return end
    self.shown[i] = key
    if not key then self.shows[i]:hide() return end
    local app = self.app
    self.shows[i]:set(key, self.tier, 'idle', x, -app.H / 2 + 110, 1.45, face, 0)
    local nd = self.shows[i].bmp.node
    local x0 = nd.x
    nd:pos(x0 - face * 160, nd.y)
    nd:tween({anchoredPositionX = x0}, 0.45, 'OutCubic')
end

-- one side: tracked English name, big name, badge, ready stamp (or the waiting state)
local function side(L, c, sd, W, H, title, ready, waiting, t)
    local al = sd < 0 and 'l' or 'r'
    local ex = sd * (W / 2 - 70)
    local bx = ex - sd * 330
    local y = H / 2 - 210
    L:label(title, bx, y + 106, 660, 26, 16, UI.GOLD, al, nil, 1)
    if c then
        local ec = UI.ECOL[c.element] or K.elementColor[c.element]
        L:label(UI.track((K.en[c.key] or ''):upper()), bx, y + 70, 660, 26, 15, UI.GREY, al, nil, 1)
        L:label(c.name, bx, y + 8, 660, 100, 80, UI.WHITE, al, nil, 1)
        UI.badge(L, c.element, ex - sd * ((utf8.len(c.name) or 3) * 80 + 50), y + 8, 56, 1)
        L:rect(ex - sd * 200, y - 46, 400, 2, ec, 0.9)
        L:label((K.elementName[c.element] or '') .. '元素　·　' .. (K.weaponName[c.weapon] or ''), bx, y - 74, 660, 28, 19, UI.CREAM, al, nil, 1)
    else
        for _ = 1, 4 do L:label('', 0, 0, 1, 1, 10, UI.WHITE, 'c', nil, 0) end
        L:label(waiting, bx, y + 10, 660, 60, 36, UI.DIM, al, nil, 1)
        L:shape(G.RECT, 0, 0, 1, 1, UI.WHITE, 0)
        UI.constellation(L, sd * (W / 2 - 330), -H / 2 + 330, 150, t * 10, UI.WHITE, 0.6)
    end
    -- ready stamp
    local sx = sd * (W / 2 - 330)
    local ra = ready and 1 or 0
    UI.slab(L, sx, -H / 2 + 120, 340, 56, ready and UI.CREAM or UI.NAVY, ready and 0.96 or 0.7, sd * -8)
    UI.slab(L, sx - sd * 165, -H / 2 + 120, 10, 62, c and (UI.ECOL[c.element] or UI.GOLD) or UI.DIM, c and 1 or 0, sd * -8)
    L:label(ready and '已准备　READY' or (c and '未准备' or ''), sx, -H / 2 + 120, 340, 56, 24,
            ready and UI.TEXT or UI.GREY, 'c', nil, (ready or c) and 1 or 0):rot(sd * -8)
end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    local t = self.t
    if self.bd then self.bd:draw(0.5, {10, 12, 28}) end
    local o = self.net
    local me = o and Art.roster[o.me.char]
    local opp = o and O.opponent(o)
    local peer = opp and o.peers[opp]
    local oc = peer and peer.lobby and Art.roster[peer.lobby.char]
    self:showChar(1, me and me.key, -W / 2 + 330, 1)
    self:showChar(2, oc and oc.key, W / 2 - 330, -1)
    -- background: element slabs per side, seam, streaks
    local B = self.back
    B:begin()
    for i, c in ipairs({me or false, oc or false}) do
        local sd = i == 1 and -1 or 1
        local ec = c and (UI.ECOL[c.element] or K.elementColor[c.element]) or UI.SLATE2
        local sx = sd * (W / 2 - 150)
        UI.slab(B, sx, 0, 520, H * 1.9, U.mix(ec, UI.NAVY, 0.75), 0.75, sd * UI.SLANT)
        UI.stripes(B, sx, 0, 420, H * 1.9, 12, UI.WHITE, 0.03, sd * UI.SLANT)
        UI.slab(B, sx - sd * 270, 0, 3, H * 2, UI.GOLD, 0.7, sd * UI.SLANT)
        UI.slab(B, sx - sd * 298, 0, 10, H * 2, ec, 0.45, sd * UI.SLANT)
        B:shape(G.ELLIPSE, sd * (W / 2 - 330), -H / 2 + 330, 560, 640, ec, c and 0.24 or 0.08, 0, 0.5)
    end
    for i = 1, 8 do
        local yy = -H / 2 + i * H / 8.5
        local xx = ((t * (500 + (i % 3) * 250) + i * 211) % (W + 600)) - W / 2 - 300
        B:rect(xx, yy, 200 + (i % 3) * 140, 2, UI.WHITE, 0.08, -UI.SLANT)
    end
    B:finish()
    local L = self.L
    L:begin()
    -- header
    L:label('联机对战', 0, H / 2 - 56, 400, 56, 40, UI.WHITE, 'c', nil, 1)
    L:label(UI.track('ONLINE  VERSUS'), 0, H / 2 - 96, 420, 24, 14, UI.GOLD, 'c', nil, 1)
    L:shape(G.RECT, -170, H / 2 - 96, 7, 7, UI.GOLD, 1, 45)
    L:shape(G.RECT, 170, H / 2 - 96, 7, 7, UI.GOLD, 1, 45)
    local dots = string.rep('·', 1 + math.floor(t * 2) % 3)
    side(L, me, -1, W, H, '你' .. (o and o.slot and ('　·　号位 ' .. o.slot) or ''), o and o.me.ready, '', t)
    side(L, oc, 1, W, H, '对手' .. (opp and ('　·　号位 ' .. opp) or ''), peer and peer.lobby and peer.lobby.ready,
         '等待对手' .. dots, t)
    -- centre column: VS, stage, connection
    local host = o and O.isHost(o)
    local st = Stage.order[(o and o.host.stage) or 1]
    local hostSt = (not host and peer) and Stage.order[O.parseSetup(peer.setup).stage] or st
    local v = L:label('VS', 0, 70, 300, 180, 150, UI.WHITE, 'c', {40, 30, 70}, 0.9)
    UI.slab(L, 0, 62, 360, 10, UI.WHITE, 0.6, -UI.SLANT)
    L:rect(0, -90, 520, 2, UI.GOLD, 0.6)
    L:label(UI.track('STAGE'), 0, -116, 200, 24, 14, UI.GOLD, 'c', nil, 1)
    L:label(stageName(host and st or (hostSt or st)), 0, -152, 520, 44, 30, UI.WHITE, 'c', nil, 1)
    UI.chevron(L, -250, -152, 22, UI.WHITE, host and 0.8 or 0, -1)
    UI.chevron(L, 250, -152, 22, UI.WHITE, host and 0.8 or 0, 1)
    L:label(host and '房主可用 ↑ ↓ 切换' or (opp and '由房主选择' or ''), 0, -186, 400, 24, 15, UI.DIM, 'c', nil, 1)
    local status
    if not o then status = '这个关卡没有联机接口'
    elseif not o.slot then status = '正在连接服务器' .. dots
    elseif not opp then status = '已连接　·　等待第二位玩家'
    else status = ('已连接　·　%s　·　延迟 %s'):format(host and '你是房主' or '对手是房主',
        o.rtt and (math.floor(o.rtt * 1000 + 0.5) .. ' ms') or '测量中') end
    L:rect(0, -232, 520, 40, UI.NAVY, 0.8)
    L:label(status, 0, -232, 520, 40, 18, UI.CREAM, 'c', nil, 1)
    L:label(('先胜 %d 局　·　%s'):format(o and o.host.rounds or 2, (o and o.host.time or 99) >= 999 and '不限时' or ((o and o.host.time or 99) .. ' 秒')),
            0, -270, 520, 24, 15, UI.DIM, 'c', nil, 1)
    -- toast
    local ta = U.clamp(self.msgT / 0.3, 0, 1)
    UI.slab(L, 0, -330, 440, 44, UI.CREAM, 0.95 * ta, 0)
    L:label(self.msg or '', 0, -330, 440, 44, 18, UI.TEXT, 'c', nil, ta)
    UI.prompt(L, W / 2 - 640, -H / 2 + 34, 'A', '上一个', 1, 'left')
    UI.prompt(L, W / 2 - 480, -H / 2 + 34, 'D', '下一个', 1, 'right')
    UI.prompt(L, W / 2 - 320, -H / 2 + 34, 'J', (o and o.me.ready) and '取消准备' or '准备', 1, 'ok')
    UI.prompt(L, W / 2 - 140, -H / 2 + 34, 'K', '返回', 1, 'back')
    L:finish()
end

function S:exit()
    for _, s in ipairs(self.shows) do s:free() end
    self.back:free()
    self.L:free()
end

return S
