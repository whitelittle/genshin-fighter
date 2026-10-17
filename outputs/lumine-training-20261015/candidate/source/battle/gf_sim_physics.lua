__loaders['gf_sim_physics']=function()
local floor,abs,max,min=math.floor,math.abs,math.max,math.min
return function(S,C, GRAV, WALL)
function S:physics(p)
    -- velocity, gravity, floor, walls
    p.x = p.x + p.vx
    local air = p.y > 0 or p.vy > 0
    if air then
        p.vy = p.vy - GRAV
        p.y = p.y + p.vy
        if p.y <= 0 then
            p.y = 0
            p.vy = 0
            self:landed(p)
        end
    end
    if p.x < -WALL then p.x = -WALL; p.atWall = -1 elseif p.x > WALL then p.x = WALL; p.atWall = 1 else p.atWall = nil end
end

function S:landed(p)
    local st = p.state
    if st == 'airhit' then
        if p.ko then
            self:setState(p, 'down'); p.vx = 0
            self:emit({type = 'land', p = p.id, hard = true, x = p.x})
            return
        end
        self:setState(p, 'down')
        p.vx = p.vx // 3
        self:emit({type = 'land', p = p.id, hard = true, x = p.x})
    elseif st == 'air' or st == 'skill' then
        p.airMove = nil
        if st == 'skill' and p.move and p.move.style ~= 'rising' then return end
        self:setState(p, 'land'); p.landT = 4; p.vx = 0
        self:emit({type = 'land', p = p.id, x = p.x})
    elseif st == 'backdash' then
        p.vx = 0
    end
end


end
end
