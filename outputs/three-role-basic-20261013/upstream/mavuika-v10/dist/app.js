'use strict';
const $=id=>document.getElementById(id), canvas=$('stage'), ctx=canvas.getContext('2d');
let art,idle,rig,fxRig,lightFxRig,targetRig,fxArt,lightFxArt,targetArt,targetFlash,artBanks={},model=QModel.create('hit'),playing=false,last=0,accumulator=0,audio,heard=new Set();
const floor=450;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function img(src){return new Promise((resolve,reject)=>{const i=new Image();i.onload=()=>resolve(i);i.onerror=()=>reject(Error('素材未能加载：'+src));i.src=src;});}
function stamp(asset,p,x,y,scale,alpha=1){
 ctx.save();ctx.globalAlpha=alpha;ctx.imageSmoothingEnabled=false;
 ctx.drawImage(asset,...p.rect,x-p.anchor[0]*scale,y-p.anchor[1]*scale,p.rect[2]*scale,p.rect[3]*scale);ctx.restore();
}
function drawTarget(t){const receiver=QFX.frame(model).receiver,p=targetRig.poses[receiver.pose];stamp(targetArt,p,receiver.x,receiver.y,p.scale);if(receiver.flash&&!$('reduced').checked)stamp(targetFlash,p,receiver.x,receiver.y,p.scale,.2);}
function drawFx(plane){for(const l of QFX.frame(model).layers){if(l.plane!==plane)continue;const bank=l.bank==='light'?lightFxRig:fxRig,p=bank.frames.find(p=>p.id===l.id);if(!p)throw Error('Missing FX '+l.id);ctx.save();ctx.translate(l.x,l.y);ctx.rotate(l.rotation||0);stamp(l.bank==='light'?lightFxArt:fxArt,p,0,0,p.scale*l.mult,l.alpha*($('reduced').checked?.55:1));ctx.restore();}}
function draw(){
  ctx.clearRect(0,0,1200,580);ctx.fillStyle='#161519';ctx.fillRect(0,0,1200,580);
  const t=Math.max(model.tick,0),reduced=$('reduced').checked,impact=model.confirmed&&model.stop>0;
  ctx.strokeStyle='#302824';ctx.lineWidth=1;for(let x=70;x<1200;x+=100){ctx.beginPath();ctx.moveTo(x,90);ctx.lineTo(x,450);ctx.stroke();}
  ctx.fillStyle='#211b19';ctx.fillRect(0,floor+1,1200,130);ctx.strokeStyle='#6e4430';ctx.beginPath();ctx.moveTo(0,floor);ctx.lineTo(1200,floor);ctx.stroke();
  ctx.save();if($('mirror').checked){ctx.translate(1200,0);ctx.scale(-1,1);}
  if(impact&&!reduced){const intensity=t===55?7:2;ctx.translate((model.wallTick%2?1:-1)*intensity,model.wallTick%3-1);}
  if(model.action==='q'){ctx.strokeStyle='#7be0b3';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(model.origin.x,430);ctx.lineTo(model.origin.x,475);ctx.stroke();ctx.fillStyle='#7be0b3';ctx.fillText('起手 = 落点',model.origin.x-35,495);}
  drawFx('rear');
  drawFx('ground');
  const presentation=QFX.frame(model),targetInFront=presentation.receiver.x>=presentation.body.x;
  if(!targetInFront)drawTarget(t);

  if(art&&rig){
    const c=QModel.choreography(model);ctx.imageSmoothingEnabled=false;
    const mode=$('material').value,bank=rig.materials[mode],p=bank.poses[c.pose],scale=p.scale;
    const asset=p.file?idle:artBanks[mode];
    ctx.drawImage(asset,...p.rect,c.x-p.anchor[0]*scale,c.y-p.anchor[1]*scale,p.rect[2]*scale,p.rect[3]*scale);
  }
  if(targetInFront)drawTarget(t);
  drawFx('front');
  ctx.restore();
  $('phase').textContent=QModel.phase(model);$('readout').textContent=t+' / '+QModel.endTick(model);$('scrub').value=t;$('hitCount').textContent=model.hits+' 次命中';
  $('subtitle').textContent=model.action==='q'&&model.confirmed&&t>=45&&t<=65?'「太阳的轰鸣！」':'';
  $('play').textContent=playing?'暂停':'播放大招';
}
function sound(hit){
  if(!$('sound').checked)return;
  try{
    audio??=new (window.AudioContext||window.webkitAudioContext)();audio.resume();
    const when=audio.currentTime,osc=audio.createOscillator(),gain=audio.createGain();
    osc.type='triangle';osc.frequency.setValueAtTime(hit.weight===3?105:180,when);osc.frequency.exponentialRampToValueAtTime(38,when+.22);
    gain.gain.setValueAtTime(.001,when);gain.gain.linearRampToValueAtTime(hit.weight===3?.2:.07,when+.01);gain.gain.exponentialRampToValueAtTime(.001,when+.3);osc.connect(gain);gain.connect(audio.destination);osc.start(when);osc.stop(when+.32);
  }catch(e){$('status').textContent='浏览器未能开启打击音，动画仍可播放。';}
}
function advance(){const before=model.events.length;QModel.step(model);for(const e of model.events.slice(before)){if(!heard.has(e.id)){heard.add(e.id);sound(e);}}if(model.ended)playing=false;}
function updateBeats(){const vehicle=$('action').value!=='q';const content=vehicle?[
 ['01 / 骑车','冲入','重击与冲刺攻击使用骑车动作，不持大剑。'],['02 / 制动','侧滑车铲','低位车头铲击，单次结算。'],['03 / 收势','刹停恢复','车铲收势，保留反击窗口。']
 ]:[['01 / 骑车升空','冲向太阳','第8帧无伤害确认；命中才斜上冲向太阳，未确认则原地短收招。'],['02 / 切剑重斩','「太阳的轰鸣！」','离车切大剑，第55动作帧一刀结算伤害，命中停顿12帧。'],['03 / 原位收招','火神回原地','出刀下降直接落回起手坐标，收尾无额外伤害。']];for(let i=0;i<3;i++)for(const [j,k] of ['label','title','text'].entries())$('beat'+(i+1)+'-'+k).textContent=content[i][j];}
