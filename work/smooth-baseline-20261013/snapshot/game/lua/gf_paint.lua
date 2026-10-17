-- Paintings: stage artwork approximated by ~1,000 translucent rotated ellipses / rectangles
-- (fitted offline, game/tools/build_stages.py). Built a slice per frame into one group;
-- once built they are static controls (the camera only moves the group).
local G = require('gf_gfx')
local U = require('gf_util')

local P = {}
P.__index = P

local list = require('gf_bglist')
P.available = {}
for _, k in ipairs(list) do P.available[k] = true end

-- part: 'full' | 'ground'; parent: group
function P.new(parent, key, part, limit)
    local data = require('gf_bg_' .. key)
    local src = part == 'ground' and data.ground or data
    if not src then return nil end
    local self = setmetatable({key = key, data = data, src = src, i = 0, nodes = {}, done = false}, P)
    self.group = G.group(parent)
    self.n = math.min(src.n, limit or src.n)
    self.bytes = nil
    self.w, self.h = src.w, src.h
    -- panel background
    local bg = src.bg
    local base
    if part == 'ground' then
        -- soft-edged so the strip's top melts into the backdrop (shapes fade there too)
        base = G.image(self.group, G.ELLIPSE)
        base:pos(0, -src.h * 0.55):size(src.w * 4, src.h * 2.3):color(bg[1], bg[2], bg[3], 255):soft(0.3):on(true)
    else
        base = G.image(self.group, G.RECT)
        base:pos(0, 0):size(src.w * 1.6, src.h * 1.6):color(bg[1], bg[2], bg[3], 255):on(true)
    end
    self.nodes[1] = base
    return self
end

-- build up to `budget` shapes; returns true when complete
function P:step(budget)
    if self.done then return true end
    if not self.bytes then
        -- decode over a few frames (a whole painting in one frame costs ~140k instructions)
        self.dec = self.dec or U.decoder(self.src.d)
        if not self.dec:step(budget * 40) then return false end
        self.bytes, self.dec = self.dec.bytes, nil
        return false
    end
    local b = self.bytes
    local stop = math.min(self.n, self.i + budget)
    for k = self.i + 1, stop do
        local o = (k - 1) * 12
        local b1, b2, b3, b4, b5, b6 = b[o + 1], b[o + 2], b[o + 3], b[o + 4], b[o + 5], b[o + 6]
        local x = ((b1 << 4) | (b2 >> 4)) - 2048
        local y = (((b2 & 15) << 8) | b3) - 2048
        local w = (b4 << 4) | (b5 >> 4)
        local h = ((b5 & 15) << 8) | b6
        local rk = (b[o + 7] << 8) | b[o + 8]
        local node = G.image(self.group, (rk & 1) == 1 and G.ELLIPSE or G.RECT)
        node:pos(x, y):size(w, h):rot(rk >> 1):color(b[o + 9], b[o + 10], b[o + 11], b[o + 12]):on(true)
        self.nodes[#self.nodes + 1] = node
    end
    self.i = stop
    if stop >= self.n then
        self.done = true
        self.bytes = nil
        return true
    end
    return false
end

function P:free(later)
    if later then
        self.group:on(false)
        G.releaseLater(self.group)
        for _, n in ipairs(self.nodes) do G.releaseLater(n) end
        self.nodes = {}
        return
    end
    for _, n in ipairs(self.nodes) do G.release(n) end
    self.nodes = {}
    G.release(self.group)
end

return P
