-- Online room + match session for two players over the server relay (game/native/
-- gf-relay.ts), ported from our 泡泡堂 room module (genshin-ugc paopao/lua/pp_online.lua).
-- Every client sends one packet layout (gf_net N.F): lobby state always, match config when
-- hosting, inputs when playing. The host is the lowest present relay slot; its opponent is
-- the next one (anyone else in the level watches the lobby and waits).
-- Native access goes through `io`:
--   io.player(name) -> number|nil      (PlayerSelf custom variable)
--   io.level(name) -> table|nil        (Level custom variable, 1-based int list)
--   io.send(list)                      (ServerSignal with the int list)
--   io.now() -> seconds
local N = require('gf_net')

local O = {}
O.VERSION = 1
O.TIMEOUT = 4        -- seconds without a new packet before a peer counts as gone
O.DROP_AFTER = 5     -- seconds of silence in a match before the host drops the peer
O.LOBBY_HZ = 5
O.SEND_EVERY = 2     -- ticks between input packets in a match (30 Hz)
O.SLOTS = 8

local F = N.F

-- lobby word: char(5) | ready(1)<<5 | version(4)<<8
function O.lobbyWord(char, ready)
    return (char & 31) | ((ready and 1 or 0) << 5) | (O.VERSION << 8)
end

function O.parseLobby(w)
    w = math.tointeger(w) or 0
    return {char = w & 31, ready = (w >> 5) & 1 == 1, version = (w >> 8) & 15}
end

-- setup word: stage(4) | rounds(2)<<4 | time(2)<<6  (time: 0 = 60, 1 = 99, 2 = none)
local TIMES = {[0] = 60, 99, 999}
function O.setupWord(stage, rounds, time)
    local tc = time == 60 and 0 or (time == 99 and 1 or 2)
    return (stage & 15) | (((rounds - 1) & 3) << 4) | (tc << 6)
end
function O.parseSetup(w)
    w = math.tointeger(w) or 0
    return {stage = w & 15, rounds = ((w >> 4) & 3) + 1, time = TIMES[(w >> 6) & 3] or 99}
end

-- roster word: slotA(4) | slotB(4)<<4 | charA(5)<<8 | charB(5)<<13
function O.rosterWord(sa, sb, ca, cb) return (sa & 15) | ((sb & 15) << 4) | ((ca & 31) << 8) | ((cb & 31) << 13) end
function O.parseRoster(w)
    w = math.tointeger(w) or 0
    return {slots = {w & 15, (w >> 4) & 15}, chars = {(w >> 8) & 31, (w >> 13) & 31}}
end

function O.new(io)
    return {
        io = io, nonce = nil, slot = nil, seq = 0, sentAt = {}, rtt = nil, rttLast = nil,
        present = {}, peers = {}, dirty = io.dirty or {}, lastForce = -1, lastLobbySend = 0,
        me = {char = 1, ready = false}, host = {stage = 1, rounds = 2, time = 99},
        match = nil, lastMatchId = 0, matchCounter = 0, sinceSend = 0,
        stats = {sent = 0, recv = 0, echo = 0},
    }
end

-------------------------------------------------------------------- polling

local function readInt(v)
    return math.tointeger(v) or (type(v) == 'number' and math.floor(v)) or nil
end

