"""Restore the uploaded one-MiB shards using the original 20-MiB manifest."""
from pathlib import Path, PureWindowsPath
import hashlib
import json
import subprocess
import zipfile
import sys
import zlib

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / 'work/github-review-20261009'
REF = 'refs/remotes/origin/work/v4-handoff-20261009'
OUT = ROOT / 'work/v4-handoff-20261009'
ARCHIVE = ROOT / 'work/V4_HANDOFF_RESTORED_20261009.zip'
PARTIAL = '--partial' in sys.argv
if PARTIAL:
    OUT = ROOT / 'work/v4-handoff-20261009-partial'
    ARCHIVE = ROOT / 'work/V4_HANDOFF_PARTIAL_20261009.zip'

def blob(path):
    return subprocess.check_output(['git','show',f'{REF}:{path}'],cwd=REPO)

def main():
    resume = '--resume' in sys.argv and PARTIAL
    if OUT.exists() or (ARCHIVE.exists() and not resume):
        raise SystemExit('Refusing to overwrite an existing restored archive/directory')
    manifest=json.loads(blob('V4_HANDOFF_MANIFEST.json'))
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',REF],cwd=REPO).decode().splitlines()
    shards=sorted(n for n in names if n.startswith('V4_1M_') and n.endswith('.part'))
    expected=[f'V4_1M_{i:04d}.part' for i in range(1,656)]
    missing=sorted(set(expected)-set(shards))
    assert not (set(shards)-set(expected))
    if missing and not PARTIAL: raise SystemExit('Missing archive shards: '+', '.join(missing))
    if resume:
        assert ARCHIVE.stat().st_size == 654*1048576, 'unexpected partial archive size'
        with ARCHIVE.open('ab') as out: out.write(blob(expected[-1]))
    else:
      with ARCHIVE.open('xb') as out:
        for i,name in enumerate(expected,1):
            data=blob(name) if name not in missing else bytes(1048576)
            assert len(data)==1048576 or i==len(expected), name
            out.write(data)
            if i%100==0: print(f'Validated/written {i}/655 shards',flush=True)
    whole=hashlib.sha256();damaged_groups=[];offset=0
    with ARCHIVE.open('rb') as stream:
        for spec in manifest['parts']:
            data=stream.read(spec['bytes']);assert len(data)==spec['bytes']
            whole.update(data)
            holes=[(int(n[6:10])-1)*1048576 for n in missing]
            if any(offset<=h<offset+len(data) for h in holes): damaged_groups.append(spec['name'])
            else: assert hashlib.sha256(data).hexdigest()==spec['sha256'],spec['name']
            offset+=len(data)
        assert not stream.read(1)
    index=len(manifest['parts'])
    if not missing: assert whole.hexdigest()==manifest['archive_sha256']
    rejected=[]; recovered=0
    with zipfile.ZipFile(ARCHIVE) as z:
        for info in z.infolist():
            p=Path(info.filename)
            assert not p.is_absolute() and not PureWindowsPath(info.filename).is_absolute()
            assert '..' not in p.parts and ':' not in info.filename
            assert (OUT/p).resolve().is_relative_to(OUT.resolve()),info.filename
            assert (info.external_attr>>16)&0o170000 != 0o120000,'symlink in archive'
        for info in z.infolist():
            if info.is_dir(): continue
            try: data=z.read(info)
            except (zipfile.BadZipFile,zlib.error,EOFError) as e:
                rejected.append({'path':info.filename,'error':str(e)});continue
            path=OUT/info.filename
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data);recovered+=1
        count=len(z.infolist())
    (OUT/'LOCAL_RESTORE_VERIFICATION.json').write_text(json.dumps({
        'branch':REF,'commit':subprocess.check_output(['git','rev-parse',REF],cwd=REPO).decode().strip(),
        'one_mib_shards':len(shards),'original_groups_verified':index,
        'complete':not missing and not rejected,'missing_shards':missing,
        'original_groups_verified':index-len(damaged_groups),'damaged_groups':damaged_groups,
        'recovered_crc_checked_files':recovered,'unrecoverable_files':rejected,
        'archive_sha256':whole.hexdigest(),'zip_entries':count,
        'method':'Missing-shard holes preserve ZIP offsets in partial mode; only CRC-valid files extracted. Unaffected original groups SHA256 checked.'
    },indent=2),encoding='utf-8')
    print(f'Restored {recovered} CRC-checked files; rejected {len(rejected)}; missing shards {missing}',flush=True)

if __name__=='__main__': main()
