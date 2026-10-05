"""Rollback netplay offline: two clients (gf_online + gf_net) through a simulated relay.

  python -X utf8 game/tests/test_net.py

The relay behaves like game/native/gf-relay.ts: it writes each sender's packet into the
Level variable GF_IN_<slot>. Packets arrive after a random delay and some are lost. Checks:
both clients enter the same match, the confirmed-state hashes agree, no desync is flagged,
and a plain local replay of the confirmed inputs ends in the same state.
"""
import sys
import unittest
from pathlib import Path

from lupa.lua53 import LuaRuntime

sys.stdout.reconfigure(encoding='utf-8')
GAME = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_sim import LOADER  # noqa: E402

RUN = r'''
local latency, jitter, loss, frames, seed = ...
local O = require('gf_online')
local N = require('gf_net')
local Sim = require('gf_sim')
local R = require('gf_roster')

local rng = seed
local function rand() rng = (rng * 1103515245 + 12345) & 0x7fffffff; return rng / 0x7fffffff end

local now = 0
local level = {}                    -- relay output: Level custom variables
local queue = {}                    -- packets in flight {at, slot, list}
local players = {{nonce = 111, slot = 1}, {nonce = 222, slot = 2}}

local function makeIo(i)
    local dirty = {}
    return {
        dirty = dirty,
        player = function(name)
            if name == 'GF_NONCE' then return players[i].nonce end
            if name == 'GF_SLOT' then return players[i].slot end
        end,
        level = function(name) return level[name] end,
        send = function(list)
            if rand() < loss then return end
            local copy = {}
            for k = 1, #list do copy[k] = list[k] end
            queue[#queue + 1] = {at = now + latency + rand() * jitter, slot = i, list = copy}
        end,
        now = function() return now end,
    }
end

local clients = {O.new(makeIo(1)), O.new(makeIo(2))}
level.GF_SLOTS = {8, 1, 1, 0, 0, 0, 0, 0, 0}
clients[1].me.char, clients[2].me.char = 3, 9
clients[1].host.stage = 2

local function makeSimOpts(chars, setup, sd)
    return {chars = {R[chars[1]], R[chars[2]]}, rounds = setup.rounds, time = setup.time, seed = sd}
end

local inLog, hashAt, logged = {}, {}, 0
local masks = {0, 0}
local hold = {0, 0}
local started = {false, false}
for tick = 1, frames do
    now = now + 1 / 60
    -- deliver
    local keep = {}
    for _, p in ipairs(queue) do
        if p.at <= now then
            -- relay: nonce is replaced by 0 is not needed here; slot from the sender
            level['GF_IN_' .. p.slot] = p.list
            for _, c in ipairs(clients) do c.dirty[p.slot] = true end
        else keep[#keep + 1] = p end
    end
    queue = keep
    for i, c in ipairs(clients) do
        O.poll(c)
        if not c.match then
            c.me.ready = true
            O.lobbyTick(c)
            if O.isHost(c) then O.hostStart(c, nil, makeSimOpts) else O.checkJoin(c, nil, makeSimOpts) end
            if c.match then started[i] = tick end
        else
            hold[i] = hold[i] - 1
            if hold[i] <= 0 then
                hold[i] = 1 + math.floor(rand() * 14)
                local m = 0
                for b = 0, 9 do if rand() < 0.18 then m = m | (1 << b) end end
                if m & 12 == 12 then m = m & ~4 end
                masks[i] = m
            end
            O.matchStep(c, masks[i])
            if i == 1 then
                -- log confirmed inputs and the confirmed state's hash (the session prunes both)
                local n = c.match.session
                for f = (logged or 0) + 1, n.confirmed do
                    inLog[f] = {n.inputs[1][f] or 0, n.inputs[2][f] or 0}
                    logged = f
                end
                if n.snaps[n.confirmed] then hashAt[n.confirmed] = n.snaps[n.confirmed]:hash() end
            end
        end
    end
end
-- let the last packets arrive and settle (no new frames)
for _ = 1, 120 do
    now = now + 1 / 60
    local keep = {}
    for _, p in ipairs(queue) do
        if p.at <= now then level['GF_IN_' .. p.slot] = p.list; for _, c in ipairs(clients) do c.dirty[p.slot] = true end
        else keep[#keep + 1] = p end
    end
    queue = keep
    for _, c in ipairs(clients) do
        O.poll(c)
        if c.match then
            local n = c.match.session
            O.send(c, N.packet(n, {match = c.match.id, lobby = O.lobbyWord(c.me.char, true)}))
            N.settle(n)
        end
    end
end

local a, b = clients[1].match, clients[2].match
if not a or not b then return 'nomatch', started[1], started[2] end
local na, nb = a.session, b.session
-- compare confirmed hashes at common frames
local common, diff = 0, 0
for f, h in pairs(na.myHash) do
    local h2 = nb.myHash[f]
    if h2 then common = common + 1; if h2 ~= h then diff = diff + 1 end end
end
-- reference: replay the inputs both sides agree on, locally
local upto = 0
for f in pairs(hashAt) do if f > upto then upto = f end end
local ref = Sim.new(makeSimOpts(a.roster.chars, a.setup, a.seed))
local refOk = true
for f = 1, upto do
    ref:step(inLog[f][1], inLog[f][2])
    if hashAt[f] and hashAt[f] ~= ref:hash() then refOk = false end
end
return 'ok', a.id == b.id, common, diff, na.desync and na.desync.frame or 0, nb.desync and nb.desync.frame or 0,
       refOk, upto, na.stats.rollbacks, na.stats.maxRollback, na.stats.stalls, nb.stats.rollbacks, a.side, b.side
'''


def run(latency, jitter, loss, frames=60 * 50, seed=5):
    rt = LuaRuntime(unpack_returned_tuples=True)
    rt.execute(LOADER, str(GAME / 'lua').replace('\\', '/'))
    f = rt.execute('return function(...) ' + RUN + ' end')
    return f(latency, jitter, loss, frames, seed)


class NetTest(unittest.TestCase):
    def check(self, latency, jitter, loss, seed):
        r = run(latency, jitter, loss, seed=seed)
        self.assertEqual(r[0], 'ok', r)
        _, same_id, common, diff, da, db, ref_ok, upto, rb, maxrb, stalls, rb2, sa, sb = r
        print(f'lat {latency * 1000:.0f}±{jitter * 1000:.0f}ms loss {loss:.0%}: confirmed {upto}, '
              f'hash checks {common}, rollbacks {rb}/{rb2} (max {maxrb}), stalls {stalls}, sides {sa}/{sb}')
        self.assertTrue(same_id)
        self.assertEqual({sa, sb}, {1, 2})
        self.assertGreater(upto, 60 * 30)
        self.assertGreaterEqual(common, 3)        # the session keeps the last 4 checks; desync flags cover the rest
        self.assertEqual(diff, 0)
        self.assertEqual((da, db), (0, 0))
        self.assertTrue(ref_ok, 'local replay of the confirmed inputs differs')

    def test_lan(self):
        self.check(0.02, 0.01, 0.0, 3)

    def test_typical(self):
        self.check(0.06, 0.04, 0.05, 7)

    def test_bad(self):
        self.check(0.10, 0.08, 0.10, 11)


if __name__ == '__main__':
    unittest.main(verbosity=2)
