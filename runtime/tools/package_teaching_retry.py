"""Save the two local teaching polish changes and the unchanged mother reference."""
from pathlib import Path
import hashlib,json,shutil,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v11-20261016';ART=ROOT/'outputs/lumine-walk-fix-20261016'
def main():
 digest=hashlib.sha256((OUT/'genshin_fighter.lua').read_bytes()).hexdigest()
 for name,key in [('dialogue-checks.json','clientSha256'),('retry-checks.json','clientSha256'),('complete-rules.json','clientSha256'),('attack-checks.json','sha256'),('guard-checks.json','sha256'),('tutorial-passed.json','sha256'),('flow-passed.json','sha256')]+[(p.name,'clientSha256')for p in (OUT/'verification').glob('complete-native-*.json')]:assert json.loads((OUT/'verification'/name).read_text(encoding='utf-8'))[key]==digest,name
 assert json.loads((OUT/'logic.json').read_text(encoding='utf-8'))['clientSha256']==digest
 shutil.copytree(ART,OUT/'walking-art',dirs_exist_ok=True)
 shutil.copytree(ROOT/'outputs/tutorial-complete-art-20261015',OUT/'previous-teaching-art',dirs_exist_ok=True)
 shutil.copy2(ROOT/'outputs/tutorial-complete-v9-20261015/rebuild_snapshot.py',OUT/'rebuild_snapshot.py')
 shutil.copy2(ROOT/'docs/current/教学重试提示与退出清理_20261016.md',OUT/'交付说明.md')
 recipes=OUT/'recipes';recipes.mkdir(exist_ok=True)
 for name in ['build_lumine_training.py','merge_tutorial_v15.py','import_lumine_walk_fix.py','package_teaching_retry.py','preview_tutorial_v15.py']:shutil.copy2(ROOT/'runtime/tools'/name,recipes/name)
 for name in ['teaching_retry.py','teaching_dialogue.py','teaching_complete.py','teaching_complete_rules.lua','teaching_complete_native.py','tutorial_v15_merge.py','lumine_guard.py','lumine_attack.py']:shutil.copy2(ROOT/'runtime/tests'/name,recipes/name)
 manifest={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in OUT.rglob('*')if p.is_file()and p.name!='package-manifest.json'}
 (OUT/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 target=ROOT/'outputs/tutorial-polish-v11-20261016.zip'
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED)as z:
  for p in OUT.rglob('*'):
   if p.is_file():z.write(p,OUT.name+'/'+p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(target)as z:
  assert z.testzip()is None
  for name,sha in manifest.items():assert hashlib.sha256(z.read(OUT.name+'/'+name)).hexdigest()==sha,name
 print(json.dumps({'zip':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'files':len(manifest)+1,'sha256':digest,'verified':True}))
if __name__=='__main__':main()
