from pathlib import Path
import json,re
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if 'local __externalRequire=require' in s:
 print('Art already split');raise SystemExit
(R/'project-inputs/dual-character-standalone.lua').write_text(s)
mods=list(re.finditer(r"__loaders\['([^']+)'\] = function\(\)",s));art={}
for i,m in enumerate(mods):
 n=m[1]
 if n.startswith(('gf_art_','gf_bg_')) or n in ['gf_animation_data','gf_animation_effects','gf_inbetween_data','gf_hd_r31','gf_aranara_data','gf_viewfinder_data','gf_raiden_eye_r31','gf_logo']:
  b=mods[i+1].start() if i+1<len(mods) else s.index('-- entry: gf_main');body=s[m.end():b].strip();assert body.endswith('end');art[n]=body[:-3].rstrip()
std='return {\n'+',\n'.join('["'+n+'"] = function()\n'+body+'\nend' for n,body in art.items() if n!='gf_hd_r31')+'\n}\n';hd=art['gf_hd_r31']+'\n'
for i in range(len(mods)-1,-1,-1):
 m=mods[i];n=m[1]
 if n not in art:continue
 b=mods[i+1].start() if i+1<len(mods) else s.index('-- entry: gf_main')
 call="__externalRequire('default_import_file/gf_art_hd.lua')" if n=='gf_hd_r31' else "__externalRequire('default_import_file/gf_art_sd.lua')['"+n+"']()"
 s=s[:m.start()]+"__loaders['"+n+"'] = function() return "+call+" end\n"+s[b:]
s=s.replace('local __loaders, __loaded = {}, {}','local __externalRequire=require\nlocal __loaders, __loaded = {}, {}',1)
j['assets']['scripts'][0]['source']=s
for guid,path,body in [(1078316001,'gf_art_sd.lua',std),(1078316002,'gf_art_hd.lua',hd)]:
 j['assets']['scripts'].append({'guid':guid,'path':path,'source':body});(R/'project-inputs'/path).write_text(body)
p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
print('Logic',len(s.encode()),'SD',len(std.encode()),'HD',len(hd.encode()))
