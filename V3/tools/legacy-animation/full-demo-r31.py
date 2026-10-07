from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source'];archive=(R/'project-inputs/archive-online/GFV2_Online_Fix_2f03d2e6b4e8.lua').read_text()
def module(text,name):
 a=text.index("__loaders['"+name+"'] = function()");b=text.find('__loaders[',a+10);return a,b if b>=0 else len(text)
for name in ['gf_online','gf_scene_online','gf_scene_select','gf_transport']:
 a,b=module(archive,name);body=archive[a:b]
 if "__loaders['"+name+"'] = function()" in s:
  a,b=module(s,name);s=s[:a]+body+s[b:]
 else:s=s.replace("__loaders['gf_ui'] = function()",body+"__loaders['gf_ui'] = function()",1)
for name in ['netOn','netPump']:
 key='function App:'+name+'()';a=archive.index(key);b=archive.index('\nfunction ',a+10);body=archive[a:b]
 a=s.index(key);b=s.index('\nfunction ',a+10);s=s[:a]+body+s[b:]
s=s.replace('netio = GF_NETIO or NETIO',"netio = GF_NETIO or require('gf_transport').new(game, script, function() return clock end)")
if "local SIGNAL = 'SQ_REC_STRIKE_V1'" in s:
 a=s.index("local SIGNAL = 'SQ_REC_STRIKE_V1'");b=s.index('local function start()',a);s=s[:a]+'local clock = 0\n\n'+s[b:]
 a=s.index('    for k = 1, 8 do\n        pcall(script.RegisterCustomVariableChangedHandler');b=s.index('    local ok, err = pcall(script.EnableUpdate',a);s=s[:a]+s[b:]
s=s.replace("GF_FIRST_SCENE='fight'","GF_FIRST_SCENE='intro'",1)
s=s.replace('local COLS = 8','local COLS = math.min(8,#Art.roster)')
s=s.replace('for i = 1, 6 do ladder[i] = pool[i] end','for i = 1, math.min(6,#pool) do ladder[i] = pool[i] end')
s=s.replace('连战七国强者，挑战最终头目','挑战已完成的角色').replace('七国之巅，已经登顶','角色挑战完成')
s=s.replace('(math.floor(o.io.now() * 1000) * 2654435761 + (o.nonce or 7)) & 0x7fffffff', 'math.floor((math.floor(o.io.now() * 1000) * 2654435761 + (o.nonce or 7)) % 2147483648)')
j['assets']['scripts'][0]['source']=s;j['meta']['name']='双角色完整 Demo · 开场、单人与联机 r31';p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
print('Full release intro/menu flow; archived GFV2 transport, selection and lobby restored')
