from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'dist/projects/raiden-nahida.json'
project = json.loads(path.read_text())
source = project['assets']['scripts'][0]['source']
if 'GF_RELEASE_ID' not in source:
    source = "GF_RELEASE_ID='dual-round-fix-r18'\n" + source
    source = source.replace("local img=bank and bank[pose]", """local aliases={idle='basic_0',walk1='basic_2',walk2='basic_4',jump='move_1',crouch='guard_1',crouchGuard='guard_7',guard='guard_6',slash='light_2',special='skill_2',qRelease=key=='raidenshogun' and 'qburst_3' or 'skill_6',hurt='hurt_0',down='hurt_3'}
    local img=bank and bank[aliases[pose] or pose]""")
    source = source.replace("function A.portrait(key) return picture(key, 'portrait') end", "function A.portrait(key) return picture(key, 'portrait') end")
    source = source.replace('function A.prepare(key, tier)', """function A.prepare(key, tier)
    if A.animation(key,tier,'basic_0') then return {step=function() return true end} end""")
    source = source.replace("self.banners[#self.banners + 1] = {text = text", """-- Round / fight / KO / victory share one announcement slot.
    -- Replace immediately: animation age is render-frame based, simulation advances independently.
    self.annL:clear()
    self.banners = {}
    self.banners[1] = {text = text""")
    source = source.replace("function S:announceRound(n)\n", """function S:announceRound(n)
    self.smalls=nil;self.cine=nil;self.cut.L:clear();self.cut.bmp.node:on(false)
""")
    start = source.index('            -- afterimage then the text itself')
    end = source.index('            local n = L:label(b.text', start)
    source = source[:start] + '            -- One title glyph layer; no text afterimage.\n' + source[end:]
    source = source.replace('function S:roundEndFx(e)\n', 'function S:roundEndFx(e)\n    self.smalls=nil\n')
source=source.replace("GF_RELEASE_ID='dual-round-fix-r18'", "GF_RELEASE_ID='dual-ai-demo-r19'")
source=source.replace("mode='versus',cpu={false,2}", "mode='demo',cpu={2,2}")
project['meta']['name'] = '雷电与纳西妲 · 双AI演示 r19' 
project['assets']['scripts'][0]['source'] = source
path.write_text(json.dumps(project,ensure_ascii=False,separators=(',',':')))
(ROOT/'project-inputs/dual-character.lua').write_text(source)
print('Prepared r18: one announcement, original heads and dual AI demonstration')