function O.poll(o)
    local io = o.io
    local now = io.now()
    -- change callbacks cut reads; still re-read everything 5x a second in case one is missed
    local force = false
    if now - o.lastForce >= 0.2 then o.lastForce, force = now, true end
    local nonce = readInt(io.player('GF_NONCE'))
    if nonce and nonce ~= 0 then o.nonce = nonce end
    local slot = readInt(io.player('GF_SLOT'))
    if slot and slot >= 1 and slot <= O.SLOTS then o.slot = slot end
    local slots = io.level('GF_SLOTS')
    if type(slots) == 'table' and readInt(slots[1]) == O.SLOTS then
        for k = 1, O.SLOTS do o.present[k] = readInt(slots[k + 1]) == 1 end
    end
    for k = 1, O.SLOTS do
        if force or o.dirty[k] ~= false then
            o.dirty[k] = false
            local pkt = io.level('GF_IN_' .. k)
            if type(pkt) == 'table' and #pkt >= N.LEN and readInt(pkt[F.kind]) == N.KIND then
                local seq = readInt(pkt[F.seq]) or 0
                if k == o.slot then
                    -- our own packet came back through the server: round-trip sample
                    local t = o.sentAt[seq]
                    if t and seq ~= o.lastEcho then
                        o.lastEcho = seq
                        local r = now - t
                        o.rttLast = r
                        o.rtt = o.rtt and (o.rtt * 0.8 + r * 0.2) or r
                        o.stats.echo = o.stats.echo + 1
                    end
                else
                    local peer = o.peers[k]
                    if not peer or peer.seq ~= seq then
                        peer = peer or {}
                        o.peers[k] = peer
                        peer.seq, peer.seen, peer.pkt = seq, now, pkt
                        peer.lobby = O.parseLobby(pkt[F.lobby])
                        peer.match = readInt(pkt[F.match]) or 0
                        peer.seed = readInt(pkt[F.seed]) or 0
                        peer.setup = readInt(pkt[F.setup]) or 0
                        peer.roster = readInt(pkt[F.roster]) or 0
                        peer.drop = readInt(pkt[F.drop]) or 0
                        o.stats.recv = o.stats.recv + 1
                        local m = o.match
                        if m and m.session and peer.match == m.id and k == m.peerSlot then
                            N.ingest(m.session, pkt)
                        end
                    end
                end
            end
        end
    end
end

-- handler for RegisterCustomVariableChangedHandler(Level, 'GF_IN_k')
function O.markDirty(o, k) o.dirty[k] = true end

function O.alive(o, k, now)
    if k == o.slot then return o.slot ~= nil end
    local p = o.peers[k]
    return p ~= nil and o.present[k] ~= false and (now - (p.seen or -99)) < O.TIMEOUT
        and p.lobby and p.lobby.version == O.VERSION
end

-- the two lowest live slots play: {host, opponent}
function O.pair(o)
    local now = o.io.now()
    local a, b
    for k = 1, O.SLOTS do
        if O.alive(o, k, now) then
            if not a then a = k elseif not b then b = k end
        end
    end
    return a, b
end

function O.isHost(o)
    local a = O.pair(o)
    return o.slot ~= nil and a == o.slot
end

function O.opponent(o)
    local a, b = O.pair(o)
    if o.slot == a then return b elseif o.slot == b then return a end
    return nil
end

-------------------------------------------------------------------- sending

function O.send(o, pkt)
    if not o.nonce or not o.slot then return false end
    o.seq = o.seq + 1
    pkt[F.nonce], pkt[F.seq] = o.nonce, o.seq
    o.sentAt[o.seq] = o.io.now()
    o.sentAt[o.seq - 200] = nil
    o.io.send(pkt)
    o.stats.sent = o.stats.sent + 1
    return true
end

local function header(o)
    local h = {match = 0, lobby = O.lobbyWord(o.me.char, o.me.ready)}
    local m = o.match
    if m then
        h.match = m.id
        if m.hosting then h.seed, h.setup, h.roster, h.drop = m.seed, m.setupWord, m.rosterWord, m.drop or 0 end
    end
    return h
end

local function emptyPacket(h)
    local p = {}
    for k = 1, N.LEN do p[k] = 0 end
    p[F.kind] = N.KIND
    p[F.match], p[F.lobby] = h.match or 0, h.lobby or 0
    p[F.seed], p[F.setup], p[F.roster], p[F.drop] = h.seed or 0, h.setup or 0, h.roster or 0, h.drop or 0
    return p
end

-- lobby heartbeat (also between matches)
function O.lobbyTick(o)
    local now = o.io.now()
    if now - o.lastLobbySend >= 1 / O.LOBBY_HZ then
        o.lastLobbySend = now
        O.send(o, emptyPacket(header(o)))
    end
end

-------------------------------------------------------------------- matches

function O.bothReady(o)
    local opp = O.opponent(o)
    return o.me.ready and opp ~= nil and o.peers[opp] and o.peers[opp].lobby.ready
end

-- opts for the session; resolve(charIndex, stageIndex) -> simOpts pieces is done by the
-- caller (gf_scene_online) from the match description
local function startSession(o, id, rosterWord, setupWord, seed, hosting, onFrame, makeSimOpts)
    local r = O.parseRoster(rosterWord)
    local side = (r.slots[1] == o.slot) and 1 or 2
    local setup = O.parseSetup(setupWord)
    local simOpts = makeSimOpts(r.chars, setup, seed)
    local session = N.new({simOpts = simOpts, side = side, delay = 2, maxPredict = 12, onFrame = onFrame})
    o.match = {id = id, rosterWord = rosterWord, roster = r, setupWord = setupWord, setup = setup, seed = seed,
               hosting = hosting, session = session, side = side, peerSlot = r.slots[3 - side],
               startedAt = o.io.now(), drop = 0}
    o.lastMatchId = id
    o.sinceSend = 0
    return o.match
