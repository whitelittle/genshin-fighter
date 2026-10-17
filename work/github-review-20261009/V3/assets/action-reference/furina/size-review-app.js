'use strict';
const $=id=>document.getElementById(id),ctx=$('cv').getContext('2d');
let frames=[],images=[],time=0,playing=true,last=0,bank={},selected='待机',loadVersion=0;
let durations=[],phases=[],total=1;
let foeAtlas=null,foeImages={},effectImages=[],foeFitted={},foeFitImages={},ultimatePortrait=null,ultimatePortraitFit=null,helperBank={},helperImages={source:{},fit:{}};
async function loadFoe(){const base='/actions/raiden/';foeAtlas=await(await fetch(base+'atlas.json?v=r31')).json();for(const sheet of ['basic','hurt','guard','victim','throw','light','heavy','air']){const data=foeAtlas[sheet];if(!data)continue;foeImages[sheet]=await new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=no;im.src=base+data.url})};foeFitted=await(await fetch('foe-fitted.json')).json();await Promise.all(Object.entries(foeFitted).map(async([key,f])=>{foeFitImages[key]=await new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=no;im.src=f.file})}))}
function shadow(x,y,w=100){ctx.fillStyle='#08071066';ctx.beginPath();ctx.ellipse(x,y,w/2,8,0,0,Math.PI*2);ctx.fill()}
function pairedRoot(){let x=550,y=550;if(time>=20&&time<30)x-=15*(time-20)/10;else if(time>=30&&time<38){const u=(time-30)/8;x=535+200*u;y=550-100*Math.sin(u*Math.PI/2)}else if(time>=38&&time<50){const u=(time-38)/12;x=735+60*u;y=450+100*u}else if(time>=50)x=795;return[x,y]}
function drawFoe(){if(!$('opponent').checked||!foeAtlas)return;let key='basic',index=0,x=810,y=550,flip=-1;const p=phase();
 if(selected==='投技'){[x,y]=pairedRoot();key=time>=50?'hurt':'victim';index=time>=50?3:time>=30?3:0;}
 if(selected==='被投'){x=410;flip=1;key='throw';index=time<30?0:time<50?2:3;}
 if(selected==='Q · 万众狂欢'){x=790;if(time>=12&&time<56){key='hurt';index=0}if(time>=56&&time<122){key='victim';index=3;y=450-Math.sin(time*.2)*12;x+=Math.sin(time*.4)*4}if(time>=122){const u=Math.min(1,(time-122)/36);key='hurt';index=3;x+=u*100;y=450+100*u}}
 const cd=bank[selected]?.combatDesign;if(cd){x=['站重','E · 孤心沙龙'].includes(selected)?790:660;const hit=cd.startup;if(time>=hit&&time<hit+cd.active+10){key='hurt';index=0;x+=Math.min(18,(time-hit)*2)}}
 if(['站立格挡','蹲防'].includes(selected)){x=690;if(p===3){key=selected==='蹲防'?'air':'light';index=1}}
 if($('material').value==='fit'){const f=foeFitted[key+'_'+index],im=foeFitImages[key+'_'+index];if(!f||!im)return;shadow(x,550);ctx.save();ctx.translate(x,y);ctx.scale(flip,1);ctx.imageSmoothingEnabled=false;ctx.drawImage(im,-f.ax*f.scale,-f.ay*f.scale,im.naturalWidth*f.scale,im.naturalHeight*f.scale);ctx.restore();return} const sheet=foeAtlas[key],im=foeImages[key],f=sheet?.frames[index];if(!f||!im)return;const scale=330/sheet.height;shadow(x,550);ctx.save();ctx.translate(x,y);ctx.scale(flip,1);ctx.imageSmoothingEnabled=false;ctx.drawImage(im,f.x,f.y,f.w,f.h,-f.ax*scale,-f.ay*scale,f.w*scale,f.h*scale);ctx.restore()}
