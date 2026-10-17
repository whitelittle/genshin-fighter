from pathlib import Path
import argparse,hashlib,json,zipfile
ap=argparse.ArgumentParser();ap.add_argument('--version',default='v1');version=ap.parse_args().version
root=Path(__file__).resolve().parent
files=[p for p in root.rglob('*') if p.is_file() and p.name!='package-manifest.json']
manifest={'version':'lumine-lawachurl-training-'+version,'status':'offline-tested-art-pending','files':{p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(root/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
archive=root.parent/('lumine-training-20261015-'+version+'.zip')
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for p in root.rglob('*'):
  if p.is_file():z.write(p,p.relative_to(root.parent))
 for path in ['runtime/tools/build_lumine_training.py','runtime/tools/preview_lumine_training.py','runtime/tests/lumine_training.py','runtime/tests/lumine_lesson.py','runtime/tests/lumine_courses.py','runtime/tests/lumine_notice.py','runtime/tests/lumine_release_flow.py','runtime/source/modes/gf_training_lesson.lua','runtime/source/modes/gf_training_courses.lua','runtime/source/menu/gf_scene_training_courses.lua','runtime/source/menu/gf_update_notice_data.lua','runtime/source/menu/gf_scene_update_notice.lua']:
  p=root.parents[1]/path;z.write(p,path)
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print('Package verified',archive.name,archive.stat().st_size)
