from pathlib import Path
p=Path('runtime/source/battle/gf_battle_events.lua');t=p.read_text(encoding='utf-8').replace("p.key~='nahida' and p.key~='furina'","p.key~='nahida' and p.key~='furina' and p.key~='kamisatoayaka'").replace('au.ID.ecircle.hydro','au.ID.ecircle[sim.f[e.p].element]');p.write_text(t,encoding='utf-8')
p=Path('runtime/tests/mock_flow.py');t=p.read_text(encoding='utf-8').replace('def local_flow(device,canvas):','def local_flow(device,canvas,chars=(3,1)):\n    a,b=chars')
t=t.replace('    c.lua("(function()GF_APP():go(\'select\',{mode=\'versus\',cpu=true});return true end)()")', '''    wait(c,"GF_APP().sceneName=='title' and GF_APP().scene.t>.8 and not GF_APP().trans")
    c.render(ROOT/f'verification/title-{device}.png')
    c.touch('down',canvas[0]/2,canvas[1]/2);c.step();c.touch('up',canvas[0]/2,canvas[1]/2)
    wait(c,"GF_APP().sceneName=='menu' and not GF_APP().trans")
    c.lua("(function()GF_APP().scene:pick('versus');return true end)()")
    c.lua("(function()GF_APP().scene.menu.o.onPick('vcpu');return true end)()")''')
t=t.replace('s.cur={3,1}', 's.cur={{{a},{b}}}').replace('c.lua("(function()local s=GF_APP().scene;s.cur=', 'c.lua(f"(function()local s=GF_APP().scene;s.cur=')
# f-string braces only for this line
lines=t.splitlines();lines=[l.replace('(function()local s=GF_APP().scene;s.cur=', '(function()local s=GF_APP().scene;s.cur=') if 's.cur=' not in l else l.replace('return true end)()', 'return true end)()') for l in lines];t='\n'.join(lines)+'\n'
t=t.replace('assert c.lua("GF_APP().scene.sim.f[1].key==\'furina\'")', 'assert c.lua(f"GF_APP().scene.sim.f[1].key==GF_REQUIRE(\'gf_roster\')[{a}].key")')
t=t.replace('def network_flow():','def network_flow(chars=(3,1)):\n    a,b=chars').replace('{3 if i==0 else 1}', '{a if i==0 else b}')
t=t.replace('for c in clients:assert c.lua("GF_APP().scene.args.chars[1]==\'furina\' and GF_APP().scene.args.chars[2]==\'raidenshogun\'")', 'for c in clients:assert c.lua(f"GF_APP().scene.args.chars[1]==GF_REQUIRE(\'gf_roster\')[{a}].key and GF_APP().scene.args.chars[2]==GF_REQUIRE(\'gf_roster\')[{b}].key")')
t=t.replace("'furinaOnlinePair':True", "'characters':chars").replace("'selectFightPauseResultRematchReselect':True", "'titleMenuSelectFightPauseResultRematchReselect':True,'characters':chars")
t=t.replace("('Mobile',(900,1600))", "('Mobile',(900,1600)),('Mobile',(1600,900))")
t=t.replace('result=local_flow(device,canvas)', 'result=local_flow(device,canvas,(4,3))').replace('net=network_flow()', 'net=network_flow((4,3))')
p.write_text(t,encoding='utf-8')