function stageRoot(){let x=410,y=550;if(selected==='被投')return pairedRoot();const d=bank[selected],t=time/Math.max(1,total);if(selected==='空轻'||selected==='空重'){y=550-(d.airHoverWorld||100);if($('stageMove').checked)x+=90*t;return [x,y]}if(!$('stageMove').checked)return [x,y];if(d?.motion){const p=phase(),start=durations.slice(0,p).reduce((a,b)=>a+b,0),u=Math.min(1,(time-start)/durations[p]),a=d.motion[p],b=d.motion[Math.min(p+1,d.motion.length-1)];return[x+a[0]+(b[0]-a[0])*u,y+a[1]+(b[1]-a[1])*u]}if(selected==='前走'||selected==='后退')x+=(selected==='后退'?-1:1)*120*t;if(d?.combatDesign?.lunge){const s=d.combatDesign.startup;x+=d.combatDesign.lunge*Math.min(1,time/Math.max(1,s))}return [x,y]}
$('stageMove').onchange=render;$('opponent').onchange=render;
$('material').onchange=()=>choose(selected).catch(showError);
function phase(){let t=time;for(let i=0;i<durations.length;i++){if(t<durations[i])return i;t-=durations[i]}return Math.max(0,durations.length-1)}
function drawPose(c,i,x,y,scale){const f=frames[i],im=images[i];if(!im)return;const factor=scale/f.scale,sx=(f.scaleX||f.scale)*factor,sy=(f.scaleY||f.scale)*factor,flip=f.facingCorrection||1;c.save();c.translate(x,y);c.scale(flip,1);c.imageSmoothingEnabled=false;c.drawImage(im,-f.anchor[0]*sx,-f.anchor[1]*sy,im.naturalWidth*sx,im.naturalHeight*sy);c.restore()}
function drawEffects(x,y){const e=bank[selected]?.effects;if(!$('fx').checked)return;
 if(['站立格挡','蹲防'].includes(selected)&&phase()===3){ctx.save();ctx.strokeStyle='#c8f4ff';ctx.lineWidth=3;const yy=y-(selected==='蹲防'?160:215);ctx.beginPath();ctx.moveTo(x+80,yy-12);ctx.lineTo(x+100,yy+12);ctx.moveTo(x+100,yy-12);ctx.lineTo(x+80,yy+12);ctx.stroke();ctx.restore()}
 // 投技/被投只展示动作与双方位移，不叠加特效；全局特效开关也不能恢复。
 if(['投技','被投'].includes(selected))return;
 if(selected==='空轻'){drawSwordTrail(x,y);return}
 if(!e||time<e.startTick||time>=e.startTick+e.duration)return;const age=time-e.startTick,list=$('material').value==='fit'?e.fitFrames:e.sourceFrames;let i=Math.min(list.length-1,Math.floor(age/e.duration*list.length)),xx=x,yy=y,alpha=Math.min(1,(e.duration-age)/5),factor=1;
 if(selected==='Q · 万众狂欢'){if(time<12){i=0;xx=460+(time-6)*50;yy=350;factor=.40}else if(time<56)return;else if(time<78){i=3;xx=790;yy=380;factor=.45;alpha=Math.max(0,1-(time-56)/22)}else if(time<100){i=4+Math.min(2,Math.floor((time-78)/22*3));xx=685;yy=338}else if(time<122){i=2;xx=790;yy=485;factor=.6;alpha=Math.max(0,1-(time-100)/22)}else{i=3;xx=810;yy=420;alpha=(142-time)/20}}
 else{const n=e.nozzles?e.nozzles[phase()]:e.worldOffset;if(!n)return;xx+=n[0];yy+=n[1];if(selected==='E · 孤心沙龙')i=time<18?0:time<24?1:time<30?2:3;if(e.impactOnly){i=3;factor=.25} }
 const f=list[i],im=effectImages[i];if(!f||!im)return;ctx.save();ctx.translate(xx,yy);if(e.rotation)ctx.rotate(e.rotation);ctx.imageSmoothingEnabled=false;ctx.globalAlpha=Math.max(0,Math.min(1,alpha));const s=f.scale*factor;ctx.drawImage(im,-f.anchor[0]*s,-f.anchor[1]*s,im.naturalWidth*s,im.naturalHeight*s);ctx.restore()}
