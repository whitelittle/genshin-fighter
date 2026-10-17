__loaders['gf_battle_network']=function()
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
function S:netTick(idle)
    local o = self.online
    local m = o.match
    if not m then return false end
    local app = self.app
    local mask = 0
    if not idle then mask = (app.input:pad(1).now or 0) | (app.input:pad(2).now or 0) end
    self.netEvents = {}
    Online.matchStep(o, mask)
    local st = m.session.state
    if st ~= self.sim then self:rebind(st) end
    for _,record in ipairs(self.netEvents) do
        self:rebind(record.state)
        app.audio.eventTime=record.frame/60
        self:events(record.state.events)
        if self.stage.L.lightning and record.state.tick%420==200 then
            if self.stage:thunder() then app.audio:play(app.audio.ID.ehit.electro) end
        end
        app.audio.eventTime=nil
    end
    self:rebind(st)
    -- the other side vanished or the states differ: end the match here
    if not self.netEnd then
        local why
        if m.session.desync then why = '同步异常，对局中止'
        elseif Online.peerGone(o) or Online.hostLost(o) then why = '对手已断开连接' end
        if why then
            self.netEnd = why
            self:banner('对局结束', why, UI.CREAM, 150, 90)
            if self.endT <= 0 then self.endT = 160 end
        end
    end
    return true
end


end
end
