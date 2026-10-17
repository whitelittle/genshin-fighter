__loaders['gf_scene_stageview'] = function()
local G = require('gf_gfx')
local Stage = require('gf_stage')

local S = {}
S.__index = S

function S.new(app, args)
    local self = setmetatable({app = app, args = args}, S)
    self.stage = Stage.new(app, app.layers.back, args.stage or 'mondstadt')
    while not self.stage:buildStep(5000) do end
    self.cx = args.cx or 0
    self.zoom = args.zoom or 1
    return self
end

function S:tick() end

function S:draw()
    local app = self.app
    self.stage:camera(self.cx, self.zoom, -app.H / 2 + 150, 0, 0)
end

function S:exit() self.stage:free() end

return S
end
