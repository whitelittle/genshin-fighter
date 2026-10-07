__loaders['gf_input'] = function()
-- Input hub: keyboard (two local players), controller, touch controls and mouse/touch menu
-- buttons, turned into per-player virtual pads sampled once per 60 Hz tick.
--
-- Keyboard (7.1 key events, heard by Lua in our other maps):
--   P1  W A S D move (W / Space = jump), J light, K heavy, E/I skill, Q/O burst, U dash, L throw
--   P2  arrows move, , light  . heavy  / skill  RShift burst  RCtrl dash
--   menus: P1 keys or arrows, J/Space/F = confirm, K/Backspace = back, P/Tab = pause, F9 = debug
-- Controller: left stick / d-pad... only the stick is readable; NormalAttack light, Interact heavy,
--   Skill1 skill, Skill2 burst, Sprint dash, Jump jump, MenuConfirm/MenuBack.
-- Touch: GF_BTN pool — floating stick on the left half, 轻/重/技/爆/冲 on the right.
local G = require('gf_gfx')

local I = {}
I.__index = I

local B = {U = 1, D = 2, L = 4, R = 8, LP = 16, HP = 32, SK = 64, BU = 128, DA = 256, TH = 512}
I.B = B
I.DIRS = 15

-- key event base name -> {player, bit} or menu action
local CRAFT = {['1'] = 1, ['2'] = 2, ['3'] = 3, ['4'] = 4, ['5'] = 5, ['6'] = 6, ['7'] = 7, ['8'] = 8, ['9'] = 9, ['0'] = 10,
    U = 11, Z = 12, Y = 13, G = 14, H = 15, I = 16, O = 17, P = 18, J = 19, K = 20, L = 21, V = 22,
    F5 = 23, F6 = 24, F7 = 25, F8 = 26, F9 = 27, F10 = 28, TILDE = 29, MINUS = 30, EQUAL = 31, BRACKET = 32,
    COMMA = 33, PERIOD = 34, SLASH = 35, UP = 36, DOWN = 37, LEFT = 38, RIGHT = 39, RCTRL = 40, RSHIFT = 41,
    BACK = 42, CAPS = 43}
I.CRAFT = CRAFT

local function ck(name) return 'KeyboardCraftspersonKey' .. CRAFT[name] end

-- {event base, player, bit, menu}
local BINDS = {
    {'KeyboardMoveForwardKey', 1, B.U, 'up'}, {'KeyboardMoveBackwardKey', 1, B.D, 'down'},
    {'KeyboardMoveLeftKey', 1, B.L, 'left'}, {'KeyboardMoveRightKey', 1, B.R, 'right'},
    {'KeyboardJumpKey', 1, B.U, 'ok'},
    {ck('J'), 1, B.LP, 'ok'}, {ck('K'), 1, B.HP, 'back'}, {'KeyboardCharacterSkill1Key', 1, B.SK, 'alt'}, {'KeyboardCharacterSkill2Key', 1, B.BU, 'alt2'},
    {ck('I'), 1, B.SK, 'alt'}, {ck('O'), 1, B.BU, 'alt2'},
    {ck('U'), 1, B.DA}, {ck('L'), 1, B.TH},
    {'KeyboardInteractKey', 0, 0, 'ok'},
    {ck('UP'), 2, B.U, 'up'}, {ck('DOWN'), 2, B.D, 'down'}, {ck('LEFT'), 2, B.L, 'left'}, {ck('RIGHT'), 2, B.R, 'right'},
    {ck('COMMA'), 2, B.LP, 'ok2'}, {ck('PERIOD'), 2, B.HP, 'back2'}, {ck('SLASH'), 2, B.SK}, {ck('RSHIFT'), 2, B.BU},
    {ck('RCTRL'), 2, B.DA},
    {ck('BACK'), 0, 0, 'back'}, {ck('P'), 0, 0, 'pause'}, {'KeyboardOpenShortcutWheelKey', 0, 0, 'pause'},
    {ck('F9'), 0, 0, 'debug'}, {ck('H'), 0, 0, 'help'},
    -- controller
    {'ControllerNormalAttackKey', 'pad', B.LP, 'ok'}, {'ControllerInteractKey', 'pad', B.HP},
    {'ControllerCharacterSkill1Key', 'pad', B.SK}, {'ControllerCharacterSkill2Key', 'pad', B.BU},
    {'ControllerSprintKey', 'pad', B.DA}, {'ControllerJumpKey', 'pad', B.U},
    {'ControllerMenuConfirmKey', 0, 0, 'ok'}, {'ControllerMenuBackKey', 0, 0, 'back'},
    {'ControllerCharacterSkill3Key', 0, 0, 'pause'},
}

