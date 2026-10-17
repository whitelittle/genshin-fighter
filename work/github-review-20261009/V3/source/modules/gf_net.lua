__loaders['gf_net'] = function()
local Sim = require('gf_sim')

local N = {}

N.KIND = -7201
N.F = {kind = 1, nonce = 2, seq = 3, match = 4, frameEnd = 5, adv = 6, hashFrame = 7, hash = 8,
       lobby = 9, seed = 10, setup = 11, roster = 12, drop = 13, inputs = 14}
N.LEN = 24
N.BITS = 10                         -- U D L R LP HP SK BU DA TH
N.PER_INT = 3                       -- 3 x 10 bits per int (30 bits)
N.INPUT_INTS = N.LEN - N.F.inputs + 1
N.WINDOW = N.INPUT_INTS * N.PER_INT -- frames of input redundancy per packet (33)
N.HASH_EVERY = 60
local MASK = (1 << N.BITS) - 1


function N.packInputs(get, frameEnd)
    local ints = {}
    local first = frameEnd - N.WINDOW + 1
    for k = 0, N.INPUT_INTS - 1 do
        local v = 0
        for j = 0, N.PER_INT - 1 do
            local f = first + k * N.PER_INT + j
            local b = f >= 1 and (get(f) or 0) or 0
            v = v | ((b & MASK) << (N.BITS * j))
        end
        ints[k + 1] = v
    end
    return ints
end

function N.unpackInputs(list, frameEnd)
    local out = {}
    local first = frameEnd - N.WINDOW + 1
    for k = 0, N.INPUT_INTS - 1 do
        local v = math.tointeger(list[N.F.inputs + k]) or 0
        for j = 0, N.PER_INT - 1 do
            local f = first + k * N.PER_INT + j
            if f >= 1 then out[f] = (v >> (N.BITS * j)) & MASK end
        end
    end
    return out
end


function N.new(opts)
    local me = opts.side
    local n = {
        state = Sim.new(opts.simOpts), onFrame = opts.onFrame, onConfirmed = opts.onConfirmed,
        delay = opts.delay or 2, maxPredict = opts.maxPredict or 12,
        me = me, them = 3 - me, inputs = {[1] = {}, [2] = {}}, last = {[1] = 0, [2] = 0}, used = {},
        snaps = {}, confirmed = 0, rollbackFrom = nil, frame = 0,
        myHash = {}, theirHash = {}, desync = nil, dropped = nil,
        stats = {rollbacks = 0, resimFrames = 0, maxRollback = 0, stalls = 0},
        remoteFrameEnd = 0, remoteAdv = 0,
    }
    n.snaps[0] = Sim.copy(n.state)
    return n
end

function N.setLocalInput(n, mask)
    local f = n.frame + 1 + n.delay
    local list, last = n.inputs[n.me], n.last[n.me]
    for g = last + 1, f - 1 do list[g] = list[last] or 0 end
    if f > last then
        list[f] = mask & MASK
        n.last[n.me] = f
    end
end

function N.dropRemote(n, from)
    if n.dropped then return end
    n.dropped = from
    local list, last = n.inputs[n.them], n.last[n.them]
    for f = last + 1, from - 1 do list[f] = list[last] or 0 end
    n.last[n.them] = math.max(last, from - 1)
end

local function inputFor(n, side, f)
    if side == n.them and n.dropped and f >= n.dropped then return 0, true end
    local list = n.inputs[side]
    local b = list[f]
    if b ~= nil then return b, true end
    return list[n.last[side]] or 0, false   -- prediction: hold the last known mask
end

function N.receive(n, frames, frameEnd, adv)
    if frameEnd and frameEnd > n.remoteFrameEnd then
        n.remoteFrameEnd, n.remoteAdv = frameEnd, adv or 0
    end
    local side = n.them
    local list = n.inputs[side]
    local f = n.last[side] + 1
    while frames[f] ~= nil do
        if n.dropped and f >= n.dropped then break end
        list[f] = frames[f]
        local u = n.used[f]
        if u ~= nil and u ~= frames[f] and f <= n.frame then
            if not n.rollbackFrom or f < n.rollbackFrom then n.rollbackFrom = f end
        end
        f = f + 1
    end
    n.last[side] = f - 1
end

