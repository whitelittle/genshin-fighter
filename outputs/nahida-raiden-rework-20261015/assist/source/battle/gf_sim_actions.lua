__loaders['gf_sim_actions']=function()
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
local function canAct(p)
    local st = p.state
    return st == 'idle' or st == 'walk' or st == 'back' or st == 'crouch' or st == 'land'
end

function S:faceFoe(p)
    if p.foe.x > p.x then p.face = 1 elseif p.foe.x < p.x then p.face = -1 end
end

function S:neutral(p)
    local nowIn, pr = p.inNow, p.inPressed
    local f, bk = fwdBit(p), backBit(p)
    if nowIn&B.U~=0 and pr&(B.LP|B.HP)~=0 and pr&(B.SK|B.BU|B.TH)==0 then
        self:setState(p,'jumpsq');p.jumpAttack=pr&B.HP~=0 and 'airHeavy' or 'airLight'
        p.jumpDir=nowIn&f~=0 and 1 or nowIn&bk~=0 and -1 or 0
        return
    end
    -- burst > skill > throw > attacks > dash > jump > move
    if pr & B.BU ~= 0 and self:startBurst(p) then return end
    if (pr & B.SK ~= 0 or ((pr & (B.LP | B.HP)) ~= 0 and motion236(p))) and self:startSkill(p) then return end
    if pr & B.TH ~= 0 then self:tryThrow(p) return end
    if pr & B.HP ~= 0 then
        if nowIn & f ~= 0 and abs(p.foe.x - p.x) <= self:throwRange(p) and grounded(p.foe) and p.foe.state ~= 'airhit' then
            self:tryThrow(p) return
        end
        self:startMove(p, nowIn & B.D ~= 0 and 'crouchHeavy' or 'heavy') return
    end
    if pr & B.LP ~= 0 then self:startMove(p, nowIn & B.D ~= 0 and 'crouchLight' or (nowIn & f ~= 0 and p.kit.weapon.forwardLight) and 'forwardLight' or 'light1') return end
    -- dashes: button, or double tap
    local dashF = (pr & B.DA ~= 0 and nowIn & bk == 0) or (pr & f ~= 0 and self.tick - p.lastFwd <= 12)
    local dashB = (pr & B.DA ~= 0 and nowIn & bk ~= 0) or (pr & bk ~= 0 and self.tick - (p.lastBack or -100) <= 12)
    if pr & f ~= 0 then p.lastFwd = self.tick end
    if pr & bk ~= 0 then p.lastBack = self.tick end
    if dashF then
        self:setState(p, 'dash'); p.vx = p.face * floor(p.kit.body.dash * C)
        self:emit({type = 'dash', p = p.id}) p.lastFwd = -100 return
    end
    if dashB then
        self:setState(p, 'backdash'); p.vx = -p.face * floor(p.kit.body.dash * C * 0.85); p.vy = 6 * C; p.invul = 8
        self:emit({type = 'dash', p = p.id, back = true}) p.lastBack = -100 return
    end
    if nowIn & B.U ~= 0 then
        self:setState(p, 'jumpsq')
        p.jumpDir = (nowIn & f ~= 0 and 1) or (nowIn & bk ~= 0 and -1) or 0
        return
    end
    if nowIn & B.D ~= 0 then
        if p.state ~= 'crouch' then self:setState(p, 'crouch') end
        p.vx = 0
        return
    end
    if nowIn & f ~= 0 then
        if p.state ~= 'walk' then self:setState(p, 'walk') end
        p.vx = p.face * floor(p.kit.body.walk * C)
    elseif nowIn & bk ~= 0 then
        if p.state ~= 'back' then self:setState(p, 'back') end
        p.vx = -p.face * floor(p.kit.body.back * C)
    else
        if p.state ~= 'idle' then self:setState(p, 'idle') end
        p.vx = 0
    end
end

