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
function App:detectQuality()
    if self:isMobile() then return 'lo' end
    return self.settings.quality=='hi' and 'hi' or 'lo'
end
function App:setQuality(q)
    if self.qualityLoad or (q=='hi' and self:isMobile()) or q==self.quality then return false end
    local entries={};local hd=require('gf_hd_r31')
    for _,key in ipairs({'raidenshogun','nahida'}) do
        local bank=hd[key=='raidenshogun' and 'raiden' or 'nahida'];local names={}
        for name in pairs(bank) do if name~='pal' then names[#names+1]=name end end
        table.sort(names);for _,name in ipairs(names) do entries[#entries+1]={key,name} end
    end
    local baseline=G.setQualityPool(q)
    self.qualityLoad={target=q,entries=entries,i=0,poolStart=G.secondPoolStatus().total,poolGoal=baseline}
    if self.scene and self.scene.exit then self.scene:exit() end
    self.scene=nil;self.sceneName='quality_loading';self:dropBackdrop();self.input:clearUI()
    self.qualityLoadingL=G.layer(self.layers.curtain)
    return true
end
function App:advanceQualityLoad()
    local job=self.qualityLoad;if not job then return false end
    local A=require('gf_art')
    for _=1,2 do
        local e=job.entries[job.i+1];if not e then break end
        A.animation(e[1],job.target,e[2]);job.i=job.i+1
    end
    if job.target=='lo' then
        G.flushTrash(400)
        for _=1,4 do G.manageImagePool(nil,true) end
    else
        for _=1,4 do G.growImages() end
    end
    local pool=G.secondPoolStatus()
    local poolProgress=math.min(1,math.max(0,(pool.total-job.poolStart)/math.max(1,job.poolGoal-job.poolStart)))
    if job.target=='lo' then poolProgress=math.min(1,math.max(0,(job.poolStart-pool.total)/math.max(1,job.poolStart-job.poolGoal))) end
    if (job.target=='hi' and pool.total>=job.poolGoal) or (job.target=='lo' and pool.total<=job.poolGoal) then poolProgress=1 end
    local progress=(job.i/math.max(1,#job.entries)+poolProgress)/2;local L=self.qualityLoadingL;local w=math.min(560,self.W-160)
    L:begin();L:rect(0,0,self.W+40,self.H+40,{8,12,24},1)
    L:label(job.target=='hi' and '正在加载高级画质' or '正在加载简单画质',0,65,w,50,30,{236,229,216})
    L:rect(0,0,w,10,{45,45,60},1);L:rect((progress-1)*w/2,0,w*progress,10,{120,196,245},1)
    L:label(('%d%%'):format(math.floor(progress*100)),0,-45,w,40,24,{210,210,220});L:finish()
    if job.i>=#job.entries and ((job.target=='hi' and pool.total>=job.poolGoal) or (job.target=='lo' and pool.total<=job.poolGoal)) then
        self.settings.quality=job.target;self.quality=job.target;self.qualityLoad=nil
        L:free();self.qualityLoadingL=nil;self:go('options')
    end
    return true
end

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
    self.input:clearUI()
    local mod = require(App.SCENES[name] or name)
    self.sceneName = name
    self.scene = mod.new(self, args or {})
    self.sceneT = 0
end

function App:update(dt)
    if self:advanceQualityLoad() then return end
    if self:advanceScenePool() then return end
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
    if #G.trash > 0 then G.flushTrash(400) end
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
    if self.acc > STEP * 4 then self.acc = 0 end
    local sc = self.scene
    if sc and sc.draw then sc:draw(self.acc / STEP, dt) end
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

function App:drawDebug()
    if not self.debugLayer then self.debugLayer = G.layer(self.layers.debug) end
    local L = self.debugLayer
    L:begin()
    local c = G.counts
    local s = ('FPS %d  | 场景 %s | 图片 %d/%d 文字 %d/%d | 写入 %d'):format(
        math.floor(self.fps + 0.5), tostring(self.sceneName), c.img - #G.freeImg, c.img, c.txt - #G.freeTxt, c.txt,
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
    if G.requestImages(needs[name] or 9500) then return false end
    self.poolNext = {name=name, args=args, start=start}
    self:drawScenePool(G.secondPoolStatus())
    return true
end
function App:advanceScenePool()
    local pending = self.poolNext
    if not pending then return false end
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
