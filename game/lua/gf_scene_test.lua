-- Developer scene: draws a few pictures to check the art pipeline (game/tests only).
local G = require('gf_gfx')
local Art = require('gf_art')

local S = {}
S.__index = S

function S.new(app, args)
    local self = setmetatable({app = app}, S)
    local L = app.layers
    self.bg = G.layer(L.back)
    self.bg:begin()
    self.bg:rect(0, 0, app.W, app.H, {24, 26, 40})
    self.bg:rect(0, -330, app.W, 240, {44, 40, 58})
    self.bg:finish()
    local keys = args.keys or {'raidenshogun', 'furina'}
    self.bmps = {}
    for i, key in ipairs(keys) do
        local tier = (i % 2 == 1) and 'hi' or 'lo'
        local img = Art.pose(key, tier, args.pose or 'idle')
        local b = G.bitmap(L.world)
        b:draw(img)
        b.node:pos(-500 + (i - 1) * 330, -210):scale(img.u * (i % 2 == 1 and 1 or -1), img.u):on(true)
        self.bmps[#self.bmps + 1] = b
    end
    local faces = G.bitmap(L.ui)
    local list = {}
    for i, c in ipairs(Art.roster) do
        local f = Art.face(c.key)
        list[#list + 1] = {img = f, ox = 120 + ((i - 1) % 4) * 120, oy = 260 - ((i - 1) // 4) * 130, s = 3.2}
    end
    faces:drawMany(list)
    faces.node:on(true)
    self.ui = G.layer(L.ui)
    self.ui:begin()
    self.ui:label('原神格斗 v2 · 管线测试', 0, 400, 900, 60, 40, {255, 236, 190}, 'c', {60, 30, 10})
    self.ui:finish()
    return self
end

function S:tick() end
function S:draw() end

return S
