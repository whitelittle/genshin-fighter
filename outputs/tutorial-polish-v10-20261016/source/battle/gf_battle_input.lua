__loaders['gf_battle_input']=function()
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
function S:touchControls()
    local app = self.app
    local want = app.settings.touch == 'on' or (app.settings.touch == 'auto' and app.input:device() == 'touch')
    if self.mode == 'demo' then return end
    if not want then self.hud:bindSkillButtons(self.side or 1); return end
    if self.touch then self.touch:layout() return end
    self.hud.compact = true
    self.touch = require('gf_touch').new(app, app.layers.top, self.sim.f[self.side or 1], function() if not self.paused then self:openPause() end end)
end

function S:setupAI()
    local cpu = (not self.online) and self.args.cpu or {}
    self.ai = {}
    for i = 1, 2 do
        if cpu[i] then self.ai[i] = AI.new(self.sim, i, cpu[i], 97 + i * 31) end
    end
end


end
end