function reset(){updateBeats();model=QModel.create($('outcome').value,$('action').value);heard.clear();accumulator=0;draw();}
function loop(now){if(playing){accumulator+=Math.min(now-last,100)*Number($('speed').value);while(accumulator>=1000/60&&playing){advance();accumulator-=1000/60;}draw();}last=now;requestAnimationFrame(loop);}
$('play').onclick=()=>{if(model.ended)reset();playing=!playing;last=performance.now();draw();};
$('restart').onclick=()=>{reset();playing=true;last=performance.now();draw();};
$('step').onclick=()=>{playing=false;advance();draw();};
$('scrub').oninput=()=>{playing=false;model=QModel.seek($('outcome').value,Number($('scrub').value),$('action').value);heard=new Set(model.events.map(e=>e.id));draw();};
$('action').onchange=()=>{playing=false;$('scrub').max=$('action').value!=='q'?54:104;reset();};
$('outcome').onchange=()=>{playing=false;reset();};
$('material').onchange=draw;$('mirror').onchange=draw;$('reduced').onchange=draw;
$('middle').onclick=()=>{playing=false;$('action').value='q';updateBeats();$('scrub').max=104;$('outcome').value='hit';model=QModel.seek('hit',55);heard=new Set(model.events.map(e=>e.id));draw();};
Promise.all([img('assets/mavuika-idle-original.png'),fetch('assets/rig.json').then(r=>{if(!r.ok)throw Error('动作锚点未能加载');return r.json();})]).then(async([w,r])=>{idle=w;rig=r;for(const [mode,bank] of Object.entries(r.materials))artBanks[mode]=await img('assets/'+bank.file);art=artBanks.source;
[fxRig,lightFxRig,targetRig]=await Promise.all(['q-fx-rig-v8.json','light1-fx-rig-v7.json','v3-target-rig-v7.json'].map(f=>fetch('assets/'+f).then(r=>{if(!r.ok)throw Error('特效数据加载失败');return r.json();})));
[fxArt,lightFxArt,targetArt,targetFlash]=await Promise.all([fxRig.fit,lightFxRig.fit,targetRig.file,'v3-target-flash-v7.png'].map(f=>img('assets/'+f)));
for(const id of ['play','restart','step','scrub'])$(id).disabled=false;$('status').textContent='V10 近距离确认 → 骑车冲上 → 下车一刀 → 原位落地 · 选项模拟命中 · 动作与对手编排待验收';reset();requestAnimationFrame(loop);}).catch(e=>{$('phase').textContent='素材加载失败';$('status').textContent=e.message+'，请刷新重试。';});
