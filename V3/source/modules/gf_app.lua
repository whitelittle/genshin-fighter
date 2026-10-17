__loaders['gf_app'] = function()
local G = require('gf_gfx')
local Input = require('gf_input')
local Audio = require('gf_audio')

local App = {}
App.__index = App

local STEP = 1 / 60
local DESIGN_W, DESIGN_H = 1600, 900

App.SCENES = {
    intro = 'gf_scene_intro', title = 'gf_scene_title', menu = 'gf_scene_menu',
    select = 'gf_scene_select', vs = 'gf_scene_vs', fight = 'gf_scene_fight',
    result = 'gf_scene_result', options = 'gf_scene_options', howto = 'gf_scene_howto',
    test = 'gf_scene_test', online = 'gf_scene_online', gallery = 'gf_scene_gallery',
}

function App.new(env)
    local self = setmetatable({env = env, t = 0, acc = 0, frame = 0, fps = 60, scene = nil, sceneName = nil}, App)
    -- Stretch a permanent opaque backing independently of design/safe-area sizing.
    self.canvasBacking=G.image(G.root,G.RECT)
    self.canvasBacking:pos(0,0):size(0,0):rgba({11,15,31},1):on(true)
    env.safe(function()
        local c=self.canvasBacking.c
        c:SetAnchorMin(0,0);c:SetAnchorMax(1,1);c:SetPivot(.5,.5)
    end)
    self.view = G.group(G.root)
    self.layers = {}
    for _, name in ipairs({'back', 'world', 'front', 'hud', 'ui', 'top', 'curtain', 'debug'}) do
        self.layers[name] = G.group(self.view)
    end
    self:fit(true)
    self.input = Input.new(self)
    require('gf_ui').app = self
    self.audio = Audio.new(env)
    self.settings = {quality = 'lo', sfx = true, shake = true, cpu = 2, rounds = 2, time = 99, touch = 'auto'}
    for k, v in pairs(env.settings or {}) do self.settings[k] = v end   -- test / preview overrides
    self.save = {wins = 0, played = 0, arcadeBest = 0, unlocked = {}}
    self.settings.quality='lo'
    self.quality = self:detectQuality()
    self.debug = false
    local first = env.firstScene or 'intro'
    self:go(first, env.firstArgs)
    return self
end

function App:isMobile()
    local ok,d=pcall(self.env.game.GetDevice);local D=self.env.Enum.Device
    return ok and (d==D.Mobile or d==D.MobileController)
end
function App:detectQuality() return 'lo' end
function App:setQuality() return false end

function App:fit(force)
    local ok, cw, ch = pcall(self.env.game.GetUICanvasSize)
    if not ok or type(cw) ~= 'number' or cw <= 0 then cw, ch = DESIGN_W, DESIGN_H end
    if not force and cw == self.cw and ch == self.ch then return false end
    self.cw, self.ch = cw, ch
    local s
    if cw / ch >= DESIGN_W / DESIGN_H then s = ch / DESIGN_H else s = cw / DESIGN_W end
    self.s = s
    self.W, self.H = cw / s, ch / s
    self.view:pos(0, 0):scale(s, s)
    if self.scene and self.scene.resize then self.scene:resize() end
    return true
end

function App:go(name, args)
    if self:requestScenePool(name,args) then return end
    local old = self.scene
    if old and old.exit then old:exit() end
    self.scene=nil
    self.input:clearUI()
    if self:requestScenePool(name,args) then return end
    local mod = require(App.SCENES[name] or name)
    self.sceneName = name
    self.scene = mod.new(self, args or {})
    self.sceneT = 0
end

function App:update(dt)
    self.callbackDt=dt
    self:netPump() -- receive before any pool maintenance or drawing
    if self.poolNext then
        self:netPump()
        if #G.trash>0 then G.flushTrash(64) end
        G.flushRetired(96)
        if self:advanceScenePool() then return end
    end
    local sim=self.scene and self.scene.sim
    local phase=sim and sim.phase
    local safeBoundary=not sim or phase=='over' or (phase=='ko' and sim.phaseT>=90)
    G.manageImagePool(phase,safeBoundary)
    if dt > 0.25 then dt = 0.25 end
    self.t = self.t + dt
    if dt > 0 then self.fps = self.fps * 0.9 + (1 / dt) * 0.1 end
    self.fitT = (self.fitT or 0) + dt
    if self.fitT > 0.5 then self.fitT = 0; self:fit(false) end
    self.input:poll()
    if #G.trash > 0 then G.flushTrash(64) end
    G.flushRetired(64)
    self.acc = self.acc + dt
    local steps = 0
    while self.acc >= STEP and steps < 4 do
        self.acc = self.acc - STEP
        steps = steps + 1
        self.frame = self.frame + 1
        self.input:tick()
        self:netPump()
        local sc = self.scene
        if sc and sc.tick then sc:tick() end
        self.sceneT = self.sceneT + STEP
        if self.nextScene then
            local n = self.nextScene
            self.nextScene = nil
            self:go(n[1], n[2])
        end
    end
    -- Keep a bounded backlog instead of discarding every pending movement tick.
    if self.acc > STEP * 4 then
        self.droppedTime=(self.droppedTime or 0)+self.acc-STEP*4
        self.acc=STEP*4
    end
    local sc = self.scene
    if sc and sc.draw then sc:draw(self.acc / STEP, dt) end
    self:samplePerformance(self.callbackDt or dt)
    self.audio:update(dt)
    self:drawTransition()
    if self.debug then self:drawDebug() elseif self.debugLayer then self.debugLayer:clear() end