function drawBoxes(x,y){const d=bank[selected]?.combatDesign;if(!$('boxes')?.checked||!d)return;const airborne=selected==='空轻'||selected==='空重',floor=airborne?y+110:y;ctx.strokeStyle='#7be79f';ctx.strokeRect(x-42,floor-(selected.startsWith('蹲')?190:290),84,selected.startsWith('蹲')?190:290);if(time>=d.startup&&time<d.startup+d.active){const [bx,by,bw,bh]=d.box;ctx.fillStyle='#ff6b6b33';ctx.fillRect(x+bx,floor-by-bh,bw,bh);ctx.strokeStyle='#ff7777';ctx.strokeRect(x+bx,floor-by-bh,bw,bh)}}
function drawSwordTrail(x,y){
 const d=bank[selected],cd=d.combatDesign;if(time<cd.startup||time>=cd.startup+cd.active)return;
 const p=phase(),marks=d.swordMarkers;if(!marks?.[p])return;
 const local=(i,k)=>{const f=d.sourceFrames[i],q=marks[i][k];return [x+(q[0]-f.anchor[0])*f.scale,y+(q[1]-f.anchor[1])*f.scale]};
 const hand=local(p,'wrist'),tip=local(p,'tip'),prev=local(Math.max(0,p-1),'tip');
 const u=(time-cd.startup)/Math.max(1,cd.active),alpha=Math.sin(Math.PI*Math.min(.98,u+.06));
 ctx.save();ctx.globalAlpha=alpha*.7;ctx.fillStyle='#80ddf8';ctx.beginPath();ctx.moveTo(...hand);ctx.quadraticCurveTo(...prev,...tip);ctx.lineTo(hand[0]+3,hand[1]+3);ctx.closePath();ctx.fill();
 ctx.strokeStyle='#e2faff';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(...prev);ctx.quadraticCurveTo((prev[0]+tip[0])/2+10,(prev[1]+tip[1])/2,...tip);ctx.stroke();ctx.restore();
}
function ultimateBackdrop(){if(selected!=='Q · 万众狂欢'||!$('fx').checked)return;const fade=Math.min(1,time/10,Math.max(0,(total-time)/20));ctx.save();ctx.globalAlpha=fade;const g=ctx.createRadialGradient(750,320,30,750,320,680);g.addColorStop(0,'#426b8c');g.addColorStop(1,'#0b182c');ctx.fillStyle=g;ctx.fillRect(0,0,1200,650);if(time>=42){ctx.strokeStyle='#9edcea';ctx.lineWidth=3;ctx.beginPath();ctx.ellipse(650,550,440,26,0,0,Math.PI*2);ctx.stroke();for(let j=0;j<3;j++){ctx.globalAlpha=fade*.12;ctx.fillStyle='#c3f4ff';ctx.beginPath();ctx.moveTo(350+j*260,30);ctx.lineTo(260+j*260,550);ctx.lineTo(500+j*260,550);ctx.closePath();ctx.fill()}}for(let i=0;i<24;i++){ctx.fillStyle=i%2?'#c9eaff':'#8acbe9';ctx.globalAlpha=fade*.4;ctx.fillRect((i*173+time*2)%1200,(i*89+time*.4)%550,3,3)}const hit=bank[selected]?.cinematic?.hitTicks.some(t=>time>=t&&time<t+4);if(hit){ctx.globalAlpha=fade*.35;ctx.fillStyle='#eafaff';ctx.fillRect(0,0,1200,650)}ctx.restore()}
function ultimateCutin(){if(selected!=='Q · 万众狂欢'||!$('fx').checked||time<12||time>=42)return;const im=$('material').value==='fit'?ultimatePortraitFit:ultimatePortrait;if(!im)return;const fade=Math.min(1,(time-12)/5,(42-time)/7);ctx.save();ctx.globalAlpha=fade;ctx.fillStyle='rgba(11,35,64,.92)';ctx.fillRect(0,120,1200,240);ctx.fillStyle='#9adff6';ctx.fillRect(0,120,1200,2);ctx.fillRect(0,358,1200,2);ctx.imageSmoothingEnabled=false;const h=310,w=h*im.naturalWidth/im.naturalHeight;ctx.drawImage(im,100+Math.min(40,(time-12)*3),125,w,h);ctx.fillStyle='#e1f6ff';ctx.font='bold 46px system-ui';ctx.fillText('万众狂欢',600,240);ctx.font='22px system-ui';ctx.fillText('芙宁娜',605,285);ctx.restore()}
function render(){ctx.clearRect(0,0,1200,650);ctx.fillStyle=$('background')?.value||'#171625';ctx.fillRect(0,0,1200,650);ultimateBackdrop();ctx.strokeStyle='#655f79';ctx.beginPath();ctx.moveTo(70,550);ctx.lineTo(1130,550);ctx.stroke();const [x,y]=stageRoot();shadow(x,550);if($('body').checked&&frames.length)drawPose(ctx,phase(),x,y,frames[phase()].scale);drawFoe();drawHelpers(x,y);drawEffects(x,y);ultimateCutin();drawBoxes(x,y);$('name').textContent=selected;$('phase').textContent=phases[phase()]||'';$('clock').textContent=`${Math.floor(time)+1} / ${total} 预览帧`;$('pair').textContent=bank[selected]?.status||'';$('scrub').value=time;document.querySelectorAll('.frame').forEach((b,i)=>b.setAttribute('aria-pressed',i===phase()));}
function sync(){$('play').textContent=playing?'暂停':'播放'}
$('play').onclick=()=>{playing=!playing;sync()};$('restart').onclick=()=>{time=0;playing=true;sync()};$('prev').onclick=()=>{playing=false;time=Math.max(0,time-1);sync();render()};$('next').onclick=()=>{playing=false;time=Math.min(total-1,time+1);sync();render()};$('scrub').oninput=()=>{playing=false;time=+$('scrub').value;sync();render()};$('body').onchange=render;$('fx').checked=true;$('fx').disabled=false;$('fx').onchange=render;if($('boxes'))$('boxes').onchange=render;
const groups={'移动':['待机','前走','后退','跳跃','前冲','后撤','蹲下'],'防御':['站立格挡','蹲防'],'攻击':['轻攻一','轻攻二','轻攻三','站重','蹲轻','蹲重','空轻','空重'],'技能与投技':['E · 孤心沙龙','Q · 万众狂欢','投技','被投'],'受击与结算':['受击与倒地','起身','胜利','败北']};
async function choose(name){const version=++loadVersion,wasPlaying=playing;playing=false;images=[];frames=[];effectImages=[];time=0;selected=name;const d=bank[name];const chosen=$('material').value==='source'?(d.sourceFrames||d.frames):d.frames;const load=f=>new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=()=>no(Error('素材加载失败：'+f.file));im.src=f.file});const [loaded,effects]=await Promise.all([Promise.all(chosen.map(load)),Promise.all((($('material').value==='fit'?(d.effects?.fitFrames||d.effects?.frames):(d.effects?.sourceFrames||d.effects?.frames))||[]).map(load))]);if(version!==loadVersion)return;frames=chosen;images=loaded;effectImages=effects;durations=d.durations;phases=d.phases;total=durations.reduce((a,b)=>a+b,0);$('scrub').max=total-1;$('timeline').replaceChildren();frames.forEach((f,i)=>{const b=document.createElement('button');b.className='frame';const c=document.createElement('canvas');c.width=240;c.height=190;drawPose(c.getContext('2d'),i,110,175,f.scale*.4);const label=document.createElement('span');label.textContent=phases[i];b.append(c,label);b.onclick=()=>{playing=false;time=durations.slice(0,i).reduce((a,b)=>a+b,0);sync();render()};$('timeline').append(b)});document.querySelectorAll('.action').forEach(b=>b.setAttribute('aria-pressed',b.dataset.name===name));$('note').textContent=d.status;$('sourceLink').href=chosen[0].source||chosen[0].file;playing=wasPlaying;last=0;sync();render()}
async function init(){try{const portraitLoad=file=>new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=no;im.src=file});[ultimatePortrait,ultimatePortraitFit]=await Promise.all([portraitLoad('ultimate-portrait.png'),portraitLoad('ultimate-portrait-fit.png')]);bank=await(await fetch('actions-size-candidate.json?v=a72f4f5c700c')).json();await loadHelpers(portraitLoad);for(const [g,names]of Object.entries(groups)){const title=document.createElement('div');title.className='group';title.textContent=g;$('actions').append(title);for(const n of names){const b=document.createElement('button');b.className='action';b.dataset.name=n;b.textContent=n;b.disabled=!bank[n];b.onclick=()=>choose(n).catch(showError);$('actions').append(b)}}await choose('待机');$('loading').hidden=true;['play','restart','prev','next'].forEach(id=>$(id).disabled=false);requestAnimationFrame(tick)}catch(e){showError(e)}}

