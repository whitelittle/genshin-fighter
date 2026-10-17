__loaders['gf_app'] = function()
local G = require('gf_gfx')
local Input = require('gf_input')
local Audio = require('gf_audio')

local App = {}
App.__index = App

local STEP = 1 / 60
local DESIGN_W, DESIGN_H = 1600, 900

App.SCENES = {
    notice='gf_scene_update_notice',trainingcourses='gf_scene_training_courses',
    intro = 'gf_scene_intro', title = 'gf_scene_title', menu = 'gf_scene_menu',
    select = 'gf_scene_select', vs = 'gf_scene_vs', fight = 'gf_scene_fight',
    result = 'gf_scene_result', options = 'gf_scene_options', howto = 'gf_scene_howto',
    test = 'gf_scene_test', online = 'gf_scene_online', gallery = 'gf_scene_gallery',
}

function App.new(env)
    local self = setmetatable({env = env, t = 0, acc = 0, frame = 0, fps = 60, scene = nil, sceneName = nil}, App)
    -- Stretch a permanent opaque backing independently of design/safe-area sizing.
    self.canvasBacking=G.image(G.root,G.RECT)
    self.canvasBacking:pos(0,0):rgba({11,15,31},1):on(true)
    env.safe(function()
        local c=self.canvasBacking.c
        c:SetAnchorMin(.5,.5);c:SetAnchorMax(.5,.5);c:SetPivot(.5,.5)
    end)
    self.view = G.group(G.root)
    self.layers = {}
    for _, name in ipairs({'back', 'world', 'front', 'hud', 'ui', 'top', 'curtain', 'debug'}) do
        self.layers[name] = G.group(self.view)
    end
    self:fit(true)
    self.input = env.recoveryInput or Input.new(self)
    self.input.app=self
    require('gf_ui').app = self
    self.audio = Audio.new(env)
    self.settings = {quality = 'lo', sfx = true, shake = true, cpu = 2, rounds = 2, time = 99, touch = 'auto'}
    for k, v in pairs(env.settings or {}) do self.settings[k] = v end   -- test / preview overrides
    self.save = {wins = 0, played = 0, arcadeBest = 0, unlocked = {}}
    self.settings.quality='lo'
    self.quality = self:detectQuality()
    self.debug = false
    self:initExit()
    self:initRecovery(env.recoveryUI)
    G.mobileLightEffects=self:isMobile()
    local first = env.firstScene or 'intro'
    self:go(first, env.firstArgs)
    if GF_ASSET_PRELOAD_AT_START then
        self.initialAssets={i=1,keys={'raidenshogun','nahida','furina','kamisatoayaka','clorinde','arlecchino'},elapsed=0,completed=0,total=0}
    end
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
    if not ok or type(cw) ~= 'number' or type(ch) ~= 'number' or cw <= 0 or ch <= 0 then cw, ch = DESIGN_W, DESIGN_H end
    if not force and cw == self.cw and ch == self.ch then return false end
    self.cw, self.ch = cw, ch
    -- The native canvas size may describe its safe layout area. Keep the root
    -- stretched to its actual parent rather than reducing it to that safe width.
    self.env.safe(function()
        local c=self.env.root
        c:SetAnchorMin(0,0);c:SetAnchorMax(1,1);c:SetPivot(.5,.5)
        c:SetSizeDelta(0,0);c:SetAnchoredPosition(0,0);c:SetLocalScale(1,1,1)
    end)
    local s
    if cw / ch >= DESIGN_W / DESIGN_H then s = ch / DESIGN_H else s = cw / DESIGN_W end
    self.s = s
    self.W, self.H = cw / s, ch / s
    -- Full-bleed graphics have a bounded gutter beyond the safe content area.
    -- Text, buttons, portraits and touch coordinates keep W/H and the same scale.
    self.coverW=self.W+2*math.max(120,self.W*.06)
    self.coverH=self.H+2*math.max(80,self.H*.04)
    self.canvasBacking:size(self.coverW*s,self.coverH*s)
    self.view:pos(0, 0):scale(s, s)
    if self.scene and self.scene.resize then self.scene:resize() end
    return true
end

function App:cover(layer,color,alpha)
    return layer:rect(0,0,self.coverW,self.coverH,color,alpha)
end

function App:getMenuPair()
    if not self.menuPair then
        local count=#require('gf_roster')
        local a=math.random(count)
        local b=count>1 and math.random(count-1) or a
        if count>1 and b>=a then b=b+1 end
        self.menuPair={a,b}
    end
    return self.menuPair
end

function App:go(name, args)
    if name=='title' and not self.initialNoticeShown and not self.env.initialNoticeShown then name='notice';args={} end
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
    if self.closed or self:advanceExit(dt) then return end
    self.callbackDt=dt
    self:sampleFrameRate(dt)
    self:netPump() -- receive before any pool maintenance or drawing
    if self.initialAssets and self:advanceInitialAssets(dt) then return end
    if self.poolNext then
        self:fit(false)
        self:netPump()
        if #G.trash>0 then G.flushTrash(64) end
        G.flushRetired(96)
        if self:advanceScenePool() then return end
    end
    local sim=self.scene and self.scene.sim
    local phase=sim and sim.phase
    local safeBoundary=not sim or phase=='over' or (phase=='ko' and sim.phaseT>=90)
    G.manageImagePool(phase,safeBoundary)
    if dt > 0.25 then
        self.droppedTime=(self.droppedTime or 0)+dt-0.25
        dt = 0.25
    end
    self.t = self.t + dt
    if dt > 0 then self.fps = self.fps * 0.9 + (1 / dt) * 0.1 end
    self.fitT = (self.fitT or 0) + dt
    if self.fitT > 0.5 then self.fitT = 0; self:fit(false) end
    self.input:poll()
    if #G.trash > 0 then G.flushTrash(64) end
    G.flushRetired(64)
    self.acc = self.acc + dt
    local steps = 0
    -- Restore the desktop callback cap used before the mobile-only change.
    local maxSteps=self:isMobile() and 8 or 4
    while self.acc >= STEP and steps < maxSteps do
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
    if self.acc > STEP * maxSteps then
        self.droppedTime=(self.droppedTime or 0)+self.acc-STEP*maxSteps
        self.acc=STEP*maxSteps
    end
    local sc = self.scene
    if sc and sc.draw then sc:draw(self.acc / STEP, dt) end
    self:samplePerformance(self.callbackDt or dt)
    self.audio:update(dt)
    self:drawTransition()
    self:drawFrameRate()
    if self.debug then self:drawDebug() elseif self.debugLayer then self.debugLayer:clear() end
end

function App:switch(name, args) self.nextScene = {name, args} end

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

-- Cover the previous scene while the second image pool grows in frame batches.
require('gf_app_network')(App)
require('gf_app_exit')(App)
require('gf_app_transition')(App)
require('gf_app_metrics')(App)
require('gf_app_loading')(App)
require('gf_app_recovery')(App)
return App
end
