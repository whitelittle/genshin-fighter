"""Scripted walk through the whole front end in the mock client, screenshots per screen.

  python -X utf8 game/tests/walkthrough.py [--canvas 1600x900] [--out game/build/shots/walk]

boot -> intro -> title -> menu -> versus vs CPU -> select (P1, P2) -> stage -> VS -> fight
(both sides driven by the CPU for a while, then the P2 hp is forced to 0) -> result -> menu.
Fails on any Lua error (printerr) or a callback over the instruction budget.
"""
import argparse
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--canvas', default='1600x900')
    ap.add_argument('--out', default=str(HERE.parent / 'build' / 'shots' / 'walk'))
    ap.add_argument('--device', default='KeyboardAndMouse')
    a = ap.parse_args()
    w, h = (int(v) for v in a.canvas.split('x'))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for f in out.glob('*.png'):
        f.unlink()
    c = Client(canvas=(w, h), device=a.device)
    shots = []

    def scene():
        return c.lua('GF_APP() and GF_APP().sceneName')

    def shot(name):
        c.render(out / f'{len(shots):02d}-{name}.png')
        shots.append({'name': name, 'scene': scene(), 'stats': c.stats(), 'calls': c.calls[-1]})

    def wait_scene(name, limit=12):
        for _ in range(int(limit * 60)):
            c.step()
            if scene() == name and not c.lua('GF_APP().trans ~= nil'):
                return True
        raise SystemExit(f'scene {name} not reached; at {scene()}')

    c.run(1.6)
    shot('intro')
    wait_scene('title')
    c.run(1.5)
    shot('title')
    c.press('J')
    wait_scene('menu')
    c.run(0.8)
    shot('menu')
    c.press('S')
    c.run(0.2)
    c.press('J')                     # versus
    c.run(0.4)
    shot('menu-versus')
    c.press('J')                     # vs CPU
    wait_scene('select')
    c.run(0.6)
    shot('select')
    c.press('D'); c.run(0.1); c.press('D'); c.run(0.1)
    c.press('J')                     # P1
    c.run(0.3)
    c.press('S'); c.run(0.1); c.press('A'); c.run(0.1)
    shot('select-p2')
    c.press('J')                     # P2 (CPU opponent picked by the player)
    c.run(0.4)
    shot('select-stage')
    c.press('D'); c.run(0.2)
    c.press('J')
    wait_scene('vs')
    c.run(1.6)
    shot('vs')
    wait_scene('fight', 8)
    c.lua("(function() local s = GF_APP().scene; s.args.cpu = {3, 3} end)()")
    c.run(2.5)
    c.lua("(function() local s = GF_APP().scene; if s.setupAI then s:setupAI() end end)()")
    c.run(4.0)
    shot('fight-1')
    c.run(3.0)
    shot('fight-2')
    # finish quickly: P2 loses every round
    for _ in range(4):
        c.lua("(function() local s = GF_APP().scene; if s.sim then s.sim.f[2].hp = 0 end end)()")
        c.run(5.5)
        if scene() != 'fight':
            break
    shot('after-fight')
    wait_scene('result', 15)
    c.run(1.2)
    shot('result')
    c.press('S'); c.run(0.1); c.press('S'); c.run(0.1)
    c.press('J')
    wait_scene('menu')
    c.run(0.5)
    shot('menu-again')
    rep = {'shots': shots, 'maxInstr': c.max_instr, 'heavy': c.heavy[:10], 'frames': c.frame}
    (out / 'report.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps({'maxInstr': c.max_instr, 'heavy': c.heavy[:5], 'frames': c.frame,
                      'scenes': [s['scene'] for s in shots]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
