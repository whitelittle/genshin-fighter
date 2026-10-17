"""Read user-supplied archives into an isolated comparison directory; never execute payloads."""
from pathlib import Path
import zipfile, struct, zlib, hashlib, json, re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'work' / 'package-review-20261008'
NAMES = ['GF_V2_20261007_0333.zip', 'GF_V2_20261007_0324.zip', 'GF_FORMAL_r33.zip', 'dual-character-r31.zip', 'GF_Online_BackgroundPool_20261007.zip', 'GF_Text_Fix_1073742224_20261007.zip', 'GF_UI_Visibility_Probe_20261007.zip']

def entries(path):
    try:
        with zipfile.ZipFile(path) as z:
            return [(i.filename, z.read(i), 'zip-crc-verified') for i in z.infolist() if not i.is_dir()]
    except zipfile.BadZipFile:
        raw = path.read_bytes()
        pos, result = 0, []
        while raw[pos:pos+4] == b'PK\x03\x04':
            _, version, flags, method, tm, date, crc, packed, size, nl, el = struct.unpack_from('<IHHHHHIIIHH', raw, pos)
            name = raw[pos+30:pos+30+nl].decode('utf-8' if flags & 2048 else 'cp437')
            start = pos + 30 + nl + el
            if flags & 8 or start + packed > len(raw):
                result.append((name, None, 'incomplete-or-descriptor'))
                break
            payload = raw[start:start+packed]
            try:
                data = zlib.decompress(payload, -15) if method == 8 else payload
            except zlib.error:
                result.append((name, None, 'damaged-compressed-stream'))
                pos = start + packed
                continue
            if len(data) != size or zlib.crc32(data) != crc:
                raise ValueError('CRC/size mismatch: ' + name)
            result.append((name, data, 'recovered-local-header-crc-verified'))
            pos = start + packed
        return result

manifest = []
for name in NAMES:
    for entry, data, status in entries(Path.home() / 'Downloads' / name):
        row = dict(package=name, entry=entry, status=status)
        if data is not None:
            row.update(size=len(data), sha256=hashlib.sha256(data).hexdigest())
            if entry.endswith(('.lua', '.md', '.json', '.txt')):
                target = (OUT / Path(name).stem / entry).resolve()
                if not target.is_relative_to(OUT.resolve()):
                    raise ValueError('unsafe entry')
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                if entry.endswith('.lua'):
                    src = data.decode('utf-8-sig')
                    # Bundled module boundaries are inspected separately before splitting.
                    row['header'] = src[:220]
                    boundaries = list(re.finditer(r"^__loaders\['(gf_\w+)'\] = function\(\)", src, re.M))
                    if boundaries and '/optional-modular/' not in '/' + entry:
                        dest = OUT / Path(name).stem / 'modules' / Path(entry).stem
                        dest.mkdir(parents=True, exist_ok=True)
                        for i, match in enumerate(boundaries):
                            end = boundaries[i+1].start() if i+1<len(boundaries) else len(src)
                            (dest / (match[1]+'.lua')).write_text(src[match.start():end], encoding='utf-8')
        manifest.append(row)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
for row in manifest:
    if row['package'].endswith('0333.zip') or row['entry'].endswith('.lua'):
        print(json.dumps(row, ensure_ascii=False))
