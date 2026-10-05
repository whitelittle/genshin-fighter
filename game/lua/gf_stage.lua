-- Stages: vector backgrounds from client primitives (rect / ellipse / triangle / star / ring),
-- grouped in parallax layers. Built once per match (spread over frames), animated by looping
-- native tweens (zero Lua per frame), moved by the camera with one write per layer.
--
-- World space: floor at y = 0, fighters within x = -1100..1100, sky up to ~y = 1100.
local G = require('gf_gfx')
local U = require('gf_util')
local Paint = require('gf_paint')

local St = {}
St.__index = St

local RECT, ELLIPSE, TRI, STAR4, STAR5, RING = G.RECT, G.ELLIPSE, G.TRI, G.STAR4, G.STAR5, G.RING

-- animated foreground in front of the fighters (parallax 1.3): dark out-of-focus plants or
-- rocks along the bottom edge that sway, and large soft motes drifting across the screen
local FORE = {
    mondstadt = {kind = 'grass', col = {22, 44, 30}, motes = {shape = ELLIPSE, col = {255, 252, 236}, n = 7, size = 30, soft = 0.5, move = 'float'}},
    liyue = {kind = 'rocks', col = {44, 30, 18}, motes = {shape = ELLIPSE, col = {255, 196, 70}, n = 8, size = 34, move = 'fall', leaf = true}},
    inazuma = {kind = 'grass', col = {34, 20, 46}, motes = {shape = ELLIPSE, col = {255, 176, 214}, n = 9, size = 30, move = 'fall', leaf = true}},
    sumeru = {kind = 'rocks', col = {66, 42, 20}, motes = {shape = RECT, col = {255, 222, 168}, n = 8, size = 220, move = 'drift', streak = true}},
    fontaine = {kind = 'grass', col = {16, 36, 56}, motes = {shape = RING, col = {214, 242, 255}, n = 8, size = 44, move = 'float'}},
    natlan = {kind = 'rocks', col = {48, 22, 12}, motes = {shape = ELLIPSE, col = {255, 140, 50}, n = 12, size = 16, soft = 0.3, move = 'float', glow = true}},
    snezhnaya = {kind = 'rocks', col = {28, 34, 52}, motes = {shape = ELLIPSE, col = {255, 255, 255}, n = 14, size = 34, soft = 0.5, move = 'fall'}},
}


local function hsh(n) return U.hash(n) end