local function stepFrame(n, f, resim)
    local a = inputFor(n, 1, f)
    local b = inputFor(n, 2, f)
    n.used[f] = n.them == 1 and a or b
    n.state:step(a, b)
    n.frame = f
    n.snaps[f] = Sim.copy(n.state)
    n.snaps[f].events = n.state.events
    if n.onFrame then n.onFrame(n.state, f, resim) end
end

local function updateConfirmed(n)
    local c = n.frame
    local l = n.dropped and math.huge or n.last[n.them]
    if l < c then c = l end
    if c > n.confirmed then
        for f = n.confirmed + 1, c do
            if n.onConfirmed and n.snaps[f] then n.onConfirmed(n.snaps[f],f) end
            if f % N.HASH_EVERY == 0 and n.snaps[f] then
                n.myHash[f] = n.snaps[f]:hash()
                local theirs = n.theirHash[f]
                if theirs and theirs ~= n.myHash[f] and not n.desync then n.desync = {frame = f} end
                n.theirHash[f] = nil
            end
        end
        for f = n.confirmed, c - 1 do
            n.snaps[f] = nil
            n.used[f] = nil
        end
        for f, _ in pairs(n.myHash) do if f < c - N.HASH_EVERY * 4 then n.myHash[f] = nil end end
        local old = c - N.WINDOW * 3
        if old > 0 then n.inputs[1][old], n.inputs[2][old] = nil, nil end
        n.confirmed = c
    end
end

function N.noteHash(n, f, h)
    if not f or f <= 0 or not h then return end
    local mine = n.myHash[f]
    if mine then
        if mine ~= h and not n.desync then n.desync = {frame = f} end
    elseif f > n.confirmed - N.HASH_EVERY * 4 then
        n.theirHash[f] = h
    end
end

local function rollback(n)
    local from = n.rollbackFrom
    n.rollbackFrom = nil
    if not from then return end
    local target = n.frame
    local base = n.snaps[from - 1]
    if not base then return end      -- older than the confirmed window: cannot happen
    n.state = Sim.copy(base)
    n.frame = from - 1
    local count = 0
    while n.frame < target do
        stepFrame(n, n.frame + 1, true)
        count = count + 1
    end
    n.stats.rollbacks = n.stats.rollbacks + 1
    n.stats.resimFrames = n.stats.resimFrames + count
    if count > n.stats.maxRollback then n.stats.maxRollback = count end
end

function N.settle(n)
    rollback(n)
    updateConfirmed(n)
end

function N.advance(n)
    rollback(n)
    updateConfirmed(n)
    if n.frame - n.confirmed >= n.maxPredict then
        n.stats.stalls = n.stats.stalls + 1
        updateConfirmed(n)
        return false
    end
    stepFrame(n, n.frame + 1, false)
    updateConfirmed(n)
    return true
end

function N.advantage(n)
    if n.dropped then return 0 end
    return math.max(0, n.frame - n.remoteFrameEnd)
end

function N.shouldWait(n)
    if n.dropped then return false end
    return (N.advantage(n) - n.remoteAdv) >= 3
end

function N.packet(n, header)
    local p = {}
    local F = N.F
    local frameEnd = n.last[n.me]
    p[F.kind] = N.KIND
    p[F.nonce] = header.nonce or 0
    p[F.seq] = header.seq or 0
    p[F.match] = header.match or 0
    p[F.frameEnd] = frameEnd
    p[F.adv] = N.advantage(n)
    local hf = 0
    for f in pairs(n.myHash) do if f > hf then hf = f end end
    p[F.hashFrame] = hf
    p[F.hash] = hf > 0 and n.myHash[hf] or 0
    p[F.lobby] = header.lobby or 0
    p[F.seed] = header.seed or 0
    p[F.setup] = header.setup or 0
    p[F.roster] = header.roster or 0
    p[F.drop] = header.drop or 0
    local list = n.inputs[n.me]
    local ints = N.packInputs(function(f) return list[f] end, frameEnd)
    for k = 1, #ints do p[F.inputs + k - 1] = ints[k] end
    return p
end

function N.ingest(n, pkt)
    local F = N.F
    if not pkt or #pkt < N.LEN or math.tointeger(pkt[F.kind]) ~= N.KIND then return end
    local frameEnd = math.tointeger(pkt[F.frameEnd]) or 0
    if frameEnd > 0 then
        N.receive(n, N.unpackInputs(pkt, frameEnd), frameEnd, math.tointeger(pkt[F.adv]))
    end
    N.noteHash(n, math.tointeger(pkt[F.hashFrame]), math.tointeger(pkt[F.hash]))
end

return N
end
