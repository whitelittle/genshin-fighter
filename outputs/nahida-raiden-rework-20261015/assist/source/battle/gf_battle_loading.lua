__loaders['gf_battle_loading']=function()
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
function S:loadTick()
    if G.retiredPending()>0 then return false end
    -- App may run four simulation ticks per host update. Loading gets one slice.
    if self.lastLoadUpdate == self.app.t then return false end
    self.lastLoadUpdate = self.app.t
    self.loadStep = self.loadStep + 1
    local app = self.app
    local done = true
    for _, j in ipairs(self.prep) do
        if not j.finished then
            j.finished = j:step(9000)
            done = false
            break
        end
    end
    if not self.stage:buildStep(160) then done = false end
    if done and not self.views then
        self.views = {FView.new(app, self.lay, self.sim.f[1], self.tier), FView.new(app, self.lay, self.sim.f[2], self.tier)}
        self.fx = FX.new(app, self.lay.fx, app.layers.top, 220, 30, 18)
        for _, v in ipairs(self.views) do v.fx = self.fx end
        self.projL = G.layer(self.lay.proj)
        self.hud = Hud.new(app, app.layers.hud, self.sim)
        self.annL = G.layer(app.layers.top)
        self.burstBg = G.layer(app.layers.back)
        self.burstEye=G.bitmap(app.layers.back);self.burstEye.node:on(false)
        self:touchControls()
        self.cut = {L = G.layer(app.layers.top), bmp = G.bitmap(app.layers.top)}
        self.cut.placeholder=self.cut.bmp
        self.cut.bmp.node:on(false)
        self.warm = 0
        return false
    end
    if self.views then
        -- warm-up: write the first poses of both fighters before showing the fight
        self.warm = self.warm + 1
        local reserved=true
        if not require('gf_character_cinematic_view').reserve(self,320) then reserved=false end
        if not require('gf_character_cinematic_view').reserveLegacy(self,160) then reserved=false end
        for _,v in ipairs(self.views) do
            if not v:reserveBody(320) then reserved=false end
            v:draw(320)
            if not v.front then reserved=false end
            if not v:warmLocomotion(160) then reserved=false end
            if not v:warmFlash(160) then reserved=false end
        end
        if not require('gf_assist_view').prepare(self,240) then reserved=false end
        self:camera(true)
        if self.warm >= 4 and reserved then
            -- Warm the announcement slots and HUD under the curtain.
            self:banner('第一回合','ROUND 1',UI.GOLD2,40,72)
            self:drawBanners();self.banners={};self.annL:clear()
            self.hud:draw()
            self:setupAI()
            self.state = 'run'
            self:curtainOpen()
            return true
        end
    end
    return false
end


end
end