-- shape list helpers ----------------------------------------------------------
local function add(list, shape, x, y, w, h, col, rot, soft, anim)
    list[#list + 1] = {shape, x, y, w, h, col, rot or 0, soft or 0, anim}
end

-- vertical gradient of `n` bands between colours (top -> bottom)
local function gradient(list, x, y0, y1, w, cols, n)
    local h = (y1 - y0) / n
    for i = 0, n - 1 do
        local t = i / (n - 1)
        local seg = t * (#cols - 1)
        local a = math.floor(seg) + 1
        local b = math.min(#cols, a + 1)
        local c = U.mix(cols[a], cols[b], seg - (a - 1))
        add(list, RECT, x, y1 - h * (i + 0.5), w, h + 1.5, c)
    end
end

local function mountains(list, seed, y, h, col, n, w, span)
    for i = 0, n - 1 do
        local x = -span / 2 + (i + hsh(seed + i)) * span / n
        local hh = h * (0.6 + hsh(seed * 3 + i) * 0.7)
        add(list, TRI, x, y + hh / 2, w * (0.8 + hsh(seed + i * 7) * 0.6), hh, col)
    end
end

-- stage definitions ----------------------------------------------------------
St.list = {}

St.list.mondstadt = {
    name = '蒙德 · 风起地', sub = '风与蒲公英的牧歌之城', bgm = nil,
    ambient = {255, 196, 140}, floorY = 0,
    build = function(L)
        local sky, far, mid, near, floor = L.sky, L.far, L.mid, L.near, L.floor
        gradient(sky, 0, -200, 1500, 5200, {{70, 60, 140}, {190, 110, 150}, {255, 170, 110}, {255, 214, 150}}, 22)
        add(sky, ELLIPSE, 300, 420, 260, 260, {255, 236, 190}, 0, 0.5)               -- sun glow
        add(sky, ELLIPSE, 300, 420, 140, 140, {255, 246, 220})
        for i = 1, 7 do                                                               -- clouds
            local x, y = -1600 + i * 480, 700 + hsh(i) * 300
            add(sky, ELLIPSE, x, y, 360, 70, {255, 210, 200}, 0, 0.6, {dx = 160, dur = 26 + i * 3})
            add(sky, ELLIPSE, x + 80, y + 20, 220, 60, {255, 228, 214}, 0, 0.6, {dx = 160, dur = 26 + i * 3})
        end
        mountains(far, 3, 120, 380, {120, 110, 160}, 9, 900, 5600)
        -- Mondstadt city on the far hill: walls, towers, cathedral spire
        add(far, ELLIPSE, -900, 120, 1700, 380, {106, 128, 120})
        for i = 0, 8 do
            local x = -1500 + i * 140
            local hh = 120 + hsh(40 + i) * 160
            add(far, RECT, x, 250 + hh / 2, 90, hh, {150, 140, 170})
            add(far, TRI, x, 250 + hh + 40, 110, 80, {120, 90, 140})
        end
        add(far, RECT, -980, 560, 70, 480, {170, 160, 186})
        add(far, TRI, -980, 860, 100, 160, {130, 96, 150})
        -- windmills (mid) with turning blades
        for i = 0, 2 do
            local x = -700 + i * 900
            add(mid, RECT, x, 260, 50, 300, {150, 110, 90})
            add(mid, TRI, x, 430, 90, 60, {120, 70, 60})
            for b = 0, 1 do
                add(mid, RECT, x, 410, 20, 280, {240, 230, 210}, b * 90, 0, {spin = 360, dur = 9 + i * 2})
            end
            add(mid, ELLIPSE, x, 410, 30, 30, {120, 80, 60})
        end
        -- rolling hills
        add(mid, ELLIPSE, -1400, 60, 2200, 360, {92, 150, 90})
        add(mid, ELLIPSE, 1100, 40, 2400, 330, {80, 140, 84})
        -- Windrise tree
        add(near, RECT, 1500, 320, 90, 640, {90, 64, 50})
        for i = 1, 9 do
            add(near, ELLIPSE, 1500 + (hsh(i * 5) - 0.5) * 520, 640 + hsh(i * 9) * 260, 300, 200, {70 + i * 4, 130 + i * 3, 80})
        end
        -- floor: stone plaza
        add(floor, RECT, 0, -260, 6000, 520, {120, 112, 104})
        for i = -14, 14 do add(floor, RECT, i * 200, -40, 196, 74, {140 + (i % 2) * 10, 130, 118}) end
        for i = -10, 10 do add(floor, RECT, i * 260 + 130, -130, 256, 90, {128, 120, 110}) end
        add(floor, RECT, 0, 6, 6000, 12, {170, 160, 140})
        -- dandelion seeds drifting
        L.particles = {kind = 'float', n = 14, col = {255, 250, 235}, shape = STAR4, size = 14, rise = 220, drift = 260, dur = 7}
    end,
}

St.list.liyue = {
    name = '璃月港 · 海灯节', sub = '万家灯火，契约之城的夜', ambient = {255, 190, 120},
    build = function(L)
        local sky, far, mid, near, floor = L.sky, L.far, L.mid, L.near, L.floor
        gradient(sky, 0, -200, 1500, 5200, {{8, 12, 40}, {24, 30, 80}, {60, 50, 110}, {150, 90, 110}}, 22)
        for i = 1, 40 do                                                                -- stars
            add(sky, STAR4, -2400 + hsh(i) * 4800, 500 + hsh(i * 3) * 900, 8 + hsh(i * 7) * 10, nil, {255, 250, 220}, 0, 0,
                i % 3 == 0 and {blink = true, dur = 1.4 + hsh(i) * 2} or nil)
        end
        add(sky, ELLIPSE, -500, 950, 200, 200, {255, 244, 210}, 0, 0.45)              -- moon glow
        add(sky, ELLIPSE, -500, 950, 110, 110, {255, 250, 230})
        -- stone forest pillars
        for i = 0, 10 do
            local x = -2600 + i * 520 + hsh(i) * 200
            local h = 500 + hsh(i * 5) * 400
            add(far, RECT, x, h / 2, 140 + hsh(i * 3) * 80, h, {44, 50, 92})
            add(far, ELLIPSE, x, h, 220, 80, {36, 60, 70})
        end
        -- harbor pavilions with red roofs and warm windows
        for i = 0, 7 do
            local x = -1800 + i * 520
            local h = 200 + hsh(i + 50) * 160
            add(mid, RECT, x, h / 2, 300, h, {60, 30, 34})
            add(mid, TRI, x, h + 50, 420, 110, {150, 40, 40})
            add(mid, RECT, x, h + 8, 380, 16, {200, 160, 80})
            for wnd = 0, 2 do add(mid, RECT, x - 90 + wnd * 90, h * 0.55, 46, 50, {255, 200, 110}, 0, 0, {blink = true, dur = 2 + hsh(i * 9 + wnd) * 3, lo = 0.6}) end
        end
        -- hanging lanterns
        for i = 0, 11 do
            local x = -1650 + i * 300
            add(near, RECT, x, 520, 4, 160, {80, 40, 30})
            add(near, ELLIPSE, x, 430, 90, 90, {255, 150, 60}, 0, 0.6, {blink = true, dur = 1.6 + hsh(i) * 1.2, lo = 0.7})
            add(near, ELLIPSE, x, 430, 46, 62, {255, 90, 50})
        end
        -- water and dock
        add(floor, RECT, 0, -300, 6000, 600, {30, 30, 52})
        for i = -16, 16 do add(floor, RECT, i * 180, -36, 176, 70, {96 + (i % 2) * 8, 62, 48}) end
        for i = -12, 12 do add(floor, RECT, i * 240, -120, 236, 80, {84, 54, 44}) end
        add(floor, RECT, 0, 6, 6000, 12, {200, 150, 90})
        L.particles = {kind = 'float', n = 12, col = {255, 170, 90}, shape = ELLIPSE, size = 26, rise = 900, drift = 120, dur = 14, soft = 0.5}
    end,
}

St.list.inazuma = {
    name = '稻妻 · 鸣神大社', sub = '永恒之下，雷光与樱的神社', ambient = {220, 160, 255},
    build = function(L)
        local sky, far, mid, near, floor = L.sky, L.far, L.mid, L.near, L.floor
        gradient(sky, 0, -200, 1500, 5200, {{30, 16, 60}, {70, 40, 110}, {130, 80, 150}, {200, 140, 170}}, 22)
        for i = 1, 6 do add(sky, ELLIPSE, -2000 + i * 700, 900 + hsh(i) * 250, 700, 140, {60, 40, 90}, 0, 0.6, {dx = 120, dur = 20 + i * 2}) end
        -- distant thunder flash band
        add(sky, RECT, 0, 1000, 6000, 600, {230, 200, 255}, 0, 0.5, {flash = true, dur = 5.5})
        -- mountain with the giant sakura
        add(far, TRI, -200, 360, 2600, 720, {60, 40, 80})
        add(far, TRI, 1500, 280, 1800, 560, {70, 46, 90})
        for i = 1, 12 do
            add(far, ELLIPSE, -200 + (hsh(i * 3) - 0.5) * 700, 760 + hsh(i * 11) * 260, 300, 200, {240, 140, 200})
        end
        add(far, RECT, -200, 600, 70, 300, {70, 40, 50})
        -- torii gates
        for i = 0, 2 do
            local x = -900 + i * 900
            local s = 1 - i * 0.12
            add(mid, RECT, x - 170 * s, 230 * s, 34 * s, 460 * s, {200, 40, 50})
            add(mid, RECT, x + 170 * s, 230 * s, 34 * s, 460 * s, {200, 40, 50})
            add(mid, RECT, x, 470 * s, 480 * s, 34 * s, {40, 20, 30})
            add(mid, RECT, x, 420 * s, 400 * s, 22 * s, {200, 40, 50})
        end
        -- sakura branches in front
        for i = 1, 10 do
            add(near, ELLIPSE, -1700 + hsh(i * 13) * 400, 900 + hsh(i * 2) * 200, 280, 170, {255, 170, 210}, 0, 0.3)
            add(near, ELLIPSE, 1700 - hsh(i * 17) * 400, 950 + hsh(i * 4) * 200, 280, 170, {250, 150, 200}, 0, 0.3)
        end
        add(floor, RECT, 0, -260, 6000, 520, {70, 50, 60})
        for i = -15, 15 do add(floor, RECT, i * 190, -36, 186, 70, {120 + (i % 2) * 10, 80, 70}) end
        for i = -12, 12 do add(floor, RECT, i * 250 + 120, -120, 246, 80, {104, 70, 64}) end
        add(floor, RECT, 0, 6, 6000, 12, {230, 160, 200})
        L.particles = {kind = 'fall', n = 18, col = {255, 180, 215}, shape = ELLIPSE, size = 18, drift = 300, dur = 6}
        L.lightning = true
    end,
}

St.list.snezhnaya = {
    name = '至冬 · 冰之宫', sub = '冰封的北国，女皇的宫殿', ambient = {180, 220, 255},
    build = function(L)
        local sky, far, mid, near, floor = L.sky, L.far, L.mid, L.near, L.floor
        gradient(sky, 0, -200, 1500, 5200, {{20, 30, 70}, {60, 90, 150}, {150, 190, 230}, {220, 236, 250}}, 22)
        for i = 1, 3 do add(sky, ELLIPSE, -1200 + i * 800, 1050, 900, 120, {120, 255, 210}, -6, 0.6, {blink = true, dur = 4 + i, lo = 0.3}) end  -- aurora
        mountains(far, 9, 100, 560, {140, 170, 210}, 10, 1000, 6000)
        mountains(far, 19, 60, 360, {200, 220, 240}, 8, 800, 6000)
        -- palace spires
        for i = 0, 6 do
            local x = -900 + i * 300
            local h = 360 + (i == 3 and 340 or hsh(i * 7) * 200)
            add(mid, RECT, x, h / 2, 120, h, {170, 200, 230})
            add(mid, TRI, x, h + 90, 150, 180, {120, 160, 210})
            add(mid, RECT, x, h * 0.6, 40, 70, {255, 240, 190}, 0, 0, {blink = true, dur = 3 + hsh(i), lo = 0.6})
        end
        add(near, TRI, -1700, 300, 500, 700, {220, 240, 255})
        add(near, TRI, 1750, 260, 520, 620, {210, 232, 250})
        add(floor, RECT, 0, -260, 6000, 520, {170, 196, 220})
        for i = -15, 15 do add(floor, RECT, i * 190, -36, 186, 70, {196 + (i % 2) * 10, 220, 240}) end
        for i = -12, 12 do add(floor, RECT, i * 250 + 120, -120, 246, 80, {184, 210, 232}) end
        add(floor, RECT, 0, 6, 6000, 12, {240, 250, 255})
        L.particles = {kind = 'fall', n = 22, col = {255, 255, 255}, shape = ELLIPSE, size = 12, drift = 120, dur = 7}
    end,
}

St.list.training = {
    name = '训练场 · 千星奇域', sub = '练习连段与元素反应', ambient = {200, 220, 255},
    build = function(L)
        local sky, far, floor = L.sky, L.far, L.floor
        gradient(sky, 0, -200, 1500, 5200, {{16, 20, 44}, {30, 40, 80}, {50, 70, 120}}, 14)
        for i = -12, 12 do add(far, RECT, i * 200, 500, 3, 1100, {80, 110, 170}) end
        for j = 0, 5 do add(far, RECT, 0, 80 + j * 180, 5000, 3, {80, 110, 170}) end
        add(floor, RECT, 0, -260, 6000, 520, {36, 44, 74})
        for i = -15, 15 do add(floor, RECT, i * 200, -60, 4, 120, {90, 120, 190}) end
        add(floor, RECT, 0, 6, 6000, 10, {120, 170, 255})
    end,
}

St.order = {}
for _, k in ipairs({'mondstadt', 'liyue', 'inazuma', 'sumeru', 'fontaine', 'natlan', 'snezhnaya'}) do
    if Paint.available[k] then St.order[#St.order + 1] = k end
end
if #St.order == 0 then St.order = {'mondstadt', 'liyue', 'inazuma', 'snezhnaya'} end

-- build -------------------------------------------------------------------------
-- parent: back layer group. Parallax factors per layer.
local FACTORS = {sky = 0.05, far = 0.25, mid = 0.55, near = 0.8, floor = 1.0}
local ORDER = {'sky', 'far', 'mid', 'near', 'floor'}

function St.new(app, parent, key)
    if Paint.available[key] then return St.newPainted(app, parent, key) end
    local def = St.list[key] or St.list.training
    local self = setmetatable({app = app, key = key, def = def, groups = {}, lists = {}, built = false, i = 0, anims = {}}, St)
    local L = {sky = {}, far = {}, mid = {}, near = {}, floor = {}}
    def.build(L)
    self.L = L
    for _, name in ipairs(ORDER) do
        self.groups[name] = G.group(parent)
    end
    -- flat job list
    local jobs = {}
    for _, name in ipairs(ORDER) do
        for _, s in ipairs(L[name]) do jobs[#jobs + 1] = {name, s} end
    end
    self.jobs = jobs
    self.nodes = {}
    return self
end

-- build up to n shapes this frame; returns true when complete
function St:buildStep(n)
    if self.painted then return self:paintedBuild(n) end
    local jobs = self.jobs
    local stop = math.min(#jobs, self.i + n)
    for k = self.i + 1, stop do
        local name, s = jobs[k][1], jobs[k][2]
        local node = G.image(self.groups[name], s[1])
        local col = s[6]
        node:pos(s[2], s[3]):size(s[4], s[5] or s[4]):rot(s[7]):color(col[1], col[2], col[3], col[4] or 255):soft(s[8]):on(true)
        self.nodes[#self.nodes + 1] = node
        local an = s[9]
        if an then self.anims[#self.anims + 1] = {node = node, a = an, s = s} end
    end
    self.i = stop
    if stop >= #jobs then
        if not self.built then
            self.built = true
            self:startAnims()
            self:buildParticles()
        end
        return true
    end
    return false
end

function St:startAnims()
    for _, an in ipairs(self.anims) do
        local n, a, s = an.node, an.a, an.s
        local col = s[6]
        if a.spin then
            local t = n:tween({localRotationZ = (s[7] or 0) + a.spin}, a.dur, 'Linear')
            if t then pcall(function() t:SetLoops(-1) end) end
        elseif a.dx then
            G.pingpong(n, {anchoredPositionX = s[2] + a.dx}, {anchoredPositionX = s[2]}, a.dur, 'InOutSine')
        elseif a.blink then
            G.pingpong(n, {imageColor = G.col(col[1], col[2], col[3], 255 * (a.lo or 0.15))},
                       {imageColor = G.col(col[1], col[2], col[3], col[4] or 255)}, a.dur, 'InOutSine')
        elseif a.flash then
            n:color(col[1], col[2], col[3], 0)
            self.flashNode = n
            self.flashCol = col
        end
    end
end

-- lightning flash for stormy stages (called by the fight scene at random moments)
function St:thunder()
    local n, col = self.flashNode, self.flashCol
    if not n then return false end
    n:color(col[1], col[2], col[3], 150)
    n:tween({imageColor = G.col(col[1], col[2], col[3], 0)}, 0.45, 'OutQuad')
    return true
end

-- ambient particles: float up or fall down, looping tweens on a few nodes
function St:buildParticles()
    local p = self.L.particles
    if not p then return end
    self.parts = {}
    local grp = self.groups.near
    for i = 1, p.n do
        local x = -1500 + U.hash(i * 31) * 3000
        local y = p.kind == 'fall' and (1100 + U.hash(i * 7) * 200) or (-20 + U.hash(i * 7) * 200)
        if p.kind == 'drift' then y = 20 + U.hash(i * 7) * 500; x = -1800 + U.hash(i * 31) * 600 end
        local node = G.image(grp, p.shape)
        local c = p.col
        local sz = p.size * (0.6 + U.hash(i * 13) * 0.8)
        node:pos(x, y):size(sz, sz * (p.shape == ELLIPSE and 0.7 or 1)):rot(U.hash(i) * 90):color(c[1], c[2], c[3], 200):soft(p.soft or 0):on(true)
        local dur = p.dur * (0.7 + U.hash(i * 3) * 0.6)
        local ty = p.kind == 'fall' and -40 or (y + (p.rise or 600))
        local tx = x + (U.hash(i * 5) - 0.5) * p.drift * 2
        if p.kind == 'drift' then ty = y + (U.hash(i * 9) - 0.5) * 120; tx = x + 3600 end
        local t = node:tween({anchoredPositionY = ty, anchoredPositionX = tx, localRotationZ = 360}, dur, 'Linear')
        if t then pcall(function() t:SetLoops(-1) end) end
        self.parts[#self.parts + 1] = node
        self.nodes[#self.nodes + 1] = node
    end
end

function St:buildForeground()
    local spec = FORE[self.key]
    if not spec then return end
    local grp = self.groups.fore
    local lo = self.app.quality == 'lo'
    local c = spec.col
    -- plant / rock clusters spaced along the stage, below the floor line
    local clusters = lo and 5 or 8
    for i = 1, clusters do
        local cx = -1700 + (i - 1) * (3400 / (clusters - 1)) + (U.hash(i * 17) - 0.5) * 160
        local base = G.image(grp, ELLIPSE)
        base:pos(cx, -175):size(420 + U.hash(i) * 200, 130):color(c[1], c[2], c[3], 235):soft(0.5):on(true)
        self.nodes[#self.nodes + 1] = base
        if spec.kind == 'rocks' then
            for j = 1, 2 do
                local r = G.image(grp, ELLIPSE)
                local w = 160 + U.hash(i * 7 + j) * 160
                r:pos(cx + (j - 1.5) * 170, -150 + U.hash(i * 3 + j) * 20):size(w, w * 0.5):rot((U.hash(i + j) - 0.5) * 30)
                 :color(c[1], c[2], c[3], 245):soft(0.25):on(true)
                self.nodes[#self.nodes + 1] = r
            end
        end
        local blades = lo and 3 or (spec.kind == 'grass' and 7 or 3)
        for j = 1, blades do
            -- low, soft-edged blades: they stay below the fighters' feet
            local b = G.image(grp, ELLIPSE)
            local h = 70 + U.hash(i * 11 + j) * 90
            local bx = cx + (j - (blades + 1) / 2) * 30 + (U.hash(j * 5 + i) - 0.5) * 30
            local a0 = (U.hash(i * 19 + j) - 0.5) * 36
            b:pos(bx, -175 + h / 2):size(16 + U.hash(j + i) * 12, h):rot(a0):color(c[1], c[2], c[3], 235):soft(0.2):on(true)
            G.pingpong(b, {localRotationZ = a0 - 5}, {localRotationZ = a0 + 6}, 1.6 + U.hash(i * 5 + j) * 1.4, 'InOutSine')
            self.nodes[#self.nodes + 1] = b
        end
    end
    -- large soft motes crossing in front
    local m = spec.motes
    local n = lo and math.ceil(m.n / 2) or m.n
    for i = 1, n do
        local node = G.image(grp, m.shape)
        local sz = m.size * (0.6 + U.hash(i * 23) * 0.8)
        local x = -1500 + U.hash(i * 41) * 3000
        local y, tx, ty
        local dur = 6 + U.hash(i * 3) * 6
        if m.move == 'fall' then
            y = 900 + U.hash(i * 9) * 300; ty = -200; tx = x + (U.hash(i * 5) - 0.5) * 700
        elseif m.move == 'drift' then
            x = -2000 + U.hash(i * 41) * 500; y = 20 + U.hash(i * 9) * 420; tx = x + 4000; ty = y + (U.hash(i) - 0.5) * 100; dur = 3 + U.hash(i * 3) * 2
        else
            y = -200 + U.hash(i * 9) * 200; ty = y + 900 + U.hash(i) * 300; tx = x + (U.hash(i * 5) - 0.5) * 500
        end
        local w, h = sz, sz
        if m.leaf then h = sz * 0.55 end
        if m.streak then w, h = sz, 3 + U.hash(i) * 3 end
        node:pos(x, y):size(w, h):rot(U.hash(i * 7) * 180):color(m.col[1], m.col[2], m.col[3], m.glow and 230 or 150)
            :soft(m.soft or (m.leaf and 0.15 or 0)):on(true)
        local t = node:tween({anchoredPositionY = ty, anchoredPositionX = tx, localRotationZ = 540}, dur, 'Linear')
        if t then pcall(function() t:SetLoops(-1) end) end
        self.nodes[#self.nodes + 1] = node
    end
end

-- camera: cx (world x at screen centre), zoom, floorY (screen y of the floor), shake offsets
function St:camera(cx, zoom, floorY, sx, sy)
    if self.painted then return self:paintedCamera(cx, zoom, floorY, sx, sy) end
    for _, name in ipairs(ORDER) do
        local f = FACTORS[name]
        local z = 1 + (zoom - 1) * f
        local g = self.groups[name]
        g:pos(-cx * f * z + (sx or 0) * f, floorY * (name == 'sky' and 0.6 or 1) + (sy or 0) * f):scale(z, z)
    end
end

function St:free()
    if self.back then self.back:free() end
    if self.ground then self.ground:free() end
    for _, n in ipairs(self.nodes) do G.release(n) end
    for _, g in pairs(self.groups) do G.release(g) end
    self.nodes = {}
end

------------------------------------------------------------------ painted stages
-- backdrop: the whole painting at half-speed parallax; ground: the bottom strip of the same
-- painting, moving 1:1 with the fighters (no foot sliding); its top fades into the backdrop.
local AMBIENT = {
    mondstadt = {particles = {kind = 'float', n = 16, col = {255, 252, 230}, shape = STAR4, size = 16, rise = 500, drift = 300, dur = 9}, rays = {255, 244, 200}},
    liyue = {particles = {kind = 'fall', n = 16, col = {255, 200, 70}, shape = ELLIPSE, size = 20, drift = 380, dur = 8}, rays = {255, 226, 160}},
    inazuma = {particles = {kind = 'float', n = 18, col = {200, 140, 255}, shape = STAR4, size = 14, rise = 700, drift = 200, dur = 7}, lightning = {220, 190, 255}},
    sumeru = {particles = {kind = 'drift', n = 18, col = {255, 214, 150}, shape = ELLIPSE, size = 12, drift = 900, dur = 6}, rays = {255, 210, 140}},
    fontaine = {particles = {kind = 'float', n = 16, col = {200, 240, 255}, shape = RING, size = 18, rise = 600, drift = 120, dur = 9}, rays = {230, 245, 255}},
    natlan = {particles = {kind = 'float', n = 20, col = {255, 150, 60}, shape = STAR4, size = 12, rise = 800, drift = 260, dur = 6}, rays = {255, 190, 120}},
    snezhnaya = {particles = {kind = 'fall', n = 26, col = {255, 255, 255}, shape = ELLIPSE, size = 12, drift = 160, dur = 7}},
}
local BACK_S, GROUND_S = 1.6, 1.75
local BACK_Y, GROUND_Y = 360, -142       -- painting footline (75 % of the image height) on the floor

function St.newPainted(app, parent, key)
    local data = require('gf_bg_' .. key)
    local self = setmetatable({app = app, key = key, painted = true, def = {name = data.name, sub = data.sub},
                               groups = {}, nodes = {}, anims = {}, built = false}, St)
    self.L = {particles = (AMBIENT[key] or {}).particles, lightning = (AMBIENT[key] or {}).lightning}
    local limit = app.quality == 'lo' and 700 or nil
    self.groups.back = G.group(parent)
    self.back = Paint.new(self.groups.back, key, 'full', limit)
    self.groups.ground = G.group(parent)
    self.ground = data.ground and Paint.new(self.groups.ground, key, 'ground', limit and 300 or nil)
    self.groups.near = G.group(parent)
    self.groups.fore = G.group(app.layers.front)
    self.parent = parent
    return self
end

function St:paintedBuild(n)
    if not self.back:step(n) then return false end
    if self.ground and not self.ground:step(n) then return false end
    if not self.built then
        self.built = true
        local amb = AMBIENT[self.key] or {}
        -- light rays from the top (sunny regions), lightning flash plane (storm)
        if amb.rays then
            for i = 1, 4 do
                local n = G.image(self.groups.back, TRI)
                local c = amb.rays
                n:pos(-500 + i * 260, 280):size(180 + i * 30, 1300):rot(180 + 14 - i * 6):color(c[1], c[2], c[3], 28):soft(0.4):on(true)
                G.pingpong(n, {imageColor = G.col(c[1], c[2], c[3], 10)}, {imageColor = G.col(c[1], c[2], c[3], 34)}, 3 + i * 0.7, 'InOutSine')
                self.nodes[#self.nodes + 1] = n
            end
        end
        if amb.lightning then
            local n = G.image(self.groups.back, RECT)
            local c = amb.lightning
            n:pos(0, 200):size(3000, 1800):color(c[1], c[2], c[3], 0):on(true)
            self.flashNode, self.flashCol = n, c
            self.nodes[#self.nodes + 1] = n
        end
        self:buildParticles()
        self:buildForeground()
        -- depth haze between the painting and the fighters (readability)
        local hz = G.image(self.parent, RECT)
        hz:color(12, 14, 30, 46):on(true)
        self.haze = hz
        self.nodes[#self.nodes + 1] = hz
    end
    return true
end

function St:paintedCamera(cx, zoom, floorY, sx, sy)
    sx, sy = sx or 0, sy or 0
    local f = 0.3
    local zf = 1 + (zoom - 1) * f
    -- painting scale: cover the visible width plus the parallax travel
    local W = self.app.W
    local need = (W / zf + 2 * f * 520) / self.back.w
    local S = math.max(1.12, need + 0.02)
    local by = BACK_Y / BACK_S * S
    self.groups.back:pos(-cx * f * zf + sx * f, floorY + by * zf + sy * f):scale(S * zf, S * zf)
    if self.ground then
        self.groups.ground:pos(-cx * zoom + sx, floorY + GROUND_Y * zoom + sy):scale(GROUND_S * zoom, GROUND_S * zoom)
    end
    local fz = 1 + (zoom - 1) * 0.8
    self.groups.near:pos(-cx * 0.8 * fz + sx * 0.8, floorY + sy * 0.8):scale(fz, fz)
    local gz = 1.08 + (zoom - 1) * 1.3
    self.groups.fore:pos(-cx * 1.3 * gz + sx * 1.3, floorY + sy * 1.3):scale(gz, gz)
    if self.haze then
        self.haze:pos(0, 0):size(W + 60, self.app.H + 60)
    end
end

return St
