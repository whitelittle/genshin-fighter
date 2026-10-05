"""Two full mock clients play online through a simulated relay (lobby -> VS -> fight).

  python -X utf8 game/tests/test_online.py [--seconds 20] [--latency 0.06] [--shots]

Each client gets GF_NETIO (the same interface gf_main builds from custom variables and the
server signal). The relay copies every packet into the shared Level list GF_IN_<slot> after
a delay. Checks: both reach the fight with the same characters and stage, the confirmed
state hashes agree, no desync, no Lua errors; then client 2 goes silent and client 1 must
end the match with "对手已断开连接" and reach the result screen.
"""
import argparse
import random
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402


class Relay:
    def __init__(self, latency, jitter, loss, seed=3):
        self.level = {'GF_SLOTS': [8, 1, 1, 0, 0, 0, 0, 0, 0]}
        self.queue = []
        self.now = 0.0
        self.r = random.Random(seed)
        self.latency, self.jitter, self.loss = latency, jitter, loss
        self.clients = []
        self.muted = set()

    def io(self, c, slot, nonce):
        rt = c.rt
        relay = self
        cache = {}

        def player(name):
            return {'GF_NONCE': nonce, 'GF_SLOT': slot}.get(name)

        def level(name):
            v = relay.level.get(name)
            if v is None:
                return None
            key = (name, id(v))
            if key not in cache:
                cache.clear()
                cache[key] = rt.table_from(v)
            return cache[key]

        def send(lst):
            if slot in relay.muted or relay.r.random() < relay.loss:
                return
            vals = [int(lst[k]) for k in range(1, len(lst) + 1)]
            relay.queue.append((relay.now + relay.latency + relay.r.random() * relay.jitter, slot, vals))

        t = rt.table()
        t.player, t.level, t.send, t.now = player, level, send, lambda: relay.now
        t.dirty = rt.table()
        return t

    def tick(self, dt):
        self.now += dt
        keep = []
        for at, slot, vals in self.queue:
            if at <= self.now:
                self.level[f'GF_IN_{slot}'] = vals
                for c in self.clients:
                    d = c.env.GF_NETIO.dirty
                    d[slot] = True
            else:
                keep.append((at, slot, vals))
        self.queue = keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=float, default=20)
    ap.add_argument('--latency', type=float, default=0.06)
    ap.add_argument('--jitter', type=float, default=0.04)
    ap.add_argument('--loss', type=float, default=0.03)
    ap.add_argument('--shots', action='store_true')
    a = ap.parse_args()
    relay = Relay(a.latency, a.jitter, a.loss)
    cs = []
    for i, build in ((1, True), (2, False)):
        c = Client(build=build)
        c.env.GF_FIRST_SCENE = 'online'
        c.env.GF_NETIO = relay.io(c, i, 1000 + i)
        relay.clients.append(c)
        cs.append(c)
    fails = []

    def check(name, ok):
        print(('PASS ' if ok else 'FAIL ') + name)
        if not ok:
            fails.append(name)

    def scene(c):
        return c.lua('GF_APP() and GF_APP().sceneName')

    def step_all(n=1):
        for _ in range(n):
            relay.tick(1 / 60)
            for c in cs:
                c.step()

    # boot + lobby
    for _ in range(60 * 12):
        step_all()
        if all(scene(c) == 'online' and not c.lua('GF_APP().trans ~= nil') for c in cs):
            break
    check('both in the online lobby', all(scene(c) == 'online' for c in cs))
    step_all(60)
    check('slots assigned', [c.lua('GF_APP().net.slot') for c in cs] == [1, 2])
    check('each sees the other', cs[0].lua("GF_APP().net.peers[2] ~= nil") and cs[1].lua("GF_APP().net.peers[1] ~= nil"))
    # pick characters: client 1 two to the right, client 2 five to the right
    for c, n in ((cs[0], 2), (cs[1], 5)):
        for _ in range(n):
            c.press('D')
            step_all(4)
    cs[0].press('S')                 # host: next stage
    step_all(10)
    for c in cs:
        c.press('J')
        step_all(6)
    if a.shots:
        cs[0].render(HERE.parent / 'build' / 'shots' / 'online-lobby.png')
    for _ in range(60 * 14):
        step_all()
        if all(scene(c) == 'fight' and c.lua("GF_APP().scene.state == 'run'") for c in cs):
            break
    check('both reached the fight', all(scene(c) == 'fight' for c in cs))
    ch = [(c.lua('GF_APP().scene.args.chars[1]'), c.lua('GF_APP().scene.args.chars[2]'), c.lua('GF_APP().scene.stageKey')) for c in cs]
    check(f'same characters and stage {ch[0]}', ch[0] == ch[1])
    sides = [c.lua('GF_APP().scene.side') for c in cs]
    check(f'sides {sides}', sides == [1, 2])
    # fight with random inputs
    keys = ['A', 'D', 'W', 'S', 'J', 'K', 'L', 'U', 'I']
    rr = random.Random(9)
    held = [None, None]
    for t in range(int(a.seconds * 60)):
        if t % 9 == 0:
            for i, c in enumerate(cs):
                if held[i]:
                    c.key(held[i], False)
                held[i] = rr.choice(keys)
                c.key(held[i], True)
        step_all()
        if any(scene(c) != 'fight' for c in cs):
            break
    for i, c in enumerate(cs):
        if held[i]:
            c.key(held[i], False)
    if a.shots:
        cs[0].render(HERE.parent / 'build' / 'shots' / 'online-fight-1.png')
        cs[1].render(HERE.parent / 'build' / 'shots' / 'online-fight-2.png')
    hs = [dict(c.lua('(function() local m = GF_APP().net.match; local t = {} if m then for f, h in pairs(m.session.myHash) do t[f] = h end end return t end)()').items()) if scene(c) == 'fight' else {} for c in cs]
    common = set(hs[0]) & set(hs[1])
    check(f'confirmed hashes agree ({len(common)} common)', len(common) > 0 and all(hs[0][f] == hs[1][f] for f in common))
    des = [c.lua('GF_APP().net.match and GF_APP().net.match.session.desync ~= nil') for c in cs]
    check('no desync flagged', des == [False, False])
    st = [c.lua('GF_APP().net.match and GF_APP().net.match.session.stats.rollbacks or -1') for c in cs]
    mx = [c.lua('GF_APP().net.match and GF_APP().net.match.session.stats.maxRollback or -1') for c in cs]
    print('rollbacks', st, 'max', mx, 'maxInstr', [c.max_instr for c in cs], 'heavy', [c.heavy[:3] for c in cs])
    # client 2 goes silent
    relay.muted.add(2)
    for _ in range(60 * 14):
        relay.tick(1 / 60)
        cs[0].step()
        if scene(cs[0]) == 'result':
            break
    check('peer loss ends the match -> result', scene(cs[0]) == 'result')
    errs = [list(c.H.err.values()) if c.H.err else [] for c in cs]
    check(f'no Lua errors {[len(e) for e in errs]}', not any(errs))
    for e in errs:
        for x in e[:5]:
            print('  ', x)
    if fails:
        raise SystemExit(f'{len(fails)} failed')


if __name__ == '__main__':
    main()