end

-- host: start now (both ready). Returns the match or nil + reason.
function O.hostStart(o, onFrame, makeSimOpts)
    if not O.isHost(o) then return nil, '只有房主可以开始' end
    local opp = O.opponent(o)
    if not opp then return nil, '等待对手加入' end
    if not O.bothReady(o) then return nil, '对手还没准备' end
    o.matchCounter = o.matchCounter + 1
    local id = ((o.slot or 1) << 20) | ((math.floor(o.io.now() * 10) & 0xfff) << 8) | (o.matchCounter & 0xff)
    if id == 0 then id = 1 end
    local seed = (math.floor(o.io.now() * 1000) * 2654435761 + (o.nonce or 7)) & 0x7fffffff
    local rw = O.rosterWord(o.slot, opp, o.me.char, math.max(1, o.peers[opp].lobby.char))
    local sw = O.setupWord(o.host.stage, o.host.rounds, o.host.time)
    return startSession(o, id, rw, sw, seed, true, onFrame, makeSimOpts)
end

-- non-host: join the match the host announced, if we are its opponent
function O.checkJoin(o, onFrame, makeSimOpts)
    if o.match then return nil end
    local h = O.pair(o)
    if not h or h == o.slot then return nil end
    local peer = o.peers[h]
    if not peer or peer.match == 0 or peer.match == o.lastMatchId then return nil end
    local r = O.parseRoster(peer.roster)
    if r.slots[2] ~= o.slot then return nil, 'spectating' end
    return startSession(o, peer.match, peer.roster, peer.setup, peer.seed, false, onFrame, makeSimOpts)
end

-- outside the fight loop (lobby, VS screen, loading): keep the peer from timing us out
function O.keepAlive(o)
    local m = o.match
    if not m then return O.lobbyTick(o) end
    o.kaT = (o.kaT or 0) + 1
    if o.kaT >= 6 then
        o.kaT = 0
        O.send(o, N.packet(m.session, header(o)))
    end
end

function O.leaveMatch(o)
    o.match = nil
    o.me.ready = false
end

-- one 60 Hz tick of a match: time sync, local input, advance, send, drops.
-- Returns true when a new frame was simulated.
function O.matchStep(o, localMask)
    local m = o.match
    local n = m.session
    local now = o.io.now()
    local ran = false
    local p = o.peers[m.peerSlot]
    -- handshake: nobody simulates until both sides have seen the other's packet for this
    -- match (otherwise a late joiner could miss frames older than the redundancy window)
    if not m.synced and p and p.match == m.id then m.synced = true end
    if not m.synced then
        o.sinceSend = o.sinceSend + 1
        if o.sinceSend >= O.SEND_EVERY then o.sinceSend = 0; O.send(o, N.packet(n, header(o))) end
        return false
    end
    if N.shouldWait(n) then
        m.waits = (m.waits or 0) + 1
        N.settle(n)
    else
        N.setLocalInput(n, localMask)
        ran = N.advance(n)
    end
    o.sinceSend = o.sinceSend + 1
    if o.sinceSend >= O.SEND_EVERY then
        o.sinceSend = 0
        O.send(o, N.packet(n, header(o)))
    end
    -- host: drop a peer silent for too long; the guest applies the host's drop
    if m.hosting then
        if not n.dropped and now - m.startedAt > O.DROP_AFTER and (not p or now - (p.seen or 0) > O.DROP_AFTER) then
            local from = math.max(n.confirmed + 1, n.last[n.them] + 1)
            N.dropRemote(n, from)
            m.drop = from
        end
    elseif p and p.match == m.id and p.drop ~= 0 and not n.dropped then
        N.dropRemote(n, p.drop)
    end
    return ran
end

-- guest view: the host vanished mid-match, the match cannot continue safely
function O.hostLost(o)
    local m = o.match
    if not m or m.hosting then return false end
    local p = o.peers[m.peerSlot]
    return (not p) or (o.io.now() - (p.seen or 0) > O.DROP_AFTER + 2)
end

function O.peerGone(o)
    local m = o.match
    return m and m.session.dropped ~= nil
end

return O
