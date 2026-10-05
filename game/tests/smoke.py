"""Smoke test: boot the bundle in the mock client, open a scene, render a screenshot.

  python -X utf8 game/tests/smoke.py [scene] [--out path] [--seconds N] [--canvas WxH]
"""
import argparse
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('scene', nargs='?', default='test')
    ap.add_argument('--out', default=str(HERE.parent / 'build' / 'shots' / 'smoke.png'))
    ap.add_argument('--seconds', type=float, default=1.0)
    ap.add_argument('--canvas', default='1600x900')
    ap.add_argument('--device', default='KeyboardAndMouse')
    args = ap.parse_args()
    w, h = (int(v) for v in args.canvas.split('x'))
    t0 = time.time()
    c = Client(canvas=(w, h), device=args.device)
    c.env.GF_FIRST_SCENE = args.scene
    c.run(args.seconds)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    c.render(args.out)
    print('time', round(time.time() - t0, 2), 's; frames', c.frame, 'max instr', c.max_instr,
          'heavy', c.heavy[:5], 'calls max', max(c.calls), 'last', c.calls[-5:])
    print('stats', c.stats())
    print('log', c.logs()[-10:])


if __name__ == '__main__':
    main()
