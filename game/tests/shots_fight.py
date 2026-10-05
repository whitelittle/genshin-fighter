"""AI vs AI fight in the mock client; saves screenshots and a per-frame cost report.

  python -X utf8 game/tests/shots_fight.py [--p1 raidenshogun] [--p2 furina] [--stage liyue]
         [--seconds 40] [--every 2.0] [--canvas 1600x900] [--quality hi]
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--p1', default='raidenshogun')
    ap.add_argument('--p2', default='furina')
    ap.add_argument('--stage', default='liyue')
    ap.add_argument('--seconds', type=float, default=30)
    ap.add_argument('--every', type=float, default=2.0)
    ap.add_argument('--canvas', default='1600x900')
    ap.add_argument('--quality', default='hi')
    ap.add_argument('--out', default=str(HERE.parent / 'build' / 'shots' / 'fight'))
    ap.add_argument('--burst', action='store_true', help='start with full energy (see bursts early)')
    args = ap.parse_args()
    w, h = (int(v) for v in args.canvas.split('x'))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob('*.png'):
        old.unlink()
    c = Client(canvas=(w, h))
    c.env.GF_FIRST_SCENE = 'fight'
    c.env.GF_FIRST_ARGS = c.rt.table_from({
        'chars': c.rt.table_from([args.p1, args.p2]), 'mode': 'demo', 'stage': args.stage,
        'cpu': c.rt.table_from([3, 3]), 'seed': 5, 'infinite': args.burst})
    t0 = time.time()
    shots = []
    nxt = 0.0
    frames = int(args.seconds * 60)
    worst = []
    for i in range(frames):
        c.step()
        if c.t >= nxt:
            name = f'{i:05d}.png'
            c.render(out / name)
            shots.append(name)
            nxt += args.every
        worst.append((c.calls[-1], i))
    worst.sort(reverse=True)
    st = c.stats()
    rep = {'frames': frames, 'wall': round(time.time() - t0, 1), 'maxInstr': c.max_instr, 'heavy': c.heavy[:10],
           'callsWorst': worst[:8], 'callsMean': round(sum(c.calls) / len(c.calls), 1), 'stats': st, 'shots': len(shots)}
    (out / 'report.json').write_text(json.dumps(rep, indent=1), encoding='utf-8')
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
