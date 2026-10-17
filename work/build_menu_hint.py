from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'outputs/menu-hint-20261014';base=R/'outputs/mobile-start-hotfix-20261014'
for variant in ['stable','pc-budget']:
 B=base/variant;before=(B/'genshin_fighter.lua').read_bytes();s=before;changes=[]
 for rel in ['menu/gf_scene_menu.lua','render/gf_hud.lua','input/gf_touch.lua','render/gf_ui.lua']:
  old=(O/'history'/Path(rel).name).read_bytes();new=(R/'runtime/source'/rel).read_bytes();assert s.count(old)==1,(variant,rel);s=s.replace(old,new,1);changes.append(rel)
 back=s
 for rel in changes:
  back=back.replace((R/'runtime/source'/rel).read_bytes(),(O/'history'/Path(rel).name).read_bytes(),1)
 assert back==before
 out=O/variant;out.mkdir(exist_ok=True);(out/'genshin_fighter.lua').write_bytes(s);m=json.loads((B/'build.json').read_text());m.update(sha256=hashlib.sha256(s).hexdigest(),bytes=len(s),baseSha256=hashlib.sha256(before).hexdigest(),changedModules=changes,reverseBaseByteIdentical=True);(out/'build.json').write_text(json.dumps(m,indent=2),encoding='utf8');print(variant,m['sha256'])
