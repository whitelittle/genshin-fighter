"""Render every stage (or one) at a few camera positions into game/build/shots/stages/.

  python -X utf8 game/tests/shots_stages.py [stage ...]
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from harness import Client  # noqa: E402

STAGES = ['mondstadt', 'liyue', 'inazuma', 'sumeru', 'fontaine', 'natlan', 'snezhnaya']


def main():
    names = sys.argv[1:] or STAGES
    out = HERE.parent / 'build' / 'shots' / 'stages'
    out.mkdir(parents=True, exist_ok=True)
    from PIL import Image
    for name in names:
        tiles = []
        for cx, zoom in ((0, 1.0), (-700, 0.85), (650, 1.1)):
            c = Client(build=False)
            c.env.GF_FIRST_SCENE = 'gf_scene_stageview'
            c.env.GF_FIRST_ARGS = c.rt.table_from({'stage': name, 'cx': cx, 'zoom': zoom})
            c.run(1.2)
            tiles.append(c.render(scale=0.5))
        sheet = Image.new('RGB', (800, 450 * 3))
        for i, t in enumerate(tiles):
            sheet.paste(t, (0, 450 * i))
        sheet.save(out / f'{name}.png')
        print(name, c.stats())


if __name__ == '__main__':
    from harness import bundle
    bundle.build()
    main()
