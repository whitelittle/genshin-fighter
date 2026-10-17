__loaders['gf_sim_snapshot']=function()
local floor,abs,max,min=math.floor,math.abs,math.max,math.min
return function(S,HIST)
local function copyList(src)
    local out = {}
    for i = 1, #src do
        local e = src[i]
        local c = {}
        for k, v in pairs(e) do c[k] = v end
        out[i] = c
    end
    return out
end

local function copyFighter(p)
    local c = {}
    for k, v in pairs(p) do c[k] = v end
    local h = {}
    for k = 0, HIST - 1 do h[k] = p.hist[k] end
    c.hist = h
    c.dots = copyList(p.dots)
    local st = {}
    for k, v in pairs(p.stats) do st[k] = v end
    c.stats = st
    return c
end

function S.copy(src)
    local self = setmetatable({}, S)
    for k, v in pairs(src) do self[k] = v end
    local a, b = copyFighter(src.f[1]), copyFighter(src.f[2])
    a.foe, b.foe = b, a
    self.f = {a, b}
    self.proj = copyList(src.proj)
    self.events = {}
    if src.teamIndex then self.teamIndex={src.teamIndex[1],src.teamIndex[2]} end
    return self
end
S.snapshot = S.copy

function S:hash()
    local h = self.tick
    if self.teamIndex then h=(h*31+self.teamIndex[1]*7+self.teamIndex[2]*11+self.teamBout*17)&0x7fffffff end
    for _, p in ipairs(self.f) do
        h = (h * 31 + p.x) & 0x7fffffff
        h = (h * 31 + p.y) & 0x7fffffff
        h = (h * 31 + p.hp) & 0x7fffffff
        h = (h * 31 + p.energy) & 0x7fffffff
        h = (h * 31 + #p.state) & 0x7fffffff
        h = (h * 31 + p.vx + p.vy * 7) & 0x7fffffff
        h = (h * 31 + p.t + p.stun * 3 + p.combo * 5 + p.wins * 11) & 0x7fffffff
        if p.key=='clorinde' or p.key=='arlecchino' then
            h=(h*31+(p.skillHitMask or 0)+(p.cinematicConfirmed and 128 or 0))&0x7fffffff
        end
    end
    h = (h * 31 + #self.proj + self.seed) & 0x7fffffff
    return h
end


end
end
