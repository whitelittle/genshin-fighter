-- Fighter view: draws one sim fighter.
--
-- Poses are bitmaps of ~700-1,300 rects. Each fighter owns two bitmap slots (front / back):
-- a new pose is written into the hidden back slot with a per-frame budget, then the slots swap
-- (two SetActive calls, no tearing). While the back slot is idle it pre-writes the pose that
-- most likely comes next (idle -> walk1, walk1 -> walk2, attack -> idle ...). Motion between
-- poses is procedural: lean, squash, lunge, recoil, shake, spin on air hits.
local G = require('gf_gfx')
local Art = require('gf_art')
local K = require('gf_kits')
local U = require('gf_util')

local V = {}
V.__index = V

local C = 100
local NEXT = {idle = 'walk1', walk1 = 'walk2', walk2 = 'walk1', slash = 'idle', special = 'idle', qRelease = 'idle',
              crouch = 'idle', jump = 'idle', hurt = 'idle', guard = 'idle', crouchGuard = 'crouch', down = 'crouch'}

-- layers: {shadow = group, body = group, fx = group}
function V.new(app, layers, fighter, tier)
    local self = setmetatable({app = app, f = fighter, tier = tier or 'hi', key = fighter.key,
                               element = fighter.element, ecol = K.elementColor[fighter.element] or {255, 255, 255}}, V)
    self.root = G.group(layers.body)
    -- root at the feet (ground tilts pivot there); spin/content pivot around the body centre (air spins)
    self.spin = G.group(self.root)
    self.content = G.group(self.spin)
    self.aura = G.bitmap(self.content)       -- element glow behind the body
    self.slots = {G.bitmap(self.content), G.bitmap(self.content)}
    self.flash = G.bitmap(self.content)      -- white / ice overlay
    for _, s in ipairs(self.slots) do s.node:on(false) end
    self.aura.node:on(false)
    self.flash.node:on(false)
    self.front = nil
    self.want = 'idle'
    self.shadow = G.image(layers.shadow, G.ELLIPSE)
    self.shadow:color(0, 0, 0, 110):on(true)
    self.ghosts = {}
    for i = 1, 3 do
        local g = G.bitmap(layers.ghost)
        g.node:on(false)
        self.ghosts[i] = {bmp = g, x = 0, y = 0, life = 0, pose = nil, face = 1, a = 0}
    end
    self.ghostI = 0
    self.flashT = 0
    self.trail = 0
    self.walkT = 0
    self.shake = 0
    self.tilt, self.sx, self.sy, self.ox, self.oy = 0, 1, 1, 0, 0
    return self
end

function V:image(pose) return Art.pose(self.key, self.tier, pose) end