async function loadHelpers(load){helperBank=await(await fetch('helpers.json')).json();for(const mode of ['source','fit'])for(const[key,d]of Object.entries(helperBank)){helperImages[mode][key]=await Promise.all(d[mode==='fit'?'fitFrames':'sourceFrames'].map(f=>load(f.file)))}}
function helperSprite(key,i,x,y,rotation=0){const mode=$('material').value,d=helperBank[key],f=d?.[mode==='fit'?'fitFrames':'sourceFrames'][i],im=helperImages[mode]?.[key]?.[i];if(!f||!im)return;ctx.save();ctx.translate(x,y);ctx.rotate(rotation);ctx.imageSmoothingEnabled=false;ctx.drawImage(im,-f.anchor[0]*f.scale,-f.anchor[1]*f.scale,im.naturalWidth*f.scale,im.naturalHeight*f.scale);ctx.restore()}
function drawHelpers(x,y){if(!$('companions')?.checked)return;const p=phase(),index=[0,1,2,2,3,0][p]||0,d=bank[selected]?.combatDesign,keys=['usher','chevalmarin','crabaletta'];
 if(['空重'].includes(selected)){const key=selected.startsWith('蹲')?'crabaletta':selected==='空轻'?'usher':'chevalmarin',start=d.startup,u=time<start?0:time<start+d.active+7?Math.min(1,(time-start)/(d.active+7)):Math.max(0,1-(time-start-d.active-7)/Math.max(1,total-start-d.active-7));helperSprite(key,index,x+120+130*u,selected.startsWith('蹲')?550:y+70+(selected==='空轻'?u*60:0),selected==='空重'?.38:0);}
 if(selected==='E · 孤心沙龙'){const gather=Math.min(1,time/18);for(let i=0;i<3;i++)helperSprite(keys[i],index,x+70+i*70+gather*35,550-[150,220,0][i])}
 if(selected==='Q · 万众狂欢'){const hits=[56,78,100],targets=[[680,465],[650,395],[730,550]],bases=[[x-50,490],[x+40,370],[x+100,550]];for(let i=0;i<3;i++){const h=hits[i],u=time<h-14?0:time<h?Math.min(1,(time-h+14)/14):time<h+14?1:Math.max(0,1-(time-h-14)/14);const xx=bases[i][0]+(targets[i][0]-bases[i][0])*u,yy=bases[i][1]+(targets[i][1]-bases[i][1])*u;helperSprite(keys[i],time<h?u>0?1:0:time<h+14?2:3,xx,yy)}}
 if(selected==='投技'){if(time<30)helperSprite('usher',time<8?0:2,500,440);if(time>=20&&time<50){const u=Math.min(1,(time-20)/10);helperSprite('crabaletta',time<30?1:2,480+u*90+(time>30?(time-30)*6:0),550)}}
}

