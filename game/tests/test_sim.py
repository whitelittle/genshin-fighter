"""Headless tests of the fight simulation (pure Lua, no client): determinism, rounds, combos.

  python -X utf8 game/tests/test_sim.py
"""
import sys
import unittest
from pathlib import Path

from lupa.lua53 import LuaRuntime

sys.stdout.reconfigure(encoding='utf-8')
GAME = Path(__file__).resolve().parent.parent
LUA = GAME / 'lua'

LOADER = r'''
local dir = ...
local cache = {}
function require(name)
    if cache[name] then return cache[name] end
    local path = dir .. '/' .. name .. '.lua'
    local f = io.open(path, 'r')
    if not f then path = dir .. '/gen/' .. name .. '.lua'; f = io.open(path, 'r') end
    local src = f:read('a'); f:close()
    local m = assert(load(src, '@' .. name))()
    cache[name] = m
    return m
end
'''


def runtime():
    rt = LuaRuntime(unpack_returned_tuples=True)
    rt.execute(LOADER, str(LUA).replace('\\', '/'))
    return rt


MATCH = r'''
local a, b, lv1, lv2, seed, maxTicks = ...
local S = require('gf_sim')
local AI = require('gf_ai')
local R = require('gf_roster')
local by = {}
for _, c in ipairs(R) do by[c.key] = c end
local sim = S.new({chars = {by[a], by[b]}, rounds = 2, time = 99, seed = seed})
local ai1, ai2 = AI.new(sim, 1, lv1, seed + 1), AI.new(sim, 2, lv2, seed + 2)
local counts = {}
local ticks = 0
while sim.phase ~= 'over' and ticks < maxTicks do
    sim:step(ai1:tick(), ai2:tick())
    ticks = ticks + 1
    for _, e in ipairs(sim.events) do counts[e.type] = (counts[e.type] or 0) + 1 end
end
return sim, counts, ticks
'''


class SimTest(unittest.TestCase):
    def match(self, a='raidenshogun', b='furina', lv=(3, 3), seed=7, ticks=60 * 60 * 8):
        rt = runtime()
        f = rt.execute('return function(...) ' + MATCH + ' end')
        sim, counts, n = f(a, b, lv[0], lv[1], seed, ticks)
        return sim, dict(counts), n

    def test_match_finishes_with_hits(self):
        sim, counts, n = self.match()
        self.assertEqual(sim.phase, 'over', f'phase {sim.phase} after {n} ticks, {counts}')
        self.assertGreater(counts.get('hit', 0), 20, counts)
        self.assertGreater(counts.get('block', 0), 0, counts)
        self.assertGreaterEqual(counts.get('roundEnd', 0), 2, counts)
        print('match', n, 'ticks', counts, 'wins', sim.f[1].wins, sim.f[2].wins)

    def test_deterministic(self):
        rt = runtime()
        f = rt.execute('return function(...) ' + MATCH + ' end')
        h = []
        for _ in range(2):
            sim, counts, n = f('zhongli', 'mavuika', 2, 3, 99, 60 * 40)
            h.append((sim.hash(sim), n))
        self.assertEqual(h[0], h[1])

    def test_double_ko_awards_nobody(self):
        rt = runtime()
        f = rt.execute(r'''return function()
            local S = require('gf_sim')
            local R = require('gf_roster')
            local sim = S.new({chars = {R[1], R[2]}, rounds = 2, time = 99, seed = 3})
            local ends = {}
            for _ = 1, 600 do
                if sim.phase == 'fight' and not ends.forced then
                    sim.f[1].hp, sim.f[2].hp = 0, 0
                    ends.forced = true
                end
                sim:step(0, 0)
                for _, e in ipairs(sim.events) do
                    if e.type == 'roundEnd' then ends.reason, ends.winner = e.reason, e.winner or 0 end
                end
                if ends.reason then break end
            end
            return ends.reason, ends.winner, sim.f[1].wins, sim.f[2].wins
        end''')
        reason, winner, w1, w2 = f()
        self.assertEqual((reason, winner, w1, w2), ('double', 0, 0, 0))

    def test_all_characters_fight(self):
        rt = runtime()
        f = rt.execute('return function(...) ' + MATCH + ' end')
        keys = [c.key for c in rt.execute("return require('gf_roster')").values()]
        for i, k in enumerate(keys):
            other = keys[(i + 5) % len(keys)]
            sim, counts, n = f(k, other, 3, 2, 11 + i, 60 * 60 * 6)
            counts = dict(counts)
            self.assertGreater(counts.get('hit', 0), 5, f'{k} vs {other}: {counts}')
            self.assertGreater(counts.get('skill', 0) + counts.get('burst', 0), 0, f'{k} vs {other}: {counts}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
