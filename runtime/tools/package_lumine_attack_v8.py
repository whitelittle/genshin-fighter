"""Save the generated candidate art and independently rebuildable local tutorial."""
from pathlib import Path
import json, hashlib, shutil, zipfile
ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'outputs/lumine-attacks-20261015'
OUT=ROOT/'outputs/tutorial-attack-v8-20261015'
meta=json.loads((ART/'import.json').read_text(encoding='utf-8'))
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>荧攻击动画候选 v1</title>
<style>body{background:#151c30;color:#eee;font:17px system-ui;max-width:1000px;margin:30px auto;padding:16px}button,select{font:inherit;padding:8px;margin:5px}canvas{width:100%;background:#26304a;image-rendering:pixelated}img{max-width:100%;background:repeating-conic-gradient(#30384b 0% 25%,#424c63 0% 50%) 0/24px 24px}a{color:#b8d7ff}</style>
<h1>荧 · 新攻击动画候选 v1</h1><p>内置生图生成。每组四姿：前摇、出手、收招前半、收招后半。尚待美术验收，可后续逐帧修改。</p>
<select id="move"><option value="light2">轻击第二段 · 上挑斩</option><option value="light3">轻击第三段 · 直刺</option><option value="heavy">重击 · 下斩</option></select>
<button id="play">暂停</button><button id="prev">上一帧</button><button id="next">下一帧</button><p id="info"></p><canvas id="stage" width="1000" height="520"></canvas>
<p>全部48张身体帧均值998.48图元，峰值1174；不是整场总图元或真机帧率。旧36帧保留，新12帧使用14色拟合。</p>
<p><a href="prompts.json">原始提示词</a> · <a href="import.json">切帧、锚点、图元与来源记录</a></p><h2>生成原图</h2><img id="sheet">
<script>const meta=__META__;const names=['前摇','出手','收招前半','收招后半'];let frame=0,ticks=0,playing=true;const images={};for(const name of Object.keys(meta.newFrames)){let im=new Image;im.src='fit/'+name+'.png';im.onload=draw;images[name]=im;}
function draw(){let key=move.value+'_'+frame,m=meta.newFrames[key],im=images[key],c=stage.getContext('2d');c.clearRect(0,0,1000,520);c.strokeStyle='#506486';c.beginPath();c.moveTo(0,465);c.lineTo(1000,465);c.stroke();c.imageSmoothingEnabled=false;if(im&&im.complete)c.drawImage(im,520-m.anchor[0]*4,465-m.anchor[1]*4,m.w*4,m.h*4);info.textContent=(frame+1)+'/4 · '+names[frame]+' · '+meta.groups[move.value][frame]+'拍 / 60Hz · '+m.n+'图元';sheet.src='source/'+move.value+'-v1.png';}
move.onchange=()=>{frame=0;ticks=0;draw()};play.onclick=()=>{playing=!playing;play.textContent=playing?'暂停':'播放'};prev.onclick=()=>{playing=false;play.textContent='播放';frame=(frame+3)%4;draw()};next.onclick=()=>{playing=false;play.textContent='播放';frame=(frame+1)%4;draw()};setInterval(()=>{if(playing&&++ticks>=meta.groups[move.value][frame]){ticks=0;frame=(frame+1)%4;draw()}},1000/60);draw();</script></html>'''
assert 'groups' in meta
(ART/'index.html').write_text(html.replace('__META__',json.dumps(meta,ensure_ascii=False)),encoding='utf-8')
shutil.copy2(ROOT/'outputs/tutorial-windup-v7-20261015/rebuild_snapshot.py',OUT/'rebuild_snapshot.py')
shutil.copytree(ART,OUT/'art',dirs_exist_ok=True)
recipes=OUT/'recipes';recipes.mkdir(exist_ok=True)
for name in ['build_lumine_training.py','merge_tutorial_v15.py','import_lumine_attacks.py','package_lumine_attack_v8.py']:
    shutil.copy2(ROOT/'runtime/tools'/name,recipes/name)
for name in ['lumine_attack.py','lumine_attack_art.py','lumine_guard.py','tutorial_v15_merge.py','lumine_courses.py','lawachurl_windup.py']:
    shutil.copy2(ROOT/'runtime/tests'/name,recipes/name)
manifest={p.relative_to(OUT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file() and p.name!='package-manifest.json'}
(OUT/'package-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
target=ROOT/'outputs/tutorial-attack-v8-20261015.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.rglob('*'):
        if p.is_file():z.write(p,OUT.name+'/'+p.relative_to(OUT).as_posix())
with zipfile.ZipFile(target) as z:
    assert z.testzip() is None
    for name,digest in manifest.items():assert hashlib.sha256(z.read(OUT.name+'/'+name)).hexdigest()==digest,name
print(json.dumps({'zip':target.relative_to(ROOT).as_posix(),'files':len(manifest)+1,'bytes':target.stat().st_size,'verified':True}))
