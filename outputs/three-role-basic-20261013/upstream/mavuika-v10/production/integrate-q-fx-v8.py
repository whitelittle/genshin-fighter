from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/'dist';p=d/'app.js';s=p.read_text();s=s.replace('let art,idle,rig,artBanks={}', 'let art,idle,rig,fxRig,lightFxRig,targetRig,fxArt,lightFxArt,targetArt,targetFlash,artBanks={}')
start=s.index('function slash(t)');end=s.index('function draw(){');s=s[:start]+'''function stamp(asset,p,x,y,scale,alpha=1){
 ctx.save();ctx.globalAlpha=alpha;ctx.imageSmoothingEnabled=false;
 ctx.drawImage(asset,...p.rect,x-p.anchor[0]*scale,y-p.anchor[1]*scale,p.rect[2]*scale,p.rect[3]*scale);ctx.restore();
}
function drawTarget(t){const receiver=QFX.frame(model).receiver,p=targetRig.poses[receiver.pose];stamp(targetArt,p,receiver.x,receiver.y,p.scale);if(receiver.flash&&!$('reduced').checked)stamp(targetFlash,p,receiver.x,receiver.y,p.scale,.45);}
function drawFx(){for(const l of QFX.frame(model).layers){const bank=l.bank==='light'?lightFxRig:fxRig,p=bank.frames.find(p=>p.id===l.id);if(!p)throw Error('Missing FX '+l.id);stamp(l.bank==='light'?lightFxArt:fxArt,p,l.x,l.y,p.scale*l.mult,l.alpha*($('reduced').checked?.55:1));}}
''' + s[end:]
s=s.replace('  sun(t);','')
start=s.index("  if(model.action!=='q'&&t>=12");end=s.index('  ctx.restore();',start);s=s[:start]+'''  drawFx();
'''+s[end:]
# Also remove leftover old slash/flash lines after old skid function's inline restore.
s=s.replace('  slash(t,impact);','');s=s.replace("  if(impact&&t===55&&!reduced){ctx.fillStyle='rgba(255,237,199,.1)';ctx.fillRect(0,0,1200,580);}",'')
old="art=artBanks.source;for(const id"
new="""art=artBanks.source;
[fxRig,lightFxRig,targetRig]=await Promise.all(['q-fx-rig-v8.json','light1-fx-rig-v7.json','v3-target-rig-v7.json'].map(f=>fetch('assets/'+f).then(r=>{if(!r.ok)throw Error('特效数据加载失败');return r.json();})));
[fxArt,lightFxArt,targetArt,targetFlash]=await Promise.all([fxRig.fit,lightFxRig.fit,targetRig.file,'v3-target-flash-v7.png'].map(f=>img('assets/'+f)));
for(const id"""
assert old in s;s=s.replace(old,new).replace('无伤害确认 → 骑车升空 → 切剑单次重斩 → 原位恢复 · 独立演出候选，支持三档素材对照','V8 独立太阳／刀光／轮胎火尾／接触特效 · 选项模拟命中 · 动作与对手编排待验收')
p.write_text(s)
p=d/'index.html';s=p.read_text().replace('候选 · 07','候选 · 08').replace('<script src="app.js"></script>','<script src="q-fx-model-v8.js"></script><script src="app.js"></script>');s=s.replace('<section class="stage">','<p><a href="review/mavuika-q-fx-v8.gif">Q 特效动图</a> · <a href="review/mavuika-bike-fx-v8.gif">车铲三分支动图</a> · <a href="mavuika-q-fx-offline-v8.html" download>下载 Q 与车铲离线查看器</a></p><section class="stage">');p.write_text(s)