function showError(e){$('loading').hidden=true;$('error').style.display='block';$('error').textContent=String(e)}
const configIds=['material','speed','background','body','fx','stageMove','opponent','companions','boxes','loop'];
try{const c=JSON.parse(localStorage.getItem('furina-display-config')||'{}');for(const id of configIds){const el=$(id);if(el&&id in c){if(el.type==='checkbox')el.checked=c[id];else el.value=c[id]}}}catch(e){}
function saveConfig(){const c={};for(const id of configIds){const el=$(id);if(el)c[id]=el.type==='checkbox'?el.checked:el.value}try{localStorage.setItem('furina-display-config',JSON.stringify(c))}catch(e){}}
for(const id of configIds){const el=$(id);if(!el)continue;const previous=el.onchange;el.onchange=ev=>{saveConfig();if(previous)previous(ev);else render()}}
function tick(now){if(last&&playing){time+=Math.min(100,now-last)*.06*+$('speed').value;if(time>=total){if($('loop').checked)time%=total;else{time=total-1;playing=false;sync()}}}last=now;if(frames[0]?.source)$('sourceLink').href=frames[0].source;render();requestAnimationFrame(tick)}init();loadFoe().catch(showError);

const scaleAuditRender=render;render=function(){scaleAuditRender();const f=frames[phase()],a=f?.anatomy;if(a?.userRejected)$("note").textContent="用户已指出比例不对：只修正显示参数，不代表源图比例通过。";if(selected==="受击与倒地"&&phase()===3)$("note").textContent="倒地最后一帧已按明确要求复用起身第1帧：同图、同倍率、同锚点。"};

