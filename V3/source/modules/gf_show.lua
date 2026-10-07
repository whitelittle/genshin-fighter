__loaders['gf_show'] = function()
local G = require('gf_gfx')
local Art = require('gf_art')
local K = require('gf_kits')

local S = {}
S.__index = S

function S.new(parent)
    local self = setmetatable({}, S)
    self.root = G.group(parent)
    self.glow = G.image(self.root, G.ELLIPSE)
    self.glow:on(false)
    self.shadow = G.image(self.root, G.ELLIPSE)
    self.shadow:on(false)
    self.bmp = G.bitmap(self.root)
    return self
end

function S:set(key, tier, pose, x, y, s, face, glowA)
    s, face = s or 1, face or 1
    local img = Art.pose(key, tier, pose or 'idle')
    self.bmp:draw(img, key .. tier .. (pose or 'idle'))
    self.bmp.node:pos(x, y):scale(img.u * s * face, img.u * s):on(true)
    local ec = K.elementColor[Art.byKey[key].element] or {255, 255, 255}
    self.glow:pos(x, y + 170 * s):size(420 * s, 520 * s):color(ec[1], ec[2], ec[3], glowA or 70):soft(0.5):on(true)
    self.shadow:pos(x, y + 4):size(240 * s, 34 * s):color(0, 0, 0, 120):soft(0.4):on(true)
    self.key, self.x, self.y, self.s = key, x, y, s
end

function S:hide()
    self.bmp.node:on(false)
    self.glow:on(false)
    self.shadow:on(false)
end

function S:free()
    self.bmp:free()
    G.release(self.glow)
    G.release(self.shadow)
    G.release(self.root)
end

return S
end
