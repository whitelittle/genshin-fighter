__loaders['gf_scene_fight'] = function()

-- The fight: loads stage + both fighters over a few frames behind a curtain, then runs the
-- simulation at 60 Hz and turns its events into effects, sound, camera and announcements.
--
-- args: {chars = {key1, key2}, mode = 'arcade' | 'versus' | 'cpu' | 'training' | 'demo' | 'online',
--        cpu = {false|level, false|level}, stage = key, arcade = {...state for the ladder}}
-- online: the match session (gf_online / gf_net) owns the simulation; this scene feeds it the
-- local input each tick, re-binds the views after a rollback and plays each event once.
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

local S = {}
S.__index = S

local C = Sim.C

function S.new(app, args)
    local self = setmetatable({app = app, args = args, state = 'load', t = 0, shake = 0, shakeT = 0, zoomPunch = 0,
                               camX = 0, zoom = 1, slow = 0, banners = {}, paused = false, endT = 0}, S)
    local L = app.layers
    app:dropBackdrop()
    self.mode = args.mode or 'versus'
    self.tier = app.quality == 'lo' and 'lo' or 'hi'
    local chars = {Art.byKey[args.chars[1]], Art.byKey[args.chars[2]]}
    self.chars = chars
    self.stageKey = args.stage or Stage.order[1]
    local net = args.online and app.net
    if net and net.match then
        -- online: the session's state is the simulation; events come through onNetFrame
        self.online = net
        app.audio.lastEvent = {}
        self.side = net.match.side
        self.sim = net.match.session.state
        self.seenEv, self.netEvents = {}, {}
        net.onFrame = nil
        net.match.session.onConfirmed = function(state,f)
            if #state.events>0 or (self.stage and self.stage.L.lightning and state.tick%420==200) then self.netEvents[#self.netEvents+1]={state=state,frame=f} end
        end
    else
        self.sim = Sim.new({chars = chars, rounds = args.rounds or app.settings.rounds, time = args.time or app.settings.time,
                            seed = args.seed or (math.floor(app.t * 1000) % 100000 + 7), training = self.mode == 'training',
                            infinite = args.infinite,teams=args.teamRoster,assistChars=args.assistChars})
    end
    -- loading curtain
    self.curtain = G.layer(L.curtain)
    -- groups
    self.stage = Stage.new(app, L.back, self.mode == 'training' and 'training' or self.stageKey)
    self.worldG = G.group(L.world)
    self.lay = {shadow = G.group(self.worldG), ghost = G.group(self.worldG), body = G.group(self.worldG),
                proj = G.group(self.worldG), fx = G.group(self.worldG)}
    self.prep = {Art.prepare(chars[1].key, self.tier), Art.prepare(chars[2].key, self.tier)}
    self.loadStep = 0
    return self
end

