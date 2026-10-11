"""Validate all volumes before restoring the Zhongli art candidate snapshot."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,zipfile

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--destination',type=Path,default=Path('outputs/zhongli-design-20261011'))
    args=parser.parse_args()
    base=Path(__file__).resolve().parent
    manifest=json.loads((base/'zhongli-git-manifest.json').read_text())
    volumes=manifest['volumes']
    for volume in volumes:
        file=base/volume['name']
        if not file.is_file():raise SystemExit('Missing volume: '+file.name)
        if file.stat().st_size!=volume['bytes'] or hashlib.sha256(file.read_bytes()).hexdigest()!=volume['sha256']:
            raise SystemExit('Volume validation failed: '+file.name)
    target=args.destination.resolve()
    if target.exists() and any(target.iterdir()):
        raise SystemExit('Destination is not empty; choose a new --destination to preserve existing work.')
    target.mkdir(parents=True,exist_ok=True)
    for volume in volumes[:-1]:
        with zipfile.ZipFile(base/volume['name']) as archive:
            assert archive.testzip() is None
            for name in archive.namelist():
                if not (target/name).resolve().is_relative_to(target):raise SystemExit('Unsafe archive member')
            archive.extractall(target)
    subprocess.run([sys.executable,str(target/'restore-duplicates.py')],check=True)
    with zipfile.ZipFile(base/volumes[-1]['name']) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            if not (target/name).resolve().is_relative_to(target):raise SystemExit('Unsafe patch member')
        archive.extractall(target)
    subprocess.run([sys.executable,str(target/'download-materials/scripts/repair_e_neutral_tail.py'),str(target/'full-actions')],check=True)
    print('Restored Zhongli snapshot:',target)
    print('Art candidates only; formal combat, browser, simulator and device acceptance pending.')

if __name__=='__main__':main()
