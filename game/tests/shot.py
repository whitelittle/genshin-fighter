"""Boot straight into one scene and save screenshots (design iteration).

  python -X utf8 game/tests/shot.py menu [--args "{mode='versus', cpu=true}"] [--keys "S,S"]
                                         [--at 1.2,2.5] [--canvas 1600x900] [--device Mobile]

Writes game/build/shots/scene-<name>-<n>.png for each time in --at (seconds after the
scene is reached). --keys are pressed (comma separated, '.' = wait 0.2 s) before the shots.
"""
import argparse
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scene')
    ap.add_argument('--args', default=None)
    ap.add_argument('--keys', default='')
    ap.add_argument('--at', default='1.5')
    ap.add_argument('--canvas', default='1600x900')
    ap.add_argument('--device', default='KeyboardAndMouse')
    ap.add_argument('--tag', default='')
    ap.add_argument('--no-build', action='store_true')
    a = ap.parse_args()
    w, h = (int(v) for v in a.canvas.split('x'))
    c = Client(canvas=(w, h), device=a.device, build=not a.no_build)
    c.env.GF_FIRST_SCENE = a.scene
    if a.args:
        c.env.GF_FIRST_ARGS = c.lua(a.args)
    for _ in range(60 * 20):
        c.step()
        if c.lua('GF_APP() ~= nil and GF_APP().scene ~= nil'):
            break
    c.run(0.3)
    for k in [k for k in a.keys.split(',') if k]:
        if k == '.':
            c.run(0.2)
        else:
            c.press(k)
            c.run(0.12)
    out = HERE.parent / 'build' / 'shots'
    out.mkdir(parents=True, exist_ok=True)
    t = 0.0
    for i, at in enumerate(float(v) for v in a.at.split(',')):
        c.run(max(0.0, at - t))
        t = at
        p = out / f'scene-{a.scene}{a.tag}-{i}.png'
        c.render(p)
        print(p)
    errs = list(c.H.err.values()) if c.H.err else []
    print('errors', len(errs), errs[:3], 'maxInstr', c.max_instr, 'heavy', c.heavy[:3])


if __name__ == '__main__':
    main()