------------------------------------------------------------------ loading
-- phones (or the touch setting) get on-screen controls for player 1
function S:curtainDraw(a)
    local app = self.app
    local L = self.curtain
    L:begin()
    if a > 0.01 then
        app:cover(L,{6,8,16},a)
        local c1, c2 = self.chars[1], self.chars[2]
        local k = self.loadStep
        local dots = ('.'):rep(1 + (k // 10) % 3)
        local completed, total = 0, 0
        for _, j in ipairs(self.prep) do
            completed = completed + (j.completed or 0)
            total = total + (j.total or 0)
        end
        local status = '载入中' .. dots
        if total > 0 and completed < total then status = '准备动作 ' .. completed .. '/' .. total end
        L:label(status, 0, -app.H / 2 + 90, 400, 40, 26, UI.GOLD2, 'c', nil, a)
        -- spinning element diamond
        local ec = K.elementColor[c1.element]
        L:shape(G.RECT, 0, -app.H / 2 + 150, 30, 30, ec, a, k * 6)
        L:shape(G.RECT, 0, -app.H / 2 + 150, 30, 30, K.elementColor[c2.element], a * 0.7, -k * 6)
    end
    L:finish()
end

function S:curtainOpen() self.curtainA = 1 end

------------------------------------------------------------------ inputs
function S:inputs()
    local app = self.app
    local sim = self.sim
    local ins = {0, 0}
    for i = 1, 2 do
        if self.ai[i] then
            ins[i] = sim.phase=='fight' and self.ai[i]:tick() or 0
        else
            local pad = app.input:pad(i)
            ins[i] = pad.now or 0
            -- single human vs CPU: the controller / P2 keys also drive P1
            if i == 1 and self.ai[2] then ins[i] = ins[i] | (app.input:pad(2).now or 0) end
        end
    end
    if self.mode == 'training' then
        local d = self.dummy or 'stand'
        local p2 = sim.f[2]
        local away = (p2.foe.x > p2.x) and Sim.B.L or Sim.B.R
        if d == 'block' then ins[2] = away
        elseif d == 'crouch' then ins[2] = Sim.B.D
        elseif d == 'cblock' then ins[2] = away | Sim.B.D
        elseif d == 'jump' then ins[2] = (sim.tick % 60 < 2) and Sim.B.U or 0
        elseif d == 'cpu' then ins[2] = self.ai[2] and ins[2] or 0
        else ins[2] = 0 end
    end
    return ins[1], ins[2]
end

------------------------------------------------------------------ events
function S:camera(snap)
    local app, sim = self.app, self.sim
    local a, b = sim.f[1], sim.f[2]
    local x1, x2 = a.x / C, b.x / C
    local mid = (x1 + x2) / 2
    local dist = math.abs(x2 - x1)
    local W = app.W
    local zoom = U.clamp((W - 520) / math.max(dist, 300), 0.78, 1.12)
    if self.cine and self.cine.char.key~='raidenshogun' then
        local p = sim.f[self.cine.p]
        mid = p.x / C
        zoom = 1.25
    end
    zoom = GF_FIXED_BODY_SCALE~=false and 1 or (zoom + self.zoomPunch)
    self.zoomPunch = self.zoomPunch * 0.85
    -- keep the view inside the stage
    local half = W / 2 / zoom
    local lim = Sim.WALL / C + 180
    mid = U.clamp(mid, -lim + half, lim - half)
    if half > lim then mid = 0 end
    if snap then self.camX, self.zoom = mid, zoom
    else
        self.camX = self.camX + (mid - self.camX) * 0.18
        self.zoom = self.zoom + (zoom - self.zoom) * 0.12
    end
    -- highest fighter: lift the camera a little
    local hy = math.max(a.y, b.y) / C
    local lift = U.clamp(hy - 220, 0, 260) * 0.45
    local sx, sy = 0, 0
    if self.shake > 0 then
        local s = self.shake
        sx = ((self.app.frame % 2 == 0) and 1 or -1) * s * 1.4
        sy = ((self.app.frame % 4 < 2) and 1 or -1) * s * 0.9
        self.shake = self.shake * 0.82
        if self.shake < 0.5 then self.shake = 0 end
    end
    self.floorY = -app.H / 2 + 150 - lift
    self.worldG:pos(-self.camX * self.zoom + sx, self.floorY + sy):scale(self.zoom, self.zoom)
    self.stage:camera(self.camX, self.zoom, self.floorY, sx, sy)
end

------------------------------------------------------------------ projectiles
function S:drawProj()
    local L = self.projL
    L:begin()
    local t = self.app.frame
    for _, pr in ipairs(self.sim.proj) do
        local x, y = pr.x / C, pr.y / C
        local ec = K.elementColor[pr.element] or {255, 255, 255}
        local st = pr.style
        local w, h = pr.w / C, pr.h / C
        local live = pr.t > pr.delay
        if pr.zone then
            -- telegraph during the delay, strike after
            if not live then
                local k = pr.t / math.max(1, pr.delay)
                L:shape(G.ELLIPSE, x, 6, w * (1.2 - 0.4 * k), 30, ec, 0.4 + 0.4 * k)
                L:shape(G.RING, x, 6, w * (1.6 - 0.8 * k), 44, ec, 0.8)
                if st == 'eye' then L:shape(G.ELLIPSE, x, 560, 120, 70, ec, 0.6 * k); L:shape(G.ELLIPSE, x, 560, 40, 40, {255, 255, 255}, k) end
                if st == 'sakura' then L:shape(G.TRI, x - 40, 60, 30, 120, {255, 170, 210}, 0.9) end
            else
                local k = (pr.t - pr.delay) / math.max(1, pr.life - pr.delay)
                local a = 1 - k
                if st == 'pillar' then
                    local hh = h * U.clamp((pr.t - pr.delay) / 5, 0, 1)
                    L:rect(x, hh / 2, w, hh, {170, 130, 70}, 1)
                    L:rect(x, hh / 2, w * 0.7, hh, {220, 180, 100}, 1)
                    L:rect(x, hh - 10, w * 1.1, 24, {255, 210, 120}, 1)
                else
                    L:rect(x, h / 2, w * 0.35 * a + 8, h, ec, 0.9 * a)
                    L:rect(x, h / 2, w * 0.12 * a + 4, h, {255, 255, 255}, a)
                    L:shape(G.ELLIPSE, x, 10, w * 1.4, 60, ec, 0.7 * a, 0, 0.4)
                end
            end
        else
            if st == 'arrow' then
                L:rect(x - pr.face * 30, y, w, 6, {255, 255, 255}, 1)
                L:rect(x - pr.face * 80, y, w * 1.4, 18, ec, 0.45)
                L:shape(G.TRI, x + pr.face * (w / 2), y, 22, 34, ec, 1, -90 * pr.face)
            elseif st == 'ushi' then
                L:shape(G.ELLIPSE, x, y, w, h * 0.8, {150, 80, 40}, 1)
                L:shape(G.ELLIPSE, x + pr.face * 40, y + 30, 70, 60, {180, 100, 50}, 1)
                L:shape(G.TRI, x + pr.face * 40 - 22, y + 70, 16, 34, {255, 240, 220}, 1, 20)
                L:shape(G.TRI, x + pr.face * 40 + 22, y + 70, 16, 34, {255, 240, 220}, 1, -20)
                L:shape(G.RING, x, y, w * 1.2, h, ec, 0.6)
            elseif st == 'torrent' then
                L:shape(G.ELLIPSE, x, y, w, h, ec, 0.8, 0, 0.3)
                L:shape(G.ELLIPSE, x, y, w * 0.8, h * 0.4, {220, 245, 255}, 0.9)
                L:shape(G.ELLIPSE, x - pr.face * w * 0.6, y, w * 0.8, h * 0.6, ec, 0.4, 0, 0.5)
            elseif st == 'shards' then
                for i = 0, 4 do
                    L:shape(G.TRI, x + (i - 2) * 30, y + ((i * 37) % 60) - 30, 26, 50, {255, 220, 120}, 1, -90 * pr.face + (i - 2) * 12)
                end
                L:shape(G.ELLIPSE, x, y, w, h * 0.6, ec, 0.4, 0, 0.5)
            elseif st == 'bubble' then
                L:shape(G.ELLIPSE, x, y + math.sin(t * 0.2) * 10, w, h, ec, 0.5, 0, 0.3)
                L:shape(G.RING, x, y + math.sin(t * 0.2) * 10, w, h, {220, 245, 255}, 0.9)
                L:shape(G.ELLIPSE, x - 18, y + 22 + math.sin(t * 0.2) * 10, 22, 16, {255, 255, 255}, 0.9)
            else
                L:shape(G.ELLIPSE, x, y, w * 1.5, h * 1.5, ec, 0.4, 0, 0.5)
                L:shape(G.ELLIPSE, x, y, w * 0.8, h * 0.8, ec, 0.95)
                L:shape(G.ELLIPSE, x, y, w * 0.4, h * 0.4, {255, 255, 255}, 1)
                L:shape(G.STAR4, x, y, w, h, {255, 255, 255}, 0.8, t * 8)
                L:shape(G.ELLIPSE, x - pr.face * w * 0.7, y, w, h * 0.5, ec, 0.35, 0, 0.5)
            end
        end
    end
    L:finish()
end

------------------------------------------------------------------ pause
function S:tick()
    local app = self.app
    if self.state == 'load' then
        self:loadTick()
        return
    end
    local menu = app.input:menu()
    if self.paused then
        if self.showMoves then
            for _, a in ipairs(menu) do if a == 'back' or a == 'ok' or a == 'pause' then self.showMoves = nil end end
        elseif self.pauseMenu then
            for _, a in ipairs(menu) do if a == 'pause' then self:closePause() return end end
            self.pauseMenu:input(menu)
        end
        -- an online match cannot pause: the menu floats over the running fight
        if self.online and self.state == 'run' and self.online.match then self:netTick(true) end
        return
    end
    for _, a in ipairs(menu) do
        if a == 'pause' then self:openPause() return end
        if a == 'debug' then app.debug = not app.debug end
    end
    if self.online then
        if not self:netTick(false) then return end
    else
        local in1, in2 = self:inputs()
        self.sim:step(in1, in2)
        self:events()
    end
    local sim = self.sim
    -- stormy stage: lightning now and then
    if not self.online and self.stage.L.lightning and sim.tick % 420 == 200 then
        if self.stage:thunder() then app.audio:play(app.audio.ID.ehit.electro) end
    end
    if self.endT > 0 then
        self.endT = self.endT - 1
        if self.endT == 0 then self:finish() end
    end
end

-- one online tick: local input in, frames out (with rollbacks), events once; false = left
function S:finish()
    local app = self.app
    local sim = self.sim
    if self.online then
        if self.netEnd and not self.winner then self.winner = self.side end
        Online.leaveMatch(self.online)
        self.online.onFrame = nil
    end
    local res = {winner = self.winner, chars = self.sim.teams and {sim.f[1].key,sim.f[2].key} or self.args.chars, mode = self.mode, args = self.args, side = self.side,
                 stats = {sim.f[1].stats, sim.f[2].stats}, wins = {sim.f[1].wins, sim.f[2].wins},
                 teamRemaining=sim.teamIndex and {math.max(0,4-sim.teamIndex[1]),math.max(0,4-sim.teamIndex[2])}}
    app:travel('result', res, K.elementColor[self.chars[self.winner or 1].element])
end

function S:draw()
    local app = self.app
    if self.state == 'load' then
        self:curtainDraw(1)
        return
    end
    if self.curtainA and self.curtainA > 0 then
        self.curtainA = self.curtainA - 0.08
        self:curtainDraw(math.max(0, self.curtainA))
    end
    self:drawBurstBackdrop()
    local urgent = self.sim.phase ~= 'intro'
    self.teamViewPending=false
    if self.sim.teams then
        require('gf_character_cinematic_view').reserve(self,160)
        require('gf_character_cinematic_view').reserveLegacy(self,160)
    end
    local bitmapLimit=GF_BATTLE_BITMAP_WRITES or 3200
    if not app:isMobile() then G.beginBitmapBudget(bitmapLimit) end
    for i,v in ipairs(self.views) do
        G.bitmapOwner(math.floor(bitmapLimit/#self.views))
        if v:bindFighter(self.sim.f[i]) then v:draw(urgent and 520 or 300)
        else self.teamViewPending=true end
    end
    G.bitmapOwner(480);require('gf_assist_view').draw(self)
    G.endBitmapBudget()
    self:arcs()
    self:camera(false)
    self:drawProj()
    self.hud:draw()
    if self.touch then self.touch.f=self.sim.f[self.side or 1] end
    if self.touch and not self.paused then self.touch:draw() end
    self.fx:update()
    self:cineDraw()
    self:drawBanners()
    if self.sim.teamIndex then
        self.teamL=self.teamL or G.layer(app.layers.hud);local L=self.teamL;L:begin()
        for side=1,2 do
            local x=(side==1 and -1 or 1)*(app.W/2-190)
            L:label(('出场 %d/3'):format(math.min(3,self.sim.teamIndex[side])),x,app.H/2-155,260,32,20,UI.GOLD,'c')
        end
        if self.teamViewPending then L:label('换人中',0,20,500,60,36,UI.WHITE,'c') end
        L:finish()
    end
    if self.paused then self:drawPause() end
end

function S:exit()
    require('gf_character_cinematic_view').hide(self)
    local app = self.app
    -- Hide owned roots immediately; return leaves to the pool over later updates.
    local function hide(n) if n then n:on(false) end end
    hide(self.worldG)
    if self.stage then for _,n in pairs(self.stage.groups) do hide(n) end end
    if self.hud then hide(self.hud.root) end
    for _,layer in ipairs({self.annL,self.burstBg,self.pauseL,self.curtain,self.projL}) do
        if layer then hide(layer.node) end
    end
    if self.cut then hide(self.cut.L.node);hide(self.cut.bmp.node) end
    if self.touch then hide(self.touch.L.node) end
    if self.pauseMenu then hide(self.pauseMenu.L.node) end
    if self.burstEye then hide(self.burstEye.node) end
    if self.fx then for _,n in ipairs(self.fx.screen.img) do hide(n) end end
    if self.online and self.online.match then self.online.match.session.onConfirmed=nil end
    G.deferRelease=true
    require('gf_assist_view').free(self)
    if self.views then for _, v in ipairs(self.views) do v:free() end end
    if self.hud then self.hud:free() end
    if self.burstBg then self.burstBg:free() end
    if self.burstEye then self.burstEye:free() end
    if self.touch then self.touch:free() end
    if self.projL then self.projL:free() end
    if self.annL then self.annL:free() end
    require('gf_character_cinematic_view').free(self)
    if self.cut then self.cut.L:free(); self.cut.bmp:free();if self.cut.placeholder~=self.cut.bmp then self.cut.placeholder:free() end end
    if self.pauseMenu then self.pauseMenu:free() end
    if self.pauseL then self.pauseL:free() end
    if self.fx then
        for _, n in ipairs(self.fx.world.img) do G.release(n) end
        for _, n in ipairs(self.fx.screen.img) do G.release(n) end
        for _, n in ipairs(self.fx.text.txt) do G.release(n) end
    end
    self.stage:free()
    self.curtain:free()
    for _, g in pairs(self.lay) do G.release(g) end
    G.release(self.worldG)
    G.deferRelease=false
    if self.teamL then self.teamL:free() end
    G.requestImageRetirement()
end

require('gf_battle_loading')(S)
require('gf_battle_input')(S)
require('gf_battle_events')(S)
require('gf_battle_pause')(S)
require('gf_battle_network')(S)
require('gf_battle_backdrop')(S)
return S
end
