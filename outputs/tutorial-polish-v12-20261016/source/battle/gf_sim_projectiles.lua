__loaders['gf_sim_projectiles']=function()
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
function S:spawnProj(p, spec, dmgMove, kind)
    local pr = {owner = p.id, x = p.x + p.face * floor((spec.x or 90) * C), y = p.y + floor((spec.y or 120) * C * p.size),
                vx = p.face * floor((spec.speed or 14) * C), vy = floor((spec.vy or 0) * C), w = floor((spec.w or 80) * C),
                h = floor((spec.h or 80) * C), life = spec.life or 60, t = 0, move = dmgMove, kind = kind or 'skill',
                style = spec.style or spec.fx, face = p.face, element = p.element, hits = spec.hits or 1, delay = spec.delay or 0,
                zone = spec.zone}
    self.proj[#self.proj + 1] = pr
    self:emit({type = 'proj', p = p.id, pr = pr})
    return pr
end

function S:updateProj()
    local list = self.proj
    for i = #list, 1, -1 do
        local pr = list[i]
        pr.t = pr.t + 1
        local alive = pr.t <= pr.life
        if pr.t > pr.delay then
            if not pr.zone then
                pr.x = pr.x + pr.vx
                pr.y = pr.y + pr.vy
                if pr.vy < 0 and pr.y <= 0 then pr.y = 0; pr.vy = 0 end
            end
            local owner = self.f[pr.owner]
            local d = owner.foe
            local hb = {self:hurtbox(d)}
            if hb[1] and alive and pr.hits > 0 then
                local x0, x1, y0, y1 = pr.x - pr.w // 2, pr.x + pr.w // 2, pr.y - (pr.zone and 0 or pr.h // 2), pr.y + (pr.zone and pr.h or pr.h // 2)
                if overlap(x0, x1, y0, y1, hb[1], hb[2], hb[3], hb[4]) then
                    local r = self:hit(owner, d, pr.move, pr.kind, {x = d.x, y = d.y + floor(170 * C * d.size)})
                    if r then
                        pr.hits = pr.hits - 1
                        if pr.hits <= 0 then alive = false end
                    end
                end
            end
            -- projectile clash
            if alive and not pr.zone then
                for j = #list, 1, -1 do
                    local o = list[j]
                    if o ~= pr and o.owner ~= pr.owner and not o.zone and o.dead ~= true then
                        if abs(o.x - pr.x) < (o.w + pr.w) // 2 and abs(o.y - pr.y) < (o.h + pr.h) // 2 then
                            o.dead, alive = true, false
                            self:emit({type = 'clash', x = (o.x + pr.x) // 2, y = (o.y + pr.y) // 2})
                        end
                    end
                end
            end
            if pr.x < -WALL - 300 * C or pr.x > WALL + 300 * C then alive = false end
        end
        if not alive or pr.dead then
            table.remove(list, i)
            self:emit({type = 'projEnd', pr = pr})
        end
    end
end

------------------------------------------------------------------ per-fighter logic

end
end
