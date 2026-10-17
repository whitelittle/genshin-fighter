from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parents[1];O=R/'outputs/pc-attack-budget-20261014'
final=(O/'shared-budget/genshin_fighter.lua').read_text(encoding='utf8');baseline=(R/'outputs/body-scale-fix-20261013/release/genshin_fighter.lua').read_text(encoding='utf8')
s=final
for rel in ['render/gf_gfx.lua','battle/gf_scene_fight.lua']:
 current=(R/'runtime/source'/rel).read_text(encoding='utf8');old=(O/'history'/Path(rel).name).read_text(encoding='utf8');assert current in s;s=s.replace(current,old,1)
name='gf_character_effect_channel'
pat=r"__loaders\['"+name+r"'\]=function\(\).*?(?=__loaders\[)"
old=re.search(pat,baseline,re.S).group();s,n=re.subn(pat,lambda m:old,s,flags=re.S);assert n==1
p=O/'flash-only/genshin_fighter.lua';p.write_text(s,encoding='utf8');m=json.loads((O/'shared-budget/build.json').read_text());m.update(bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),variant='flash-only',sharedBudget=False);(p.parent/'build.json').write_text(json.dumps(m,indent=2),encoding='utf8')
print('A flash-only',m['sha256'])