-- cancel window: on hit/block, during active and the first 8 recovery frames (or hitstop)
function S:tryCancel(p, m)
    if not p.connected or not m.cancel then return false end
    local pr = p.inPressed
    if pr == 0 then return false end
    local want
    if pr & B.BU ~= 0 then want = 'burst'
    elseif pr & B.SK ~= 0 or ((pr & (B.LP | B.HP)) ~= 0 and motion236(p)) then want = 'skill'
    elseif pr & B.HP ~= 0 then want = (p.inNow&B.D~=0) and 'crouchHeavy' or (p.y>0 and 'airHeavy' or (p.inNow&B.U~=0 and p.kit.weapon.upHeavy and 'upHeavy') or 'heavy')
    elseif pr & B.LP ~= 0 then
        local id = p.moveId or p.airMoveId
        if id == 'light1' then want = 'light2' elseif id == 'light2' then want = 'light3'
        elseif id == 'crouchLight' then want = 'crouchLight' else want = 'light1' end
    end
    if not want then return false end
    local allowed = false
    for _, c in ipairs(m.cancel) do if c == want then allowed = true break end end
    if not allowed then return false end
    if want == 'burst' then return self:startBurst(p) end
    if want == 'skill' then return self:startSkill(p) end
    if p.y > 0 then
        if want ~= 'airHeavy' then return false end
    end
    return self:startMove(p, want)
end

function S:attackUpdate(p)
    local m = p.move
    local t = p.t
    local su, ac = m.startup, m.active
    if m.lunge and t < su then p.vx = p.face * floor(m.lunge * C / su) elseif t < su + ac then p.vx = p.vx * 6 // 10 else p.vx = 0 end
    if t >= su and t < su + ac and not m.whiff then
        if m.projectile then
            if t == su then self:spawnProj(p, m.projectile, m, 'heavy') end
        elseif not p.connected then
            local x0, x1, y0, y1 = boxOf(p, m.box, p.kit.weapon.reach)
            local d = p.foe
            local hx0, hx1, hy0, hy1 = self:hurtbox(d)
            if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
                local kind = (p.moveId and p.moveId:find('eavy')) and 'heavy' or 'light'
                self:hit(p, d, m, kind)
            end
        end
    end
    if t >= su then
        if self:tryCancel(p, m) then return end
    end
    if t >= su + ac + m.recovery then self:setState(p, 'idle') end
end

function S:airAttackUpdate(p)
    local m = p.airMove
    local t = p.airT
    p.airT = t + 1
    local su, ac = m.startup, m.active
    if t >= su and t < su + ac then
        if m.projectile then
            if t == su then self:spawnProj(p, m.projectile, m, 'heavy') end
        elseif not p.connected then
            local x0, x1, y0, y1 = boxOf(p, m.box, p.kit.weapon.reach)
            local hx0, hx1, hy0, hy1 = self:hurtbox(p.foe)
            if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
                self:hit(p, p.foe, m, p.airMoveId == 'airHeavy' and 'heavy' or 'light')
            end
        end
    end
    if t >= su and self:tryCancel(p, m) then return end
    if t >= su + ac + m.recovery then p.airMove = nil end
end

