"""Build the generated art modules of the v2 game from the roster pose PNGs.

  python -X utf8 game/tools/build_art.py            (all characters in roster.json)
  python -X utf8 game/tools/build_art.py --only furina --preview

For every character in game/tools/roster.json:
  * two quality tiers of the 12 poses (hi for PC / strong phones, lo for weak phones); each
    pose picks the largest resolution whose rectangle count fits the tier cap,
  * one palette per character and tier (OKLab k-means), shared layer order across poses,
  * a coarse one-colour silhouette per pose (afterimages, hit flash),
  * a select-screen face icon and a VS-screen portrait from the official head picture.
Writes game/lua/gen/gf_art_<key>.lua, game/lua/gen/gf_roster.lua and game/build/art-report.json;
--preview also writes contact sheets to game/build/art-preview/.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
HERE = Path(__file__).resolve().parent
GAME = HERE.parent
REPO = GAME.parent
sys.path.insert(0, str(HERE))
import artlib as A  # noqa: E402

POSES = ['idle', 'walk1', 'walk2', 'jump', 'crouch', 'crouchGuard', 'guard',
         'slash', 'special', 'qRelease', 'hurt', 'down']
# world units per source pixel = frames.json scale x WORLD_GAIN (adult idle ~ 108 px -> ~335 units
# on the 1600x900 design canvas, about 37 % of the screen height)
WORLD_GAIN = 1.45
TIERS = {
    'hi': {'scales': [0.82, 0.75, 0.68, 0.62, 0.56, 0.5], 'cap': 1250, 'colours': 24},
    'lo': {'scales': [0.62, 0.56, 0.5, 0.45, 0.4], 'cap': 760, 'colours': 18},
}
SIL_CELL = 1          # silhouette cell in lo-tier pixels (exact outline, ~75-125 rects)
FACE = {'size': 34, 'colours': 16, 'crop': (34, 6, 222, 194)}     # select-screen icon
PORTRAIT = {'size': 64, 'colours': 20}                          # VS screen


def lua_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n') + "'"


def palette_bytes(pal):
    return A.b64(bytes(v for c in pal for v in c[:3]))


def layer_order(idxs, ncol):
    total = np.zeros(ncol, dtype=np.int64)
    for idx in idxs:
        c, n = np.unique(idx[idx >= 0], return_counts=True)
        total[c] += n
    return [int(i) for i in np.argsort(-total, kind='stable')]


def build_tier(src, frames, tier):
    """src: pose -> RGBA image (source resolution). Returns (palette, poses dict, preview)."""
    spec = TIERS[tier]
    base = spec['scales'][0]
    pal = A.build_palette([A.downscale(src[p], base) for p in POSES], spec['colours'])
    out, idx_by_pose = {}, {}
    for p in POSES:
        fr = frames[p]
        chosen = None
        for s in spec['scales']:
            im = A.downscale(src[p], s)
            idx = A.despeckle(A.apply_palette(im, pal))
            chosen = (s, im, idx)
            n_est = len(A.painter(idx))
            if n_est <= spec['cap']:
                break
        s, im, idx = chosen
        idx_by_pose[p] = (s, idx, fr)
    order = layer_order([v[1] for v in idx_by_pose.values()], len(pal))
    for p, (s, idx, fr) in idx_by_pose.items():
        rects = A.painter(idx, order)
        ax, ay = fr['anchor']
        out[p] = {
            'w': idx.shape[1], 'h': idx.shape[0],
            'ax': round(ax * s, 2), 'ay': round((ay + 1) * s, 2),     # anchor = bottom centre of the feet
            'u': round(fr['scale'] * WORLD_GAIN / s, 4),
            'n': len(rects), 'd': A.b64(A.pack_rects(rects)), 'rects': rects, 'scale': s,
        }
    return pal, out


def silhouettes(lo):
    sil = {}
    for p, v in lo.items():
        H, W = v['h'], v['w']
        idx = np.full((H, W), -1, dtype=np.int32)
        for x, y, w, h, c in v['rects']:
            idx[y:y + h, x:x + w] = 0
        rects = A.silhouette(idx, SIL_CELL)
        sil[p] = {'n': len(rects), 'd': A.b64(A.pack_rects(rects))}
    return sil


def picture(path, size, colours, crop=None, circle=False):
    im = A.load_rgba(path)
    if crop:
        im = im.crop(crop)
    sm = im.resize((size, size), Image.LANCZOS)
    a = np.asarray(sm).copy()
    a[..., 3] = np.where(a[..., 3] >= 100, 255, 0)
    if circle:
        # round icon: fill the transparent background with the dominant dark colour, cut a circle
        yy, xx = np.mgrid[0:size, 0:size]
        r = size / 2
        inside = (xx + 0.5 - r) ** 2 + (yy + 0.5 - r) ** 2 <= (r - 0.2) ** 2
        bgfill = (a[..., 3] == 0) & inside
        a[bgfill, :3] = (22, 24, 40)
        a[bgfill, 3] = 255
        a[~inside, 3] = 0
    sm = Image.fromarray(a)
    pal = A.build_palette([sm], colours)
    idx = A.despeckle(A.apply_palette(sm, pal))
    rects = A.painter(idx)
    return pal, rects


def skill_names(src_dir, key):
    p = src_dir / f'{key}-talents.json'
    d = json.loads(p.read_text(encoding='utf-8'))
    return d['name'], d['combat1']['name'], d['combat2']['name'], d['combat3']['name']


def build_char(src_dir, entry, preview_dir=None):
    key = entry['key']
    frames = {f['pose']: f for f in json.loads((src_dir / f'{key}-frames.json').read_text(encoding='utf-8'))['frames']}
    src = {p: A.load_rgba(src_dir / f'{key}-{p}.png') for p in POSES}
    tiers = {}
    for t in TIERS:
        tiers[t] = build_tier(src, frames, t)
    sil = silhouettes(tiers['lo'][1])
    fpal, frects = picture(src_dir / f'{key}-official-head.png', FACE['size'], FACE['colours'], FACE['crop'])
    cpal, crects = picture(src_dir / f'{key}-official-head.png', FACE['size'], FACE['colours'], FACE['crop'], circle=True)
    ppal, prects = picture(src_dir / f'{key}-official-head.png', PORTRAIT['size'], PORTRAIT['colours'])
    name, na, e, q = skill_names(src_dir, key)

    lines = [f'-- generated by game/tools/build_art.py from {src_dir.relative_to(REPO).as_posix()}/{key}-*.png; do not edit',
             'return {', f'key={lua_str(key)},']
    for t, (pal, poses) in tiers.items():
        lines.append(f'{t}={{pal={lua_str(palette_bytes(pal))},')
        for p in POSES:
            v = poses[p]
            lines.append(f"{p}={{w={v['w']},h={v['h']},ax={v['ax']},ay={v['ay']},u={v['u']},n={v['n']},d={lua_str(v['d'])}}},")
        lines.append('},')
    lines.append('sil={' + ','.join(f"{p}={{n={v['n']},d={lua_str(v['d'])}}}" for p, v in sil.items()) + '},')
    lines.append(f"face={{s={FACE['size']},pal={lua_str(palette_bytes(fpal))},n={len(frects)},d={lua_str(A.b64(A.pack_rects(frects)))}}},")
    lines.append(f"round={{s={FACE['size']},pal={lua_str(palette_bytes(cpal))},n={len(crects)},d={lua_str(A.b64(A.pack_rects(crects)))}}},")
    lines.append(f"portrait={{s={PORTRAIT['size']},pal={lua_str(palette_bytes(ppal))},n={len(prects)},d={lua_str(A.b64(A.pack_rects(prects)))}}},")
    lines.append('}')
    text = '\n'.join(lines) + '\n'

    report = {
        'key': key, 'name': name,
        'tiers': {t: {p: {'n': v['n'], 'scale': v['scale'], 'u': v['u']} for p, v in poses.items()} for t, (pal, poses) in tiers.items()},
        'palette': {t: len(pal) for t, (pal, _) in tiers.items()},
        'sil': {p: v['n'] for p, v in sil.items()}, 'face': len(frects), 'portrait': len(prects),
        'bytes': len(text.encode('utf-8')),
    }
    meta = {'key': key, 'name': name, 'element': entry['element'], 'weapon': entry['weapon'],
            'attack': na, 'skill': e, 'burst': q, 'h': frames['idle']['h'] * frames['idle']['scale'] * WORLD_GAIN}

    if preview_dir:
        preview_dir.mkdir(parents=True, exist_ok=True)
        H = 220
        cells = []
        for t, (pal, poses) in tiers.items():
            for p in POSES:
                v = poses[p]
                im = A.render(v['rects'], pal, v['w'], v['h'])
                k = H / 120 * (v['u'] / poses['idle']['u'] if False else 1)
                hh = max(1, round(v['h'] * v['u'] / 3.2))
                ww = max(1, round(v['w'] * v['u'] / 3.2))
                cells.append(im.resize((ww, hh), Image.NEAREST))
        fim = A.render(frects, fpal, FACE['size'], FACE['size']).resize((136, 136), Image.NEAREST)
        pim = A.render(prects, ppal, PORTRAIT['size'], PORTRAIT['size']).resize((192, 192), Image.NEAREST)
        per = len(POSES)
        cw = max(c.width for c in cells) + 8
        ch = max(c.height for c in cells) + 8
        sheet = Image.new('RGBA', (cw * per, ch * 2 + 200), (26, 30, 46, 255))
        for i, c in enumerate(cells):
            sheet.alpha_composite(c, ((i % per) * cw, (i // per) * ch + (ch - c.height)))
        sheet.alpha_composite(fim, (0, ch * 2 + 4))
        sheet.alpha_composite(pim, (150, ch * 2 + 4))
        sheet.save(preview_dir / f'{key}.png')
    return text, report, meta


def write_roster(metas, out):
    lines = ['-- generated by game/tools/build_art.py from game/tools/roster.json; do not edit', 'return {']
    for m in metas:
        lines.append('{' + ','.join([
            f"key={lua_str(m['key'])}", f"name={lua_str(m['name'])}", f"element={lua_str(m['element'])}",
            f"weapon={lua_str(m['weapon'])}", f"attack={lua_str(m['attack'])}", f"skill={lua_str(m['skill'])}",
            f"burst={lua_str(m['burst'])}", f"h={round(m['h'])}"]) + '},')
    lines.append('}')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--preview', action='store_true')
    args = ap.parse_args()
    cfg = json.loads((HERE / 'roster.json').read_text(encoding='utf-8'))
    src_dir = REPO / cfg['source']
    gen = GAME / 'lua' / 'gen'
    gen.mkdir(parents=True, exist_ok=True)
    build = GAME / 'build'
    build.mkdir(exist_ok=True)
    rep_path = build / 'art-report.json'
    reports = json.loads(rep_path.read_text(encoding='utf-8')) if rep_path.exists() else {}
    metas = []
    for entry in cfg['chars']:
        key = entry['key']
        if args.only and key not in args.only:
            name, na, e, q = skill_names(src_dir, key)
            frames = {f['pose']: f for f in json.loads((src_dir / f'{key}-frames.json').read_text(encoding='utf-8'))['frames']}
            metas.append({'key': key, 'name': name, 'element': entry['element'], 'weapon': entry['weapon'],
                          'attack': na, 'skill': e, 'burst': q, 'h': frames['idle']['h'] * frames['idle']['scale'] * WORLD_GAIN})
            continue
        text, report, meta = build_char(src_dir, entry, build / 'art-preview' if args.preview else None)
        (gen / f'gf_art_{key}.lua').write_text(text, encoding='utf-8')
        reports[key] = report
        metas.append(meta)
        hi = report['tiers']['hi']
        lo = report['tiers']['lo']
        print(f"{key:15s} hi max {max(v['n'] for v in hi.values()):5d} sum {sum(v['n'] for v in hi.values()):6d} | "
              f"lo max {max(v['n'] for v in lo.values()):4d} | face {report['face']} portrait {report['portrait']} | {report['bytes'] // 1024} KB")
    write_roster(metas, gen / 'gf_roster.lua')
    rep_path.write_text(json.dumps(reports, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
