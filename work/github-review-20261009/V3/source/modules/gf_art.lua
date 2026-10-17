__loaders['gf_art'] = function()


local U = require('gf_util')
local R = require('gf_roster')

local A = {}
A.POSES = {'idle', 'walk1', 'walk2', 'jump', 'crouch', 'crouchGuard', 'guard',
           'slash', 'special', 'qRelease', 'hurt', 'down'}
A.roster = R
A.byKey = {}
for i, c in ipairs(R) do c.index = i; A.byKey[c.key] = c end

local mods = {}
local function mod(key)
    local m = mods[key]
    if not m then
        m = require('gf_art_' .. key)
        mods[key] = m
    end
    return m
end
A.mod = mod

local cache = {}          -- key..tier..pose -> image
local palCache = {}

local function pal(key, tier)
    local k = key .. ':' .. tier
    local p = palCache[k]
    if not p then
        p = U.palette(mod(key)[tier].pal)
        palCache[k] = p
    end
    return p
end
A.pal = pal

local function newImage(src, palette)
    return {bytes = nil, n = src.n, pal = palette, ax = src.ax or 0, ay = src.ay or 0,
            u = src.u or 1, w = src.w, h = src.h, src = src.d}
end

local animations
function A.animation(key,tier,pose)
    tier='lo'
    if key ~= 'raidenshogun' and key ~= 'nahida' then return nil end
    animations = animations or require('gf_animation_data')
    local char=animations[key=='raidenshogun' and 'raiden' or 'nahida']
    local bank=char and char[tier]
    local aliases={idle='basic_0',walk1='basic_2',walk2='basic_4',jump='move_1',crouch='guard_1',crouchGuard='guard_7',guard='guard_6',slash='light_2',special='skill_2',qRelease=key=='raidenshogun' and 'qburst_3' or 'skill_6',hurt='hurt_0',down='hurt_3'}
    local img=bank and bank[aliases[pose] or pose]
    if not img and bank then local extra=require('gf_inbetween_data');local c=extra.poses[key=='raidenshogun' and 'raiden' or 'nahida'];img=c and c[tier] and c[tier][pose] end
    if img and img.d then
        local raw=U.decodeAll(img.d);local values={}
        for i=1,img.n*5 do values[i]=raw[i*2-1]+raw[i*2]*256 end
        img.bytes=values;img.d=nil
    end
    if img then img.pal=bank.pal; if not img.baked and key=='raidenshogun' and (aliases[pose] or pose):match('^qburst_') then img.originalU=img.originalU or img.u;img.u=img.originalU*0.77 end end
    if img and not img.baked then
        local u=img.u;local bytes={}
        for i=1,#img.bytes,5 do
            for k=0,3 do bytes[i+k]=img.bytes[i+k]*u end
            bytes[i+4]=img.bytes[i+4]
        end
        img.bytes=bytes;img.ax=img.ax*u;img.ay=img.ay*u;img.w=img.w*u;img.h=img.h*u
        img.seam=0.08*u;img.u=1;img.baked=true
    end
    return img
end
function A.pose(key, tier, pose)
    tier='lo'
    local animated=A.animation(key,tier,pose)
    if animated then return animated end
    local k = key .. ':' .. tier .. ':' .. pose
    local img = cache[k]
    if not img then
        local src = mod(key)[tier][pose]
        img = newImage(src, pal(key, tier))
        cache[k] = img
    end
    if not img.bytes then img.bytes = U.decodeAll(img.src) end
    return img
end

function A.silhouette(key, pose)
    local animated=A.animation(key,'lo',pose)
    if animated then return animated end
    local k = key .. ':sil:' .. pose
    local img = cache[k]
    if not img then
        local m = mod(key)
        local src = m.sil[pose]
        local lo = m.lo[pose]
        img = {bytes = U.decodeAll(src.d), n = src.n, pal = {{255, 255, 255, 255}},
               ax = lo.ax, ay = lo.ay, u = lo.u, w = lo.w, h = lo.h}
        cache[k] = img
    end
    return img
end

local function picture(key, which)
    local k = key .. ':' .. which
    local img = cache[k]
    if not img then
        local src = mod(key)[which]
        img = {bytes = U.decodeAll(src.d), n = src.n, pal = U.palette(src.pal), ax = src.s / 2, ay = src.s,
               u = 1, w = src.s, h = src.s}
        cache[k] = img
    end
    return img
end
function A.face(key) return picture(key, 'face') end
function A.round(key) return picture(key, 'round') end
function A.portrait(key) return picture(key, 'portrait') end

function A.prepare(key, tier)
    if key == 'raidenshogun' or key == 'nahida' then
        -- Decode all body poses behind the loading curtain, including inbetweens.
        -- Jobs keep private decoder state; the shared image is committed atomically.
        animations = animations or require('gf_animation_data')
        local name = key == 'raidenshogun' and 'raiden' or 'nahida'
        local extra = require('gf_inbetween_data')
        local list, seen = {}, {}
        for _, bank in ipairs({animations[name].lo, extra.poses[name].lo}) do
            for pose, img in pairs(bank) do
                if type(img) == 'table' and img.n and not img.baked and not seen[pose] then
                    list[#list + 1] = {pose=pose, img=img}
                    seen[pose] = true
                end
            end
        end
        table.sort(list, function(a,b) return a.pose < b.pose end)
        local job = {i=1, total=#list, completed=0}
        function job:step(budget)
            local entry = list[self.i]
            if not entry then return true end
            local img = entry.img
            if not img.baked then
                if img.d then
                    self.decoder = self.decoder or U.decoder(img.d)
                    if not self.decoder:step(math.max(4, math.min(budget or 9000, 9000))) then return false end
                    local raw, values = self.decoder.bytes, {}
                    for i=1,img.n*5 do values[i]=raw[i*2-1]+raw[i*2]*256 end
                    img.bytes, img.d = values, nil
                end
                A.animation(key, 'lo', entry.pose)
            end
            self.decoder = nil
            self.completed = self.i
            self.i = self.i + 1
            return self.i > self.total
        end
        return job
    end
    local list = {}
    for _, p in ipairs(A.POSES) do list[#list + 1] = p end
    local job = {i = 1, cur = nil}
    function job.step(_, budget)
        while budget > 0 do
            local pose = list[job.i]
            if not pose then return true end
            local k = key .. ':' .. tier .. ':' .. pose
            local img = cache[k]
            if not img then
                img = newImage(mod(key)[tier][pose], pal(key, tier))
                cache[k] = img
            end
            if img.bytes then
                job.i = job.i + 1
                A.silhouette(key, pose)
            else
                job.cur = job.cur or U.decoder(img.src)
                local before = job.cur.i
                if job.cur:step(budget) then
                    img.bytes = job.cur.bytes
                    job.cur = nil
                end
                budget = budget - math.max(4, (job.cur and job.cur.i or #img.src + 1) - before)
            end
        end
        return list[job.i] == nil
    end
    return job
end

function A.trim(keep)
    local k2 = {}
    for _, k in ipairs(keep) do k2[k] = true end
    for k, img in pairs(cache) do
        local key = k:match('^([^:]+)')
        if not k2[key] and not k:find(':face') and not k:find(':portrait') then
            img.bytes = nil
            if k:find(':sil:') then cache[k] = nil end
        end
    end
end

return A
end