function S:skillUpdate(p)
    local sk = p.move
    local t = p.t
    local d = p.foe
    local st = sk.style
    if sk.invuln and t < sk.invuln then p.invul = max(p.invul, 1) end
    if t == sk.startup then
        self:emit({type = 'skillActive', p = p.id, fx = sk.fx, style = st, element = p.element})
        if st == 'projectile' then
            self:spawnProj(p, {x = 100, y = sk.y or 130, speed = sk.speed, w = sk.w, h = sk.h, life = sk.life, style = sk.fx}, sk, 'skill')
        elseif st == 'zone' then
            local pr = self:spawnProj(p, {x = 0, y = 0, speed = 0, w = sk.w, h = sk.h, life = sk.delay + 8, style = sk.fx, delay = sk.delay, zone = true}, sk, 'skill')
            pr.x = sk.fixedOffset and p.x+p.face*sk.fixedOffset*C or d.x
            pr.y = 0
        elseif st == 'pillar' then
            local pr = self:spawnProj(p, {x = sk.dist, y = 0, speed = 0, w = sk.w, h = sk.h, life = 30, style = sk.fx, delay = 2, zone = true}, sk, 'skill')
            pr.y = 0
            if sk.shield then p.shield = max(p.shield, sk.shield); p.shieldT = 420 end
        elseif st == 'rush' then
            p.vx = p.face * floor(sk.speed * C)
            p.rushHits = sk.hits or 1
        elseif st == 'rising' then
            p.vy = 20 * C
            p.vx = p.face * 3 * C
        end
    end
    if st=='capture' and t>=8 and t<=13 and not p.connected then
        local steps={0,0.10,0.26,0.48,0.74,1};local k=steps[t-7]
        local cx=(p.castX or p.x)+(p.castFace or p.face)*math.floor((110+540*k)*C)
        local cy=p.castY or 190*C
        local hx0,hx1,hy0,hy1=self:hurtbox(d)
        if hx0 and overlap(cx-sk.w*C/2,cx+sk.w*C/2,cy-sk.h*C/2,cy+sk.h*C/2,hx0,hx1,hy0,hy1) then
            local result=self:hit(p,d,{damage=sk.damage,hitstun=sk.hitstun,blockstun=16,push=9,level='mid',energy=8,shake=8},'skill')
            if result then p.captureHitT=t;p.captureHitX=d.x;p.captureHitY=cy end
        end
    end
    if st == 'rush' and t >= sk.startup and t < sk.startup + sk.dur then
        p.vx = p.face * floor(sk.speed * C) * (sk.startup + sk.dur - t) // sk.dur
        if p.rushHits > 0 and (not p.lastRushHit or t - p.lastRushHit >= 5) then
            local x0, x1, y0, y1 = boxOf(p, {x = -20, y = 40, w = sk.w, h = sk.h})
            local hx0, hx1, hy0, hy1 = self:hurtbox(d)
            if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
                local per = {damage = sk.damage // (sk.hits or 1), hitstun = sk.hitstun, blockstun = 14, push = 6,
                             launch = (p.rushHits == 1) and sk.launch or nil, level = 'mid', energy = 4, shake = 5}
                if self:hit(p, d, per, 'skill') then p.rushHits = p.rushHits - 1; p.lastRushHit = t end
            end
        end
    elseif st == 'rush' and t >= sk.startup + sk.dur then
        p.vx = p.vx * 7 // 10
    end
    if st == 'rising' and t >= sk.startup and t < sk.startup + 10 and not p.connected then
        local x0, x1, y0, y1 = boxOf(p, {x = -sk.w / 3, y = 0, w = sk.w, h = sk.h})
        local hx0, hx1, hy0, hy1 = self:hurtbox(d)
        if hx0 and overlap(x0, x1, y0, y1, hx0, hx1, hy0, hy1) then
            self:hit(p, d, {damage = sk.damage, hitstun = sk.hitstun, blockstun = 16, push = 4, launch = sk.launch, level = 'mid', energy = 8, shake = 7}, 'skill')
        end
    end
    local total = sk.startup + (sk.dur or 0) + sk.recovery
    if st == 'rising' then
        if t > sk.startup and p.y <= 0 and p.vy <= 0 then self:setState(p, 'land'); p.landT = 8 return end
        if t >= total + 30 then self:setState(p, p.y > 0 and 'air' or 'idle') end
        return
    end
    if t >= total then
        p.armor = false
        self:setState(p, p.y > 0 and 'air' or 'idle')
    end
end