end

function App:netOn()
    if not self.net and self.env.netio then
        if self.env.netio.start then self.env.netio.start() end
        self.net = require('gf_online').new(self.env.netio)
    end
    return self.net
end

function App:netPump()
    local o = self.net
    if not o then return end
    local O = require('gf_online')
    if o.io.pump then o.io.pump() end
    O.poll(o)
    local sc = self.scene
    if sc and sc.online and sc.state == 'run' and o.match then return end
    O.keepAlive(o)
end

function App:switch(name, args) self.nextScene = {name, args} end

function App:travel(name, args, col)
    if self.trans then return end
    self.trans = {t = 0, name = name, args = args, col = col or {255, 214, 120}}
    self.audio:play(self.audio.ID.open)
end

function App:drawTransition()
    local tr = self.trans
    if not tr then if self.transL then self.transL:clear() end return end
    self.transL = self.transL or G.layer(self.layers.curtain)
    local L = self.transL
    tr.t = tr.t + 1
    local IN, HOLD, OUT = 16, 4, 18
    local k
    if tr.t <= IN then k = tr.t / IN
    elseif tr.t <= IN + HOLD then
        k = 1
        if tr.t == IN + 1 then self:go(tr.name, tr.args) end
    else k = 1 - (tr.t - IN - HOLD) / OUT end
    local W, H = self.W, self.H
    local e = k * k * (3 - 2 * k)
    L:begin()
    for i = 1, 3 do
        local off = (1 - e) * (W * 1.4) * (tr.t <= IN + HOLD and 1 or -1) + (i - 2) * 30 * (1 - e)
        local col = i == 2 and tr.col or {12, 14, 26}
        L:rect(off, 0, W * 1.5 * (i == 2 and 0.04 or 1) + (i == 2 and 0 or 0), H * 1.6, col, i == 2 and 1 or 1, -12)
    end
    L:shape(G.STAR4, 0, 0, 140 * e, 140 * e, tr.col, e, tr.t * 6)
    L:finish()
    if tr.t >= IN + HOLD + OUT then self.trans = nil; L:clear() end
end

function App:backdrop(key)
    local B = require('gf_backdrop')
    if self.bd and self.bd.key ~= key then self.bd:free(true); self.bd = nil end
    if not self.bd then
        self.bd = B.new(self, self.layers.back, key)
        self.bd.root:sibling(0)          -- under anything the scene already put in the back layer
    end
    self.bd.root:on(true)
    return self.bd
end

function App:dropBackdrop()
    if self.bd then self.bd:free(true); self.bd = nil end
end

