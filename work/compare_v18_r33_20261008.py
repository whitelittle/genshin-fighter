"""Static comparison of supplied V18 and r33, without executing either client."""
from pathlib import Path
import re, hashlib, json, difflib

BASE=Path(__file__).resolve().parent/'package-review-20261008'
source=Path.home()/'Desktop'/'GF_Online_Repair_3e508011db14 (1).lua'
src=source.read_text(encoding='utf-8-sig')
out=BASE/'V18'
out.mkdir(parents=True,exist_ok=True)
marks=list(re.finditer(r"^__loaders\['(gf_\w+)'\] = function\(\)",src,re.M))
modules={}
for i,m in enumerate(marks):
    end=marks[i+1].start() if i+1<len(marks) else len(src)
    modules[m[1]]=src[m.start():end]
    (out/(m[1]+'.lua')).write_text(modules[m[1]],encoding='utf-8')
r33=BASE/'GF_FORMAL_r33/modules/genshin_fighter'
report={'v18_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'v18_bytes':source.stat().st_size,'modules':{}}
for name in ['gf_net','gf_online','gf_transport','gf_app','gf_gfx','gf_art','gf_fview','gf_scene_fight','gf_sim','gf_stage']:
    a=modules[name]
    b=(r33/(name+'.lua')).read_text(encoding='utf-8')
    diff=''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='V18/'+name,tofile='r33/'+name))
    (out/(name+'.diff')).write_text(diff,encoding='utf-8')
    report['modules'][name]={'identical':a==b,'diff_lines':len(diff.splitlines())}
(out/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