function S:burstUpdate(p)
    if p.key=='nahida' then
        local t,d,bu=p.t,p.foe,p.move
        local per={damage=bu.damage//bu.hits,hitstun=75,blockstun=18,push=3,level='mid',energy=0,shake=9,launch=13}
        if t==1 then self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style}) end
        if (t==2 or t==28 or t==54) and not d.ko then
            if (d.x-p.x)*p.face>=-bu.range*C and self:burstTouches(p,d,bu.range) then
                per.launch=t==54 and 26 or 13;per.knockdown=t==54
                local result=self:hit(p,d,per,'burst',{unblockable=p.cinematicConfirmed==true,ignoreInvul=p.cinematicConfirmed==true})
                if result=='hit' then p.cinematicConfirmed=true;p.invul=100 end
                if t>2 then self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style}) end
            end
        end
        if p.cinematicConfirmed and not d.ko and t<54 then
            p.x=math.max(-WALL+400*C,math.min(WALL-400*C,p.x))
            d.x=p.x+p.face*330*C;d.y=math.max(d.y,110*C);d.vx=0
        end
        if t>=90 or (not p.cinematicConfirmed and t>=24) then p.cinematicConfirmed=false;self:setState(p,p.y>0 and 'air' or 'idle') end
        return
    end
    if p.key=='raidenshogun' then
        local t,d,bu=p.t,p.foe,p.move
        local per={damage=bu.damage//bu.hits,hitstun=80,blockstun=18,push=3,level='mid',energy=0,shake=12,launch=22}
        if t==2 then
            if (d.x-p.x)*p.face>=-bu.range*C and self:burstTouches(p,d,950) and d.y<420*C then
                local result=self:hit(p,d,per,'burst',{unblockable=false})
                if result=='hit' then
                    p.cinematicConfirmed=true;p.invul=160
                    -- Reserve space for the victim even at the stage wall.
                    p.x=math.max(-WALL+400*C,math.min(WALL-400*C,p.x))
                    d.x=p.x+p.face*330*C
                    d.y=math.max(d.y,130*C);d.vx=0
                    self.freeze=56;self.freezeBy=p.id
                    self:emit({type='burst',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
                    self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
                end
            end
        end
        if p.cinematicConfirmed then
            -- Hold the caught opponent in the cinematic until the final launch.
            if t<70 then d.x=p.x+p.face*330*C;d.y=math.max(d.y,130*C);d.vx=0 end
            if t==35 or t==70 then
                per.launch=t==70 and 28 or 18;per.knockdown=t==70
                self:hit(p,d,per,'burst',{unblockable=true,ignoreInvul=true})
                self:emit({type='burstActive',p=p.id,fx=bu.fx,element=p.element,style=bu.style})
            end
            if t>=100 then p.cinematicConfirmed=false;self:setState(p,p.y>0 and 'air' or 'idle') end
        elseif t>=32 then self:setState(p,p.y>0 and 'air' or 'idle') end
        return
    end
    local bu = p.move
    local t = p.t
    local d = p.foe
    -- the cinematic freeze runs first (self.freeze); t counts after it
    if t == 1 then self:emit({type = 'burstActive', p = p.id, fx = bu.fx, style = bu.style, element = p.element}) end
    local per = {damage = bu.damage // bu.hits, hitstun = 30, blockstun = 18, push = 5, level = 'mid', energy = 0, shake = 10}
    local window = 6 * bu.hits
    if bu.style == 'rush' and t < 22 then
        p.vx = p.face * 30 * C
    else
        p.vx = p.vx * 7 // 10
    end
    if t >= 2 and t < 2 + window and (t - 2) % 6 == 0 then
        local inRange
        if bu.style == 'rain' then inRange = true
        elseif bu.style == 'beam' then
            inRange = (d.x - p.x) * p.face > -40 * C and abs(d.x - p.x) <= bu.range * C and d.y < 420 * C
        elseif bu.style == 'rush' then
            inRange = abs(d.x - p.x) <= 260 * C
        else
            inRange = abs(d.x - p.x) <= bu.range * C
        end
        if inRange then
            local last = (t - 2) // 6 == bu.hits - 1
            per.launch = last and 24 or 9
            per.knockdown = last
            if bu.pull and not last then per.push = -6 end
            self:hit(p, d, per, 'burst', {unblockable = false})
        end
    end
    if t >= 2 + window + 26 then
        self:setState(p, p.y > 0 and 'air' or 'idle')
    end
end


end
end
