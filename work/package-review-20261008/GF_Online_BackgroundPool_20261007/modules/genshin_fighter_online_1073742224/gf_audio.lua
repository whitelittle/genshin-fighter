__loaders['gf_audio'] = function()
local A = {}
A.__index = A

local ELEM = {'geo', 'hydro', 'electro', 'pyro', 'anemo', 'dendro', 'cryo'}
local function per(t) return t end

A.ID = {
    move = 50942, ok = 50915, okBig = 50873, back = 50863, open = 50923, close = 50922, fail = 50931,
    lock = 50937, tick = 50886, coin = 50935,
    jump = 30026, land = 30020, dash = 40096, dash2 = 30001, fall = 30134, down = 30004,
    swing = {
        sword = {40310, 40305}, claymore = {40284, 40277}, polearm = {40270, 40265},
        catalyst = {40036, 40055}, bow = {40026, 40027},
    },
    punch = {40106, 40107}, slap = 40111, blade = 40176, blunt = 40186,
    ehit = per({geo = 40117, hydro = 40126, electro = 40136, pyro = 40144, anemo = 40150, dendro = 40158, cryo = 40164}),
    eboom = per({geo = 40221, hydro = 40227, electro = 40234, pyro = 40243, anemo = 40250, dendro = 40255, cryo = 40259}),
    ecast = per({geo = 40049, hydro = 40055, electro = 40060, pyro = 40065, anemo = 40070, dendro = 40075, cryo = 40081}),
    ecircle = per({geo = 40350, hydro = 40368, electro = 40385, pyro = 40400, anemo = 40421, dendro = 40440, cryo = 40461}),
    guard = 40320, guardBreak = 40193, parry = 40332, shield = 40335,
    heart = 10061, bell = 51063, clap = 30132, shock = 10067,
}
A.ELEM = ELEM

function A.new(env)
    return setmetatable({env = env, on = true, last = {}, lastEvent = {}, t = 0}, A)
end

function A:update(dt) self.t = self.t + dt end

function A:play(id, gap)
    if not self.on or not id then return end
    if type(id) == 'table' then id = id[1] end
    local stamp = self.eventTime or self.t
    local last = self.eventTime and self.lastEvent or self.last
    local t = last[id]
    if t and stamp - t < (gap or 0.04) then return end
    last[id] = stamp
    self.env.safe(self.env.game.PlayAudio2D, id)
end

function A:swing(weapon, heavy)
    local s = A.ID.swing[weapon] or A.ID.swing.sword
    self:play(heavy and s[2] or s[1])
end

function A:hit(element, kind)
    local id = A.ID
    if kind == 'boom' then self:play(id.eboom[element] or id.eboom.pyro)
    elseif kind == 'elem' then self:play(id.ehit[element] or id.punch[1])
    elseif kind == 'blade' then self:play(id.blade)
    else self:play(id.punch[1]) end
end

return A
end
