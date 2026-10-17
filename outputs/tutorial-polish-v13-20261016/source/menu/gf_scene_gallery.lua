__loaders['gf_scene_gallery'] = function()
local G = require('gf_gfx')
local UI = require('gf_ui')

local S = {}
S.__index = S

local ELS = {'pyro', 'hydro', 'anemo', 'electro', 'dendro', 'cryo', 'geo'}

function S.new(app,args)
    local self = setmetatable({app = app, t = 0,teamShape=args and args.teamShape}, S)
    self.L = G.layer(app.layers.ui)
    if self.teamShape then return self end
    self.menu = UI.menu(app, app.layers.ui, {{id = 'a', label = '街机模式', sub = '说明文字'}, {id = 'b', label = '对战模式'},
        {id = 'c', label = '画质', value = function() return '高' end}},
        {x = 380, y = -150, w = 520, h = 80, gap = 10, size = 36, numbers = true})
    return self
end

function S:tick() self.t = self.t + 1 / 60; if self.menu then self.menu:input(self.app.input:menu()) end end

function S:draw()
    local app = self.app
    local W, H = app.W, app.H
    local L = self.L
    L:begin()
    app:cover(L,UI.NAVY,1)
    if self.teamShape then
        for p=1,2 do
            local y=100-(p-1)*110
            UI.parallelogram(L,0,y,720,70,UI.NAVY2,1,UI.GOLD)
            for i=1,3 do UI.parallelogram(L,-50+(i-1)*150,y,130,48,UI.NAVY,1,UI.GOLD) end
            L:label(p..'P',-270,y,100,40,24,UI.GOLD,'c')
        end
        L:finish();return
    end
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

function S:exit() self.L:free(); if self.menu then self.menu:free() end end

return S
end
