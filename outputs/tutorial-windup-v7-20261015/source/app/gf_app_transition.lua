__loaders['gf_app_transition']=function()
local G=require('gf_gfx')
return function(App)
function App:travel(name, args, col)
    if self.trans then return end
    self.trans = {t = 0, name = name, args = args, col = col or {255, 214, 120}}
    self.audio:play(self.audio.ID.open)
end

function App:drawTransition()
    local tr = self.trans
    if not tr then if self.transL then self.transL:clear() end return end
    self.transL = self.transL or G.layer(self.layers.curtain)
    local L = self.transL
    tr.t = tr.t + 1
    local IN, HOLD, OUT = 16, 4, 18
    local k
    if tr.t <= IN then k = tr.t / IN
    elseif tr.t <= IN + HOLD then
        k = 1
        if tr.t == IN + 1 then self:go(tr.name, tr.args) end
    else k = 1 - (tr.t - IN - HOLD) / OUT end
    local W, H = self.coverW, self.coverH
    local e = k * k * (3 - 2 * k)
    L:begin()
    for i = 1, 3 do
        local off = (1 - e) * (W * 1.4) * (tr.t <= IN + HOLD and 1 or -1) + (i - 2) * 30 * (1 - e)
        local col = i == 2 and tr.col or {12, 14, 26}
        L:rect(off, 0, W * 1.5 * (i == 2 and 0.04 or 1) + (i == 2 and 0 or 0), H * 1.6, col, i == 2 and 1 or 1, -12)
    end
    L:shape(G.STAR4, 0, 0, 140 * e, 140 * e, tr.col, e, tr.t * 6)
    L:finish()
    if tr.t >= IN + HOLD + OUT then self.trans = nil; L:clear() end
end


end
end