local function newPad()
    return {held = 0, prev = 0, pressed = 0, released = 0, counts = {}, hist = {}, histN = 0, touch = 0, stick = 0}
end

function I.new(app)
    local self = setmetatable({app = app, pads = {newPad(), newPad()}, menuQ = {}, rep = {}, held = {},
                               dev = 'pc', padOwner = 1, buttons = {}, touchOn = false, mouseOn = false}, I)
    self:attach()
    return self
end

function I:attach()
    local env = self.app.env
    local E = env.Enum
    local host = env.host
    local n = 0
    for _, b in ipairs(BINDS) do
        local okd, dn = pcall(function() return E.KeyEventType[b[1] .. 'Down'] end)
        local oku, up = pcall(function() return E.KeyEventType[b[1] .. 'Up'] end)
        if okd and oku and dn and up then
            local bind = b
            env.safe(host.AddKeyEventListener, host, dn, function() self:key(bind, true) return true end)
            env.safe(host.AddKeyEventListener, host, up, function() self:key(bind, false) return true end)
            n = n + 1
        end
    end
    self.listeners = n
end

function I:key(b, down)
    local p, bit, menu = b[2], b[3], b[4]
    if p == 'pad' then p = self.padOwner; self.dev = 'pad' end
    if p ~= 0 and bit ~= 0 then
        local pad = self.pads[p]
        local c = pad.counts[bit] or 0
        c = down and c + 1 or math.max(0, c - 1)
        pad.counts[bit] = c
        if c > 0 then pad.held = pad.held | bit else pad.held = pad.held & ~bit end
    end
    if menu then
        if down then
            self.menuQ[#self.menuQ + 1] = menu
            self.held[menu] = 0
        else
            self.held[menu] = nil
        end
    end
    if self.dev == 'touch' and p ~= 'pad' then self.dev = 'pc' end
end

function I:device()
    local ok, d = pcall(self.app.env.game.GetDevice)
    local D = self.app.env.Enum.Device
    if ok and d ~= nil then
        if d == D.Mobile then return 'touch' end
        if d == D.Controller or d == D.MobileController then return 'pad' end
    end
    return 'pc'
end

local function stickDirs(x, y)
    local m = 0
    if x > 0.45 then m = m | B.R elseif x < -0.45 then m = m | B.L end
    if y > 0.55 then m = m | B.U elseif y < -0.5 then m = m | B.D end
    return m
end

function I:poll()
    self.dev = self:device()
    if self.dev == 'pad' then
        local ok, x, y = pcall(self.app.env.game.GetControllerLeftStickAxis)
        if ok and type(x) == 'number' and type(y) == 'number' then
            local m = stickDirs(x, y)
            local pad = self.pads[self.padOwner]
            pad.stick = m
            local was = self.stickMenu or 0
            -- menu navigation from the stick (edge)
            if m ~= was then
                if m & B.U ~= 0 and was & B.U == 0 then self.menuQ[#self.menuQ + 1] = 'up' end
                if m & B.D ~= 0 and was & B.D == 0 then self.menuQ[#self.menuQ + 1] = 'down' end
                if m & B.L ~= 0 and was & B.L == 0 then self.menuQ[#self.menuQ + 1] = 'left' end
                if m & B.R ~= 0 and was & B.R == 0 then self.menuQ[#self.menuQ + 1] = 'right' end
                self.stickMenu = m
            end
        end
    end
end

-- clean opposite directions (SOCD): left+right = neutral, up+down = up
local function clean(m)
    if m & B.L ~= 0 and m & B.R ~= 0 then m = m & ~(B.L | B.R) end
    if m & B.U ~= 0 and m & B.D ~= 0 then m = m & ~B.D end
    return m
end

-- once per 60 Hz tick
function I:tick()
    for _, pad in ipairs(self.pads) do
        local now = clean(pad.held | pad.touch | pad.stick | (pad.pulse or 0))
        pad.pulse = 0
        pad.pressed = now & ~pad.prev
        pad.released = pad.prev & ~now
        pad.prev = now
        pad.now = now
        pad.histN = pad.histN + 1
        pad.hist[pad.histN % 32] = now
    end
    -- menu key repeat for held directions
    for k, t in pairs(self.held) do
        if k == 'up' or k == 'down' or k == 'left' or k == 'right' then
            t = t + 1
            self.held[k] = t
            if t > 22 and t % 6 == 0 then self.menuQ[#self.menuQ + 1] = k end
        end
    end
end

function I:pad(p) return self.pads[p] end

-- direction history: bits of the pad i frames ago (0 = now)
function I:past(p, i)
    local pad = self.pads[p]
    return pad.hist[(pad.histN - i) % 32] or 0
end

-- menu actions since the last call
function I:menu()
    local q = self.menuQ
    self.menuQ = {}
    return q
end

function I:clearUI()
    self.menuQ = {}
    for _, b in ipairs(self.buttons) do
        if b.node then b.node:on(false) end
    end
    self.buttons = {}
    self.usedBtn = 0
    self.gen = (self.gen or 0) + 1
    for _, pad in ipairs(self.pads) do pad.touch = 0; pad.pulse = 0 end
end

------------------------------------------------------------------ pointer buttons
-- A clickable area over design coordinates; uses a pooled transparent preset button.
-- handlers: {click = fn(x, y), down = fn(x, y, id), drag = fn(x, y, id), up = fn(x, y, id)}
function I:area(x, y, w, h, handlers, parent)
    self.usedBtn = (self.usedBtn or 0) + 1
    local node = G.btns[self.usedBtn]
    if not node then return nil end
    local app = self.app
    local b = {node = node, handlers = handlers}
    self.buttons[#self.buttons + 1] = b
    node.handlers = handlers
    if not node.bound then
        node.bound = true
        local E = app.env.Enum.CursorEventType
        local function conv(ev)
            local ok, px, py = pcall(ev.GetUIPos, ev)
            if not ok or type(px) ~= 'number' then return nil end
            return (px - app.cw / 2) / app.s, (py - app.ch / 2) / app.s
        end
        local function on(name, key)
            if not E[name] then return end
            app.env.safe(node.c.AddCursorEventListener, node.c, E[name], function(ev)
                local hd = node.handlers
                if not hd or not hd[key] then return end
                local px, py = conv(ev)
                if px then
                    local id = -1
                    pcall(function() id = ev.touchId end)
                    hd[key](px, py, id)
                end
            end)
        end
        on('CursorDown', 'down'); on('CursorDrag', 'drag'); on('CursorUp', 'up'); on('CursorClick', 'click')
        pcall(function() node.c.raycastTarget = true end)
    end
    node:parentTo(parent or app.layers.top)
    node:pos(x, y):size(w, h):on(true)
    return b
end

function I:moveArea(b, x, y, w, h)
    if b and b.node then b.node:pos(x, y):size(w, h) end
end

return I
end
