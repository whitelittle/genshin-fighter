__loaders['gf_backdrop'] = function()
-- Menu backdrop: a stage painting with a slow Ken Burns drift, a navy veil, a vignette and
-- floating sparks. Owned by the app so title -> menu -> options never rebuild it.
local G = require('gf_gfx')
local U = require('gf_util')
local Paint = require('gf_paint')

local B = {}
B.__index = B

function B.new(app, parent, key, opts)
    opts = opts or {}
    local self = setmetatable({app = app, key = key, opts = opts, ready = false, t = 0}, B)
    self.root = G.group(parent)
    self.kb = G.group(self.root)                 -- Ken Burns group
    if Paint.available[key] then
        self.paint = Paint.new(self.kb, key, 'full', app.quality == 'lo' and 700 or nil)
    end
    self.L = G.layer(self.root)                   -- veil + vignette (immediate)
    self.sparks = {}
    return self
end

function B:step(n)
    if self.ready then return true end
    if self.paint and not self.paint:step(n) then return false end
    self.ready = true
    -- slow drift: scale and pan back and forth
    local s = self.opts.scale or 1.25
    self.kb:scale(s, s):pos(0, self.opts.y or 40)
    G.pingpong(self.kb, {localScaleX = s * 1.08, localScaleY = s * 1.08, anchoredPositionX = -60, anchoredPositionY = (self.opts.y or 40) + 20},
               {localScaleX = s, localScaleY = s, anchoredPositionX = 40, anchoredPositionY = self.opts.y or 40}, 18, 'InOutSine')
    -- rising sparks
    for i = 1, 14 do
        local n = G.image(self.root, G.STAR4)
        local x = -900 + U.hash(i * 37) * 1800
        local y0 = -520 - U.hash(i * 11) * 100
        local sz = 10 + U.hash(i * 5) * 14
        n:pos(x, y0):size(sz, sz):color(255, 236, 190, 200):on(true)
        local t = n:tween({anchoredPositionY = 560, anchoredPositionX = x + (U.hash(i * 3) - 0.5) * 300, localRotationZ = 270},
                          7 + U.hash(i * 17) * 6, 'Linear')
        if t then pcall(function() t:SetLoops(-1) end) end
        self.sparks[#self.sparks + 1] = n
    end
    return true
end

-- veil: 0..1 darkness over the painting; tint: colour of the veil
function B:draw(veil, tint)
    local app = self.app
    local W, H = app.W, app.H
    local L = self.L
    L:begin()
    tint = tint or {10, 12, 28}
    L:rect(0, 0, W + 80, H + 80, tint, veil or 0.45)
    -- vignette: dark feathered edges
    L:shape(G.ELLIPSE, -W / 2, 0, W * 0.7, H * 1.6, {4, 5, 12}, 0.55, 0, 0.5)
    L:shape(G.ELLIPSE, W / 2, 0, W * 0.7, H * 1.6, {4, 5, 12}, 0.55, 0, 0.5)
    L:shape(G.ELLIPSE, 0, -H / 2, W * 1.6, H * 0.6, {4, 5, 12}, 0.6, 0, 0.5)
    L:finish()
end

-- later: hide now, hand the nodes back to the pools over the next frames (see G.releaseLater)
function B:free(later)
    if later then
        self.root:on(false)
        G.releaseLater(self.root)
        G.releaseLater(self.kb)
        if self.paint then self.paint:free(true) end
        self.L:free()
        for _, n in ipairs(self.sparks) do G.releaseLater(n) end
        return
    end
    if self.paint then self.paint:free() end
    self.L:free()
    for _, n in ipairs(self.sparks) do G.release(n) end
    G.release(self.kb)
    G.release(self.root)
end

return B
end
