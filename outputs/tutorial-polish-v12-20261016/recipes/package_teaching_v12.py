"""Freeze confirmed-input/portrait/dash candidate plus retained rejected art research."""
from pathlib import Path
import hashlib,json,shutil,zipfile,sys
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-polish-v12-20261016'
def main():
 sha=hashlib.sha256((OUT/'genshin_fighter.lua').read_bytes()).hexdigest()
 for name,key in [('confirm-checks.json','clientSha256'),('portraits-dash-checks.json','clientSha256'),('complete-rules.json','clientSha256'),('flow-passed.json','sha256')]:assert json.loads((OUT/'verification'/name).read_text(encoding='utf-8'))[key]==sha,name
 assert json.loads((OUT/'logic.json').read_text(encoding='utf-8'))['clientSha256']==sha
 sys.path.insert(0,str(ROOT/'runtime/tools'));sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
 from compact_assets import LuaRuntime,python_table
 for key in ['lumine','lawachurl']:
  banks=[]
  for version in ['tutorial-polish-v11-20261016','tutorial-polish-v12-20261016']:
   rt=LuaRuntime();rt.execute('__loaders={};'+(ROOT/f'outputs/{version}/source/teaching/gf_{key}_training_data.lua').read_text(encoding='utf-8'));banks.append(python_table(rt.globals().__loaders[f'gf_{key}_training_data']()))
  for field in ['frames','groups','aliases','bodyPeak']:assert banks[0][field]==banks[1][field],(key,field)
 for a,b in [('tutorial-standard-icons-20261016','standard-icons'),('lumine-walk-research-20261016','walking-research'),('lumine-walk-four-20261016','rejected-walk-art')]:shutil.copytree(ROOT/'outputs'/a,OUT/b,dirs_exist_ok=True)
 shutil.copy2(ROOT/'outputs/tutorial-complete-v9-20261015/rebuild_snapshot.py',OUT/'rebuild_snapshot.py')
 shutil.copy2(ROOT/'docs/current/派蒙手动确认标准头像与前冲_20261016.md',OUT/'交付说明.md')
 recipes=OUT/'recipes';recipes.mkdir(exist_ok=True)
 for name in ['build_lumine_training.py','merge_tutorial_v15.py','import_teaching_standard_icons.py','preview_tutorial_v15.py','package_teaching_v12.py']:shutil.copy2(ROOT/'runtime/tools'/name,recipes/name)
 for name in ['teaching_confirm.py','teaching_portraits_dash.py','teaching_complete.py','teaching_complete_rules.lua','tutorial_v15_merge.py']:shutil.copy2(ROOT/'runtime/tests'/name,recipes/name)
 (OUT/'verification/body-preservation.json').write_text(json.dumps({'clientSha256':sha,'bodyBanksMatchV11Exactly':True,'newWalkRejected':True},indent=2),encoding='utf-8')
 manifest={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in OUT.rglob('*')if p.is_file()and p.name!='package-manifest.json'}
 (OUT/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
 target=OUT.with_suffix('.zip')
 with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED)as z:
  for p in OUT.rglob('*'):
   if p.is_file():z.write(p,OUT.name+'/'+p.relative_to(OUT).as_posix())
 with zipfile.ZipFile(target)as z:
  assert z.testzip()is None
  for name,h in manifest.items():assert hashlib.sha256(z.read(OUT.name+'/'+name)).hexdigest()==h
 print(json.dumps({'sha256':sha,'zip':target.relative_to(ROOT).as_posix(),'bytes':target.stat().st_size,'files':len(manifest)+1,'verified':True}))
if __name__=='__main__':main()