// Candidate only: flight and movement input are independent of attack animation.
let airEntryTick=12,previewMoveX=0,moveHeld=new Set();
const jumpTicks=38,jumpPeak=160;
function flightRate(){return jumpTicks/bank['跳跃'].durations.reduce((a,b)=>a+b,0)}
function jumpHeight(t){return jumpPeak*Math.sin(Math.PI*Math.max(0,Math.min(1,t/jumpTicks)))}
const priorChoose=choose;
choose=async function(name){if(name==='空轻'||name==='空重')airEntryTick=selected==='跳跃'?time/total*jumpTicks:['空轻','空重'].includes(selected)?Math.min(jumpTicks,airEntryTick+time*flightRate()):12;return priorChoose(name)};
const priorStageRoot=stageRoot;
stageRoot=function(){if(selected==='空轻'||selected==='空重')return[410+previewMoveX,550-jumpHeight(airEntryTick+time*flightRate())];if(selected==='跳跃')return[410+previewMoveX,550-jumpHeight(time/total*jumpTicks)];return priorStageRoot()};
window.addEventListener('keydown',e=>{if(['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;if(['ArrowLeft','ArrowRight','a','d','A','D'].includes(e.key)){moveHeld.add(e.key.toLowerCase());e.preventDefault()}});
window.addEventListener('keyup',e=>moveHeld.delete(e.key.toLowerCase()));
window.addEventListener('blur',()=>moveHeld.clear());
const priorTick=tick;
tick=function(now){if(last&&playing&&['跳跃','空轻','空重'].includes(selected)){const dt=Math.min(100,now-last)*.06*+$('speed').value;previewMoveX=Math.max(-250,Math.min(250,previewMoveX+4*dt*((moveHeld.has('arrowright')||moveHeld.has('d')?1:0)-(moveHeld.has('arrowleft')||moveHeld.has('a')?1:0))))}priorTick(now)};
function airHelperState(x,y){
 const cd=bank['空重'].combatDesign,active=time>=cd.startup&&time<cd.startup+cd.active,index=active?2:time<cd.startup?1:3;
 const mouths=[[390,250],[410,249],[393,278],[390,250]],src=helperBank.chevalmarin.sourceFrames[index],q=mouths[index];
 const offset=[(q[0]-src.anchor[0])*src.scale,(q[1]-src.anchor[1])*src.scale],root=[x+120,y-140-offset[1]];
 return{index,root,mouth:[root[0]+offset[0],y-140],active};
}
const priorHelpers=drawHelpers;
drawHelpers=function(x,y){if(selected!=='空重')return priorHelpers(x,y);if(!$('companions').checked)return;const h=airHelperState(x,y);helperSprite('chevalmarin',h.index,...h.root,0)};
const priorEffects=drawEffects;
drawEffects=function(x,y){
 if(selected!=='空重')return priorEffects(x,y);if(!$('fx').checked)return;
 const h=airHelperState(x,y);if(!h.active)return;
 const e=bank[selected].effects,list=$('material').value==='fit'?e.fitFrames:e.sourceFrames,age=time-bank[selected].combatDesign.startup,i=Math.min(list.length-1,Math.floor(age/bank[selected].combatDesign.active*list.length)),f=list[i],im=effectImages[i];if(!im)return;
 const angle=Math.atan2(330-h.mouth[1],660-h.mouth[0]);
 ctx.save();ctx.translate(...h.mouth);ctx.rotate(angle);ctx.imageSmoothingEnabled=false;ctx.drawImage(im,-f.anchor[0]*f.scale,-f.anchor[1]*f.scale,im.naturalWidth*f.scale,im.naturalHeight*f.scale);ctx.restore();
};
