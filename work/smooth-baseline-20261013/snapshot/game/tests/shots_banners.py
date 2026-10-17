"""Screenshots of the fight announcements (round, fight, K.O., winner) in the mock client.

  python -X utf8 game/tests/shots_banners.py [--canvas 1600x900]
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402

ARGS = "{chars = {'kamisatoayaka', 'mavuika'}, mode = 'versus', stage = 'mondstadt', cpu = {3, 3}}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--canvas', default='1600x900')
    ap.add_argument('--out', default=str(HERE.parent / 'build' / 'shots' / 'banners'))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    w, h = (int(v) for v in a.canvas.split('x'))
    c = Client(canvas=(w, h))
    c.env.GF_FIRST_SCENE = 'fight'
    c.env.GF_FIRST_ARGS = c.lua(ARGS)
    for _ in range(60 * 20):
        c.step()
        if c.lua("GF_APP() ~= nil and GF_APP().scene ~= nil and GF_APP().scene.state == 'run'"):
            break
    marks = {}
    seen = set()
    for _ in range(60 * 40):
        c.step()
        if c.lua("GF_APP().sceneName") != 'fight' or not c.lua("GF_APP().scene.banners ~= nil"):
            break
        for b in range(1, 4):
            txt = c.lua(f"(GF_APP().scene.banners[{b}] or {{}}).text")
            t = c.lua(f"(GF_APP().scene.banners[{b}] or {{}}).t")
            if txt and t in (8, 30) and (txt, t) not in seen:
                seen.add((txt, t))
                name = f'{len(seen):02d}-{t}'
                c.render(out / f'{name}.png')
                marks[name] = txt
        if c.lua("GF_APP().scene.sim.phase == 'fight'") and not c.lua("GF_APP().scene.ended"):
            c.lua("(function() local s = GF_APP().scene; if s.sim.tick % 600 == 300 then s.sim.f[2].hp = 0 end end)()")
        if c.lua("GF_APP().sceneName") != 'fight':
            break
    print(marks)
    print('max instr', c.max_instr)


if __name__ == '__main__':
    main()
