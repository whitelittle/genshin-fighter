__loaders['gf_sim_fighter']=function()
local K=require('gf_kits')
local floor,abs,max,min=math.floor,math.abs,math.max,math.min
return function(S,ctx)
local C=ctx.C
local GRAV=ctx.GRAV
local WALL=ctx.WALL
local B=ctx.B
local HIST=ctx.HIST
local fwdBit=ctx.fwdBit
local backBit=ctx.backBit
local holding=ctx.holding
local pressed=ctx.pressed
local grounded=ctx.grounded
local motion236=ctx.motion236
local boxOf=ctx.boxOf
local overlap=ctx.overlap
local moveTable=ctx.moveTable
function S:fighterTick(p)
    p.t = p.t + 1
    if p.invul > 0 then p.invul = p.invul - 1 end
    if p.coat > 0 then p.coat = p.coat - 1 end
    if p.vuln > 0 then p.vuln = p.vuln - 1 end
    if p.skillCd > 0 then p.skillCd = p.skillCd - 1 end
    if p.shieldT > 0 then p.shieldT = p.shieldT - 1 if p.shieldT == 0 then p.shield = 0 end end
    -- damage over time from reactions
    for i = #p.dots, 1, -1 do
        local d = p.dots[i]
        d.t = d.t + 1
        if d.t % d.every == 0 then
            d.left = d.left - 1
            if p.hp > 0 then
                p.hp = max(p.state == 'ko' and 0 or 1, p.hp - d.dmg)
                self:emit({type = 'dot', p = p.id, dmg = d.dmg, x = p.x, y = p.y + floor(200 * C * p.size)})
            end
            if d.left <= 0 then table.remove(p.dots, i) end
        end
    end
    local st = p.state
    if p.frozen > 0 then p.frozen = p.frozen - 1 end
    if st == 'intro' or st == 'win' or st == 'lose' or st == 'thrown' then
        p.vx = 0
    elseif st == 'idle' or st == 'walk' or st == 'back' or st == 'crouch' then
        self:faceFoe(p)
        if self.phase == 'fight' then self:neutral(p) else p.vx = 0 end
    elseif st == 'land' then
        if p.t >= (p.landT or 4) then self:setState(p, 'idle') end
    elseif st == 'jumpsq' then
        if p.t >= 4 then
            self:setState(p, 'air')
            p.vy = 24 * C
            p.vx = (p.jumpDir or 0) * p.face * floor(5.6 * C)
            self:emit({type = 'jump', p = p.id})
        end
    elseif st == 'air' then
        if p.airMove then self:airAttackUpdate(p)
        elseif self.phase == 'fight' then
            local pr = p.inPressed
            if pr & B.BU ~= 0 and self:startBurst(p) then return end
            if pr & B.SK ~= 0 and self:startSkill(p) then return end
            if pr & B.HP ~= 0 then self:startMove(p, 'airHeavy')
            elseif pr & B.LP ~= 0 then self:startMove(p, 'airLight') end
        end
    elseif st == 'dash' then
        if p.t >= 14 then self:setState(p, 'idle') end
        p.vx = p.vx * 92 // 100
        if p.t >= 5 and self.phase == 'fight' and p.inPressed ~= 0 then
            -- dash cancel into attacks
            if p.inPressed & (B.LP | B.HP | B.SK | B.BU | B.TH) ~= 0 then self:setState(p, 'idle'); self:neutral(p) end
        end
    elseif st == 'backdash' then
        p.vx = p.vx * 90 // 100
        if p.t >= 18 then self:setState(p, 'idle') end
    elseif st == 'attack' then
        self:attackUpdate(p)
    elseif st == 'skill' then
        self:skillUpdate(p)
    elseif st == 'burst' then
        self:burstUpdate(p)
    elseif st == 'throw' then
        local d = p.foe
        p.vx = 0
        local assist=p.key=='nahida'
        local impact=assist and 34 or 30
        if p.t == impact then
            local dmg = K.throw.damage
            d.hp = max(0, d.hp - dmg)
            p.energy = min(100, p.energy + K.throw.energy)
            p.stats.damage = p.stats.damage + dmg
            self:setState(d, 'airhit')
            d.vy = (assist and 24 or -12) * C
            d.y=math.max(d.y,(assist and 20 or 40)*C)
            d.vx = p.face * (assist and 15 or 9) * C
            d.combo, d.comboDmg = 1, dmg
            if d.hp <= 0 then d.ko = true; self:emit({type = 'ko', p = d.id, by = p.id, x = d.x, y = d.y + 170 * C}) end
            p.hitstop, d.hitstop = 12, 12
            self:emit({type = 'hit', p = d.id, by = p.id, kind = 'throw', dmg = dmg, combo = 1, x = d.x, y = d.y + floor(170 * C * d.size),
                       element = p.element, heavy = true, shake = 9, weapon = p.weapon})
        elseif p.t < impact then
            if assist then
                d.t=p.t;d.face=-p.face;d.y=0
            else
            d.x = p.x + p.face * 120 * C
            d.t=p.t;d.face=-p.face
            local lift=p.t<12 and 0 or p.t<24 and (p.t-12)/12 or (30-p.t)/6
            d.y=math.max(0,lift)*160*C
            end
        end
        if p.t >= (assist and 76 or 50) then self:setState(p, 'idle') end
    elseif st == 'hit' or st == 'block' or st == 'cblock' then
        p.vx = p.vx * 85 // 100
        if p.atWall and p.foe and (st == 'hit' or st == 'block' or st == 'cblock') then
            -- pushback transfers to the attacker at the wall
            local a = p.foe
            if a.state == 'attack' or a.state == 'skill' then a.x = a.x - a.face * abs(p.vx) // 2 end
        end
        p.stun = p.stun - 1
        if p.stun <= 0 and p.frozen <= 0 then
            p.combo, p.comboDmg, p.juggle = 0, 0, 0
            self:setState(p, (p.inNow & B.D ~= 0) and 'crouch' or 'idle')
        end
    elseif st == 'airhit' then
        -- physics only
    elseif st == 'down' then
        p.vx = p.vx * 8 // 10
        if p.ko then
            if p.t == 1 then self:emit({type = 'downed', p = p.id}) end
        elseif p.t >= 38 then
            self:setState(p, 'getup')
            p.invul = 18
        end
    elseif st == 'getup' then
        if p.t >= (p.kit.body.getupTicks or 16) then
            p.combo, p.comboDmg, p.juggle = 0, 0, 0
            self:setState(p, 'idle')
            p.invul = 4
        end
    end
end


end
end
