-- Design sheet (debug scene): element emblems large and small, badges, keycaps, chevrons,
-- slabs, a menu sample. Used to tune the front-end kit; not reachable from the menus.
local G = require('gf_gfx')
local UI = require('gf_ui')

local S = {}
S.__index = S

local ELS = {'pyro', 'hydro', 'anemo', 'electro', 'dendro', 'cryo', 'geo'}

function S.new(app)
    local self = setmetatable({app = app, t = 0}, S)
    self.L = G.layer(app.layers.ui)
    self.menu = UI.menu(app, app.layers.ui, {{id = 'a', label = '街机模式', sub = '说明文字'}, {id = 'b', label = '对战模式'},
        {id = 'c', label = '画质', value = function() return '高' end}},
        {x = 380, y = -150, w = 520, h = 80, gap = 10, size = 36, numbers = true})
    return self
end

function S:tick() self.t = self.t + 1 / 60; self.menu:input(self.app.input:menu()) end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    local L = self.L
    L:begin()
    L:rect(0, 0, W + 40, H + 40, UI.NAVY, 1)
    for i, el in ipairs(ELS) do
        local x = -W / 2 + 120 + (i - 1) * 200
        L:shape(G.ELLIPSE, x, 250, 170, 170, UI.NAVY2, 1)
        UI.element(L, el, x, 250, 150, 1)
        UI.badge(L, el, x, 80, 64, 1)
        UI.element(L, el, x + 60, 80, 24, 1)
        L:label(el, x, 160, 180, 30, 18, UI.GREY, 'c', nil, 1)
    end
    UI.prompt(L, -W / 2 + 120, -60, 'J', '确认')
    UI.chevron(L, -W / 2 + 320, -60, 30, UI.WHITE, 1)
    UI.slab(L, -W / 2 + 500, -60, 200, 50, UI.CREAM, 1)
    UI.constellation(L, -W / 2 + 300, -280, 120, self.t * 10, UI.WHITE, 1)
    L:finish()
    self.menu:draw(1)
end

function S:exit() self.L:free(); self.menu:free() end

return S
