from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if "GF_RELEASE_ID='nahida-preview-pool-r23'" not in s:
 s=s.replace('select=9500, online=9500, vs=9500, fight=9500','select=14000, online=12000, vs=14000, fight=14000')
 s=s.replace('batch=32, limit=10000','batch=32, limit=18000')
 gfx=(R/'project-inputs/gf_gfx-r23.lua').read_text()
 a=s.index("__loaders['gf_gfx'] = function()");b=s.index("__loaders['",a+10);s=s[:a]+gfx+s[b:]
 s=s.replace("GF_RELEASE_ID='dual-scale-throw-r22'","GF_RELEASE_ID='nahida-preview-pool-r23'")
 j['meta']['name']='雷电与纳西妲 · 图元池修复 r23';j['assets']['scripts'][0]['source']=s
 p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
