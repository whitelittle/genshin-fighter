"""One-time mechanical V3 source migration. Refuse to overwrite a maintained tree."""
from pathlib import Path
import json, re, hashlib

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'work/github-review-20261009/V3'
OUT = ROOT / 'runtime'

def domain(name):
    if name.startswith(('gf_art_', 'gf_bg_')) or name.endswith('_data') or name in ['gf_animation_effects','gf_logo','gf_raiden_eye_r31']:
        return 'assets'
    if name.startswith('gf_scene_'):
        return 'battle' if name == 'gf_scene_fight' else 'menu'
    return {'gf_app':'app','gf_roster':'characters','gf_art':'characters','gf_kits':'characters',
            'gf_sim':'battle','gf_ai':'battle','gf_net':'network','gf_online':'network','gf_transport':'network',
            'gf_input':'input','gf_touch':'input','gf_util':'core'}.get(name,'render')

def write(path, code):
    p=OUT/path; p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(code,encoding='utf-8',newline='\n')

def main():
    assert not OUT.exists(), 'runtime already exists; edit maintained source, do not reimport'
    old=json.loads((BASE/'source/order.json').read_text())
    order=[];origin=[]
    for entry in old:
        p=Path(entry); name=p.stem
        dest=f'source/{domain(name)}/{p.name}' if p.parent.name=='modules' else entry
        code=(BASE/p).read_text(encoding='utf-8')
        if name=='gf_app':
            installs=[]
            for module,start,end in [
                ('gf_app_network','function App:netOn()', 'function App:switch('),
                ('gf_app_transition','function App:travel(', 'function App:backdrop('),
                ('gf_app_metrics','function App:samplePerformance(', '-- Cover the previous scene'),
                ('gf_app_loading','function App:drawScenePool(', 'return App')]:
                # Extracted functions have the same App receiver; only their ownership moves.
                a=code.index(start);b=code.index(end,a);body=code[a:b];code=code[:a]+code[b:]
                path=f'source/app/{module}.lua'
                write(path,f"__loaders['{module}']=function()\nlocal G=require('gf_gfx')\nreturn function(App)\n{body}\nend\nend\n")
                order.append(path)
                installs.append(f"require('{module}')(App)")
            code=code.replace('return App','\n'.join(installs)+'\nreturn App')
        if name=='gf_scene_fight':
            header=code[code.index("local G ="):code.index('local S =')]
            blocks=[('gf_battle_loading','function S:loadTick()', '-- phones'),
                    ('gf_battle_input','function S:touchControls()', 'function S:curtainDraw('),
                    ('gf_battle_events','local REACT_COL', 'function S:camera('),
                    ('gf_battle_pause','function S:openPause()', 'function S:tick()'),
                    ('gf_battle_network','function S:netTick(', 'function S:finish()'),
                    ('gf_battle_backdrop','local burstEyeData', 'function S:draw()')]
            for module,start,end in blocks:
                a=code.index(start);b=code.index(end,a);body=code[a:b];code=code[:a]+code[b:]
                path=f'source/battle/{module}.lua'
                write(path,f"__loaders['{module}']=function()\n{header}\nlocal C=Sim.C\nreturn function(S)\n{body}\nend\nend\n")
                order.append(path)
                code=code.replace('return S',f"require('{module}')(S)\nreturn S")
        if name=='gf_sim':
            installs=[]
            for module,start,end,params,header in [
                ('gf_sim_physics','function S:physics(', 'function S:fighterTick(', 'C, GRAV, WALL', ''),
                ('gf_sim_flow','function S:roundOver(', '------------------------------------------------------------------ main tick','C',''),
                ('gf_sim_snapshot','local function copyList(', 'S.C = C','HIST','')]:
                a=code.index(start);b=code.index(end,a);body=code[a:b];code=code[:a]+code[b:]
                path=f'source/battle/{module}.lua'
                write(path,f"__loaders['{module}']=function()\nlocal floor,abs,max,min=math.floor,math.abs,math.max,math.min\nreturn function(S,{params})\n{body}\nend\nend\n")
                order.append(path)
                installs.append(f"require('{module}')(S,{params})")
            code=code.replace('S.C = C','\n'.join(installs)+'\nS.C = C')
        write(dest,code);order.append(dest)
        origin.append({'module':name,'source':entry,'target':dest,'sha256':hashlib.sha256((BASE/p).read_bytes()).hexdigest()})
    write('source/order.json',json.dumps(order,indent=2))
    write('migration.json',json.dumps({'baseline':'V3 accepted E','modules':origin},indent=2))
    for name in ['checks-d.lua','checks-e.lua']:
        write('tests/'+name,(BASE/'tests'/name).read_text(encoding='utf-8'))
    print('Created maintained runtime tree with',len(order),'chunks')

if __name__=='__main__': main()
