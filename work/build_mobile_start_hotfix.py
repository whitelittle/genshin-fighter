from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/mobile-start-hotfix-20261014'
for variant,base in [('stable','outputs/body-scale-fix-20261013/release'),('pc-budget','outputs/pc-attack-budget-20261014/shared-budget')]:
 B=R/base;before=(B/'genshin_fighter.lua').read_bytes();s=before;changes=[]
 for rel in ['input/gf_input.lua','menu/gf_scene_title.lua']:
  old=(O/'history'/Path(rel).name).read_bytes();new=(R/'runtime/source'/rel).read_bytes();assert s.count(old)==1,(variant,rel)
  s=s.replace(old,new,1);changes.append({'module':rel,'oldSha256':hashlib.sha256(old).hexdigest(),'newSha256':hashlib.sha256(new).hexdigest()})
 back=s
 for rel in ['input/gf_input.lua','menu/gf_scene_title.lua']:
  old=(O/'history'/Path(rel).name).read_bytes();new=(R/'runtime/source'/rel).read_bytes();back=back.replace(new,old,1)
 assert back==before
 out=O/variant;out.mkdir(parents=True,exist_ok=True);(out/'genshin_fighter.lua').write_bytes(s)
 m=json.loads((B/'build.json').read_text(encoding='utf8'));m.update(variant=variant,bytes=len(s),sha256=hashlib.sha256(s).hexdigest(),baseSha256=hashlib.sha256(before).hexdigest(),changedModules=changes,reverseBaseByteIdentical=True,nativeDeviceTested=False)
 (out/'build.json').write_text(json.dumps(m,indent=2),encoding='utf8');print(variant,m['sha256'])
