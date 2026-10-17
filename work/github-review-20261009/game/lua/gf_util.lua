-- Small shared helpers: maths, easing, colours, base64 rect decoding.
local U = {}

local floor, sqrt, sin, cos, pi = math.floor, math.sqrt, math.sin, math.cos, math.pi
U.floor = floor

function U.clamp(v, a, b) if v < a then return a elseif v > b then return b end return v end
function U.lerp(a, b, t) return a + (b - a) * t end
function U.round(v) return floor(v + 0.5) end
function U.sign(v) if v > 0 then return 1 elseif v < 0 then return -1 end return 0 end
function U.approach(v, target, step)
    if v < target then return math.min(v + step, target) end
    return math.max(v - step, target)
end

-- easing (t in 0..1)
U.ease = {
    linear = function(t) return t end,
    inQuad = function(t) return t * t end,
    outQuad = function(t) return t * (2 - t) end,
    inOutQuad = function(t) if t < 0.5 then return 2 * t * t end return -1 + (4 - 2 * t) * t end,
    outCubic = function(t) t = t - 1 return t * t * t + 1 end,
    inCubic = function(t) return t * t * t end,
    inOutCubic = function(t) if t < 0.5 then return 4 * t * t * t end t = 2 * t - 2 return 0.5 * t * t * t + 1 end,
    outBack = function(t) local s = 1.70158 t = t - 1 return t * t * ((s + 1) * t + s) + 1 end,
    outExpo = function(t) if t >= 1 then return 1 end return 1 - 2 ^ (-10 * t) end,
    outElastic = function(t)
        if t <= 0 then return 0 elseif t >= 1 then return 1 end
        return 2 ^ (-10 * t) * sin((t * 10 - 0.75) * (2 * pi / 3)) + 1
    end,
    outSine = function(t) return sin(t * pi / 2) end,
    inOutSine = function(t) return -(cos(pi * t) - 1) / 2 end,
}

function U.hex(s)
    local r, g, b, a = s:match('#?(%x%x)(%x%x)(%x%x)(%x?%x?)')
    return {tonumber(r, 16), tonumber(g, 16), tonumber(b, 16), a ~= '' and tonumber(a, 16) or 255}
end

function U.mix(c1, c2, t)
    return {c1[1] + (c2[1] - c1[1]) * t, c1[2] + (c2[2] - c1[2]) * t, c1[3] + (c2[3] - c1[3]) * t,
            (c1[4] or 255) + ((c2[4] or 255) - (c1[4] or 255)) * t}
end

-- deterministic hash noise (no math.random in presentation code that must be stable)
function U.hash(n)
    n = (n * 1103515245 + 12345) & 0x7fffffff
    n = (n ~ (n >> 13)) * 1274126177 & 0x7fffffff
    return (n & 0xffff) / 65535
end

------------------------------------------------------------------------ base64 -> bytes

local B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
local DEC = {}
for i = 1, 64 do DEC[B64:byte(i)] = i - 1 end
U.B64DEC = DEC

-- Incremental decoder: returns a job; job:step(nChars) decodes up to nChars characters into
-- job.bytes (a flat array of byte values); returns true when finished. Used to spread big
-- decodes over frames (the client aborts callbacks past ~1.2 M VM instructions).
function U.decoder(s)
    return {s = s, i = 1, n = #s, bytes = {}, k = 0, step = U.decodeStep}
end

function U.decodeStep(job, budget)
    local s, i, n, out, k = job.s, job.i, job.n, job.bytes, job.k
    local stop = math.min(n, i + budget - 1)
    stop = stop - ((stop - i + 1) % 4)
    if stop < i and i <= n then stop = math.min(n, i + 3) end
    local byte = string.byte
    while i + 3 <= stop do
        local a, b, c, d = byte(s, i, i + 3)
        local v = (DEC[a] << 18) | (DEC[b] << 12) | (DEC[c] << 6) | DEC[d]
        out[k + 1] = (v >> 16) & 255
        out[k + 2] = (v >> 8) & 255
        out[k + 3] = v & 255
        k = k + 3
        i = i + 4
    end
    job.i, job.k = i, k
    return i > n
end

function U.decodeAll(s)
    local job = U.decoder(s)
    job:step(#s + 4)
    return job.bytes
end

-- palette string (base64 of r,g,b triples) -> list of {r,g,b}
function U.palette(s)
    local b = U.decodeAll(s)
    local pal = {}
    for i = 1, #b - 2, 3 do pal[#pal + 1] = {b[i], b[i + 1], b[i + 2], 255} end
    return pal
end

return U
