-- Character art access: generated modules gen/gf_art_<key>.lua hold base64 rect lists.
-- Decoding is incremental (jobs) so a whole character can be prepared over a few frames of
-- a loading / VS screen without one huge callback.
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

-- image: {bytes, n, pal, ax, ay, u, w, h}
local function newImage(src, palette)
    return {bytes = nil, n = src.n, pal = palette, ax = src.ax or 0, ay = src.ay or 0,
            u = src.u or 1, w = src.w, h = src.h, src = src.d}
end

function A.pose(key, tier, pose)
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

-- Job that decodes every pose of a character (and the silhouettes) a slice at a time.
-- job:step(budgetChars) -> true when done.
function A.prepare(key, tier)
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

-- drop decoded bytes of characters not in `keep` (memory between matches)
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