-- the pose the sim state wants right now
function V:poseFor()
    local f = self.f
    local st = f.state
    if f.airMove then
        local m = f.airMove
        if (f.airT or 0) < m.startup and m.windup then return m.windup end
        return m.pose or 'jump'
    end
    if st == 'idle' or st == 'intro' then return 'idle' end
    if st == 'walk' or st == 'back' then
        return ((self.walkT // 10) % 2 == 0) and 'walk1' or 'walk2'
    end
    if st == 'crouch' or st == 'jumpsq' or st == 'land' or st == 'getup' then return 'crouch' end
    if st == 'air' then return 'jump' end
    if st == 'dash' then return 'walk2' end
    if st == 'backdash' then return 'jump' end
    if st == 'attack' or st == 'throw' then
        local m = f.move
        if m.windup and f.t < m.startup then return m.windup end
        return m.pose or 'slash'
    end
    if st == 'skill' then
        local m = f.move
        if f.t < m.startup then return 'guard' end
        return (m.style == 'rising') and 'jump' or 'special'
    end
    if st == 'burst' then return 'qRelease' end
    if st == 'hit' or st == 'airhit' or st == 'thrown' or st == 'lose' then return 'hurt' end
    if st == 'down' then return 'down' end
    if st == 'block' then return 'guard' end
    if st == 'cblock' then return 'crouchGuard' end
    if st == 'win' then return 'special' end
    return 'idle'
end

local function slotHas(s, pose) return s.key == pose and not s.job end

-- drive the double buffer; budget = rects per frame
function V:updatePose(budget)
    local want = self:poseFor()
    self.want = want
    local front, back = self.front, nil
    for _, s in ipairs(self.slots) do if s ~= front then back = s end end
    if front and slotHas(front, want) then
        -- idle back slot: prefetch the likely next pose
        local nxt = NEXT[want]
        if nxt and back and not slotHas(back, nxt) then
            if not back.job or back.job.key ~= nxt then back:start(self:image(nxt), nxt) end
            back:step(math.min(budget // 2, 220))
        end
        return
    end
    if not slotHas(back, want) then
        if not back.job or back.job.key ~= want then back:start(self:image(want), want) end
        back:step(budget)
    end
    if slotHas(back, want) then
        back.node:on(true)
        if front then front.node:on(false) end
        self.front = back
        self.poseImg = self:image(want)
        self.poseChanged = true
    end
end

function V:spawnGhost()
    if not self.poseImg then return end
    self.ghostI = self.ghostI % #self.ghosts + 1
    local g = self.ghosts[self.ghostI]
    local sil = Art.silhouette(self.key, self.front.key)
    g.bmp:draw(sil, self.front.key, self.ecol)
    g.x, g.y, g.face, g.life, g.u = self.wx, self.wy, self.f.face, 14, sil.u
    g.bmp.node:on(true)
end

-- events from the sim for this fighter
function V:onHit(e)
    self.flashT = 5
    self.flashTint = {255, 255, 255}
    self.shake = e.heavy and 10 or 6
end

function V:onBlock()
    self.flashT = 3
    self.flashTint = {150, 210, 255}
    self.shake = 4
end

-- per rendered frame; world: {x0 = camera offset...} handled by the parent layer
function V:draw(budget)
    local f = self.f
    local st = f.state
    if st == 'walk' or st == 'back' then self.walkT = self.walkT + (f.hitstop > 0 and 0 or 1) else self.walkT = 0 end
    self:updatePose(budget)
    local x, y = f.x / C, f.y / C
    self.wx, self.wy = x, y
    -- procedural motion
    local tilt, sx, sy, ox, oy = 0, 1, 1, 0, 0
    local t = f.t
    if st == 'idle' then
        sy = 1 + 0.012 * math.sin(self.app.t * 3.2 + f.id)
    elseif st == 'walk' or st == 'back' then
        oy = math.abs(math.sin(self.walkT * 0.31)) * 5
        tilt = (st == 'walk' and -3 or 3)
    elseif st == 'dash' then
        tilt = -10
        sx = 1.06
    elseif st == 'backdash' then
        tilt = 12
    elseif st == 'jumpsq' or st == 'land' then
        sy, sx = 0.9, 1.06
    elseif st == 'air' then
        local vy = f.vy / C
        sy = 1 + U.clamp(vy * 0.006, -0.06, 0.08)
        sx = 2 - sy
        if f.airMove then tilt = -(f.airMove.tilt or 0) end
    elseif st == 'attack' then
        local m = f.move
        if t < m.startup then
            local k = t / math.max(1, m.startup)
            tilt = (m.tilt or 0) * 0.5 * k + 4 * k
            sx = 1 - 0.04 * k
        elseif t < m.startup + m.active then
            tilt = -(m.tilt or 0)
            sx = 1.06
            ox = 8
        else
            local k = U.clamp((t - m.startup - m.active) / math.max(1, m.recovery), 0, 1)
            tilt = -(m.tilt or 0) * (1 - k)
        end
    elseif st == 'skill' or st == 'burst' then
        if t < 6 then sy, sx = 0.94, 1.05 else sx = 1.03 end
    elseif st == 'hit' or st == 'thrown' then
        tilt = 8 + math.min(f.stun or 0, 10)
        ox = -10
    elseif st == 'airhit' then
        tilt = U.clamp(f.vy / C * 2.2, -40, 50) + 20
    elseif st == 'block' or st == 'cblock' then
        ox = -6
    elseif st == 'win' then
        sy = 1 + 0.015 * math.sin(self.app.t * 4)
    end
    if self.shake > 0 then
        ox = ox + ((self.shake % 2 == 0) and 1 or -1) * self.shake * 0.8
        self.shake = self.shake - 1
    end
    self.tilt, self.sx, self.sy, self.ox, self.oy = tilt, sx, sy, ox, oy
    local face = f.face
    local hc = 150 * f.size
    if st == 'airhit' then
        self.root:pos(x + ox * face, y + oy):rot(0):scale(face * sx, sy)
        self.spin:pos(0, hc):rot(tilt * face)
        self.content:pos(0, -hc)
    else
        self.root:pos(x + ox * face, y + oy):rot(tilt * face):scale(face * sx, sy)
        self.spin:pos(0, 0):rot(0)
        self.content:pos(0, 0)
    end
    local img = self.poseImg
    if self.front and img then
        self.front.node:scale(img.u, img.u)
    end
    -- shadow on the floor
    local hgt = math.max(0, y)
    local k = U.clamp(1 - hgt / 500, 0.35, 1)
    self.shadow:pos(x, 4):size(170 * k * f.size, 26 * k):color(0, 0, 0, 120 * k)
    -- element coat glow (reaction window) and frozen tint
    local coat = f.coat > 0 or st == 'burst'
    local c = self.ecol
    if coat then
        local pulse = 0.5 + 0.5 * math.sin(self.app.t * 10)
        self.aura.node:on(false)
        if not self.glow then self.glow = G.image(self.content, G.ELLIPSE); self.glow:sibling(0) end
        self.glow:pos(0, 170 * f.size):size(300 * f.size, 380 * f.size):color(c[1], c[2], c[3], 70 + 50 * pulse):soft(0.5):rot(0):scale(1, 1):on(true)
        if self.app.frame % 6 == 0 and self.fx then
            self.fx:spawn(self.fx.world, {shape = G.STAR4, x = x + (math.random() - 0.5) * 140, y = y + 40 + math.random() * 200, w = 14 + math.random() * 10,
                                          col = c, a = 1, to = {y = y + 300 + math.random() * 80, s = 0.3, a = 0}, dur = 0.7})
        end
    else
        self.aura.node:on(false)
        if self.glow then self.glow:on(false) end
    end
    local frozen = f.frozen > 0
    if (self.flashT > 0 or frozen) and img then
        local sil = Art.silhouette(self.key, self.front.key)
        local tint = frozen and {170, 235, 255} or self.flashTint
        self.flash:draw(sil, self.front.key .. (frozen and ':ice' or ':flash'), tint)
        local a = frozen and 140 or (30 + self.flashT * 28)
        for i = 1, self.flash.used do self.flash.kids[i]:color(tint[1], tint[2], tint[3], a) end
        self.flash.node:scale(sil.u, sil.u):on(true)
        self.flash.node:front()
        if self.flashT > 0 then self.flashT = self.flashT - 1 end
    else
        self.flash.node:on(false)
    end
    -- afterimages while moving fast
    -- afterimages only while actually moving fast (a standing burst must not stack ghosts)
    local speed = math.abs(f.vx) / C
    local fast = speed > 9 and (st == 'dash' or st == 'backdash' or st == 'skill' or st == 'burst' or (st == 'airhit' and f.ko))
    if fast and self.app.frame % 3 == 0 then self:spawnGhost() end
    for _, g in ipairs(self.ghosts) do
        if g.life > 0 then
            g.life = g.life - 1
            local a = g.life / 14
            g.bmp.node:pos(g.x, g.y):scale(g.face * g.u, g.u)
            local c = self.ecol
            for i = 1, g.bmp.used do g.bmp.kids[i]:color(c[1], c[2], c[3], 110 * a) end
            if g.life == 0 then g.bmp.node:on(false) end
        end
    end
end

function V:free()
    for _, s in ipairs(self.slots) do s:free() end
    self.aura:free()
    self.flash:free()
    for _, g in ipairs(self.ghosts) do g.bmp:free() end
    G.release(self.shadow)
    G.release(self.content)
    G.release(self.spin)
    if self.glow then G.release(self.glow) end
    G.release(self.root)
end

return V