function App:samplePerformance(dt)
    if GF_PERF_ENABLED==false and not self.debug then return end
    local n=G.N
    -- bitmap writes are a subset of N.pos: do not count them twice.
    local writes=(n.pos or 0)+(n.size or 0)+(n.col or 0)+(n.vis or 0)+(n.par or 0)+(n.txt or 0)
    local s=G.secondPoolStatus()
    local m=self.net and self.net.match
    local net=m and m.session
    local p=self.perf or {samples=0,sum=0,max=0,slow=0,lastWrites=0,lastBitmap=0,lastCreated=0,lastDecode=0,writes=0,windowT=0}
    local bitmap=n.bitmap or 0
    local decoded=require('gf_util').decodedBytes or 0
    p.samples=p.samples+1;p.sum=p.sum+dt;p.windowT=p.windowT+dt
    p.max=math.max(p.max,dt);if dt>1/30 then p.slow=p.slow+1 end
    p.frameWrites=math.max(0,writes-p.lastWrites);p.lastWrites=writes;p.writes=p.writes+p.frameWrites
    p.frameBitmapWrites=math.max(0,bitmap-p.lastBitmap);p.lastBitmap=bitmap
    p.frameCreated=math.max(0,s.created-p.lastCreated);p.lastCreated=s.created
    p.frameDecoded=math.max(0,decoded-p.lastDecode);p.lastDecode=decoded
    p.maxFrameWrites=math.max(p.maxFrameWrites or 0,p.frameWrites)
    p.maxBitmapWrites=math.max(p.maxBitmapWrites or 0,p.frameBitmapWrites)
    p.created=(p.created or 0)+p.frameCreated;p.decoded=(p.decoded or 0)+p.frameDecoded
    p.waits=m and (m.waits or 0) or 0
    p.syncWaits=m and (m.syncWaits or 0) or 0
    p.stalls=net and net.stats.stalls or 0
    p.predict=net and math.max(0,net.frame-net.confirmed) or 0
    p.maxPredict=net and net.maxPredict or 0
    p.rollbacks=net and net.stats.rollbacks or 0
    p.droppedMs=(self.droppedTime or 0)*1000
    p.simTick=self.scene and self.scene.sim and self.scene.sim.tick or 0
    self.perf=p
    if p.windowT>=2 then
        print(('GF_PERF scene=%s dt_avg_ms=%.1f dt_max_ms=%.1f slow=%d ui_calls=%d ui_peak=%d bitmap_peak=%d created=%d decoded=%d waits=%d sync_waits=%d stalls=%d predict=%d/%d rollback=%d dropped_ms=%.1f sim_tick=%d'):format(
            tostring(self.sceneName),p.sum/p.samples*1000,p.max*1000,p.slow,p.writes,p.maxFrameWrites,p.maxBitmapWrites,p.created,p.decoded,
            p.waits,p.syncWaits,p.stalls,p.predict,p.maxPredict,p.rollbacks,p.droppedMs,p.simTick))
        p.samples=0;p.sum=0;p.max=0;p.slow=0;p.writes=0;p.windowT=0
        p.maxFrameWrites=0;p.maxBitmapWrites=0;p.created=0;p.decoded=0
    end
end

function App:drawDebug()
    if not self.debugLayer then self.debugLayer = G.layer(self.layers.debug) end
    local L = self.debugLayer
    L:begin()
    local c = G.counts
    local s = ('FPS %d  | 场景 %s | 图片 %d/%d 文字 %d/%d | 写入 %d'):format(
        math.floor(self.fps + 0.5), tostring(self.sceneName), c.img - #G.freeImg - #(G.freeSecond or {}), c.img, c.txt - #G.freeTxt, c.txt,
        G.N.pos + G.N.size + G.N.col + G.N.vis)
    L:rect(-self.W / 2 + 330, self.H / 2 - 18, 660, 30, {0, 0, 0, 170})
    L:label(s, -self.W / 2 + 330, self.H / 2 - 18, 650, 30, 16, {120, 255, 160}, 'l')
    L:finish()
end

-- Cover the previous scene while the second image pool grows in frame batches.
function App:drawScenePool(state)
    local pending = self.poolNext
    local total = math.max(1, state.target - pending.start)
    local progress = math.max(0, math.min(1, (state.total - pending.start) / total))
    self.poolLoadingL = self.poolLoadingL or G.layer(self.view)
    local L = self.poolLoadingL
    L.node:front()
    local width = math.min(560, self.W - 160)
    L:begin()
    L:rect(0, 0, self.W + 80, self.H + 80, {0, 0, 0}, 1)
    L:label('正在加载', 0, 48, width, 44, 28, {236, 229, 216})
    L:rect(0, 0, width, 6, {45, 45, 45}, 1)
    L:rect((progress - 1) * width / 2, 0, width * progress, 6, {211, 188, 142}, 1)
    L:label(('%d%%'):format(math.floor(progress * 100)), 0, -36, width, 32, 20, {165, 165, 165})
    L:finish()
    self.env.host:SetVisible(false)
end

function App:requestScenePool(name, args)
    local needs = {intro=1800, title=8000, menu=3200, options=3200, howto=6400,
                   select=14000, online=12000, vs=14000, fight=14000, result=6400, test=256}
    local start = G.secondPoolStatus().total
    local ready=G.requestImages(needs[name] or 9500)
    if ready and G.retiredPending()==0 and #G.trash==0 then return false end
    self.poolNext = {name=name, args=args, start=start}
    self:drawScenePool(G.secondPoolStatus())
    return true
end
function App:advanceScenePool()
    local pending = self.poolNext
    if not pending then return false end
    if G.retiredPending()>0 or #G.trash>0 then
        self:drawScenePool(G.secondPoolStatus())
        return true
    end
    local done = G.growImages()
    self:drawScenePool(G.secondPoolStatus())
    if done then
        self.poolNext = nil
        self.poolLoadingL:free()
        self.poolLoadingL = nil
        self:go(pending.name, pending.args)
    end
    return true
end

return App
end
