-- Boot splash: a star of light opens a horizon line, the project name rises, everything fades
-- into the title. Meanwhile the title backdrop painting is built off-screen. Any key skips.
local G = require('gf_gfx')
local U = require('gf_util')
local UI = require('gf_ui')
local Paint = require('gf_paint')

local S = {}
S.__index = S

local TITLE_STAGE = 'mondstadt'

function S.new(app)
    local self = setmetatable({app = app, t = 0}, S)
    self.L = G.layer(app.layers.top)
    local key = Paint.available[TITLE_STAGE] and TITLE_STAGE or next(Paint.available)
    if key then
        self.bd = app:backdrop(key)
        self.bd.root:on(false)
    end
    return self
end

function S:tick()
    local app = self.app
    self.t = self.t + 1 / 60
    if self.bd then self.bd:step(220) end
    for _, a in ipairs(app.input:menu()) do
        if a == 'ok' or a == 'back' or a == 'pause' then self.t = math.max(self.t, 3.0) end
    end
    if self.t >= 3.2 and not self.left then
        self.left = true
        app:travel('title', nil, {236, 229, 216})
    end
end

function S:draw()
    local app = self.app
    local L = self.L
    local t = self.t
    L:begin()
    L:rect(0, 0, app.W + 60, app.H + 60, {4, 5, 10}, 1)
    local open = U.ease.outCubic(U.clamp((t - 0.5) / 1.0, 0, 1))
    local fade = 1 - U.clamp((t - 2.5) / 0.6, 0, 1)
    -- horizon line and star
    L:shape(G.ELLIPSE, 0, 0, 900 * open, 220 * open, {255, 230, 170}, 0.18 * fade, 0, 0.5)
    L:rect(0, 0, 1100 * open, 2, {255, 244, 220}, 0.9 * fade)
    L:shape(G.STAR4, 0, 0, 90 * open + 10, 90 * open + 10, {255, 255, 255}, fade, t * 40)
    L:shape(G.STAR4, 0, 0, 34 * open, 34 * open, {255, 230, 170}, fade, -t * 60)
    -- project name
    local ta = U.clamp((t - 1.1) / 0.5, 0, 1) * fade
    L:label('千星奇域 · 同人格斗企划', 0, -54 - 10 * (1 - ta), 800, 40, 24, UI.CREAM, 'c', {0, 0, 0, 160}, ta)
    L:label('GENSHIN FIGHTER PROJECT', 0, -90, 800, 30, 15, UI.DIM, 'c', nil, ta)
    L:finish()
end

function S:exit() self.L:free() end

return S
