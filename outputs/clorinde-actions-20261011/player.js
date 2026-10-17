'use strict';
const $=id=>document.getElementById(id==='stage'?'cv':id),ctx=$('stage').getContext('2d'),bank=window.CLORINDE_ACTIONS||{},foe=window.CLORINDE_OPPONENT||{};
const names={idle:'待机',walk:'前走',backwalk:'后退',jump:'跳跃',forwarddash:'前冲',backdash:'后撤',crouch:'蹲下',standguard:'站防',crouchguard:'蹲防',light1:'轻1',light2:'轻2',light3:'轻3',heavy:'站重',crouchlight:'蹲轻',crouchheavy:'蹲重',airlight:'空轻',airheavy:'空重',E:'E · 枪剑突进',Q:'Q · 残光将终',throw:'投技',victim:'被投',hit_knockdown:'受击与倒地',wakeup:'起身',victory:'胜利',defeat:'败北'};
const imgs=new Map();let selected='idle',time=0,playing=true,desiredPlaying=true,last=0,version=0,active=null,sequence=[],durations=[],total=1,loopCount=0,portrait=null,portraitFit=null,entryRoot=[410,550];
const config=['material','speed','background','branch','body','fx','opponent','movement','mirror','anchors','loop','enemyModel'];
try{const c=JSON.parse(localStorage.getItem('clorinde-player-config')||'{}');for(const id of config)if(id in c){const el=$(id);if(el.type==='checkbox')el.checked=c[id];else el.value=c[id]}}catch(e){}
function save(){try{localStorage.setItem('clorinde-player-config',JSON.stringify(Object.fromEntries(config.map(id=>[id,$(id).type==='checkbox'?$(id).checked:$(id).value]))))}catch(e){}}
function load(file){if(!imgs.has(file))imgs.set(file,new Promise((ok,no)=>{const im=new Image();im.onload=()=>ok(im);im.onerror=()=>no(Error('素材加载失败：'+file));im.src=file+'?v='+(window.CLORINDE_VERSION||'1')}));return imgs.get(file)}
function phase(){let left=time;for(let i=0;i<durations.length;i++){if(left<durations[i])return i;left-=durations[i]}return durations.length-1}
function elapsedPhase(){const i=phase();return(time-durations.slice(0,i).reduce((a,b)=>a+b,0))/Math.max(1,durations[i])}
function shadow(x,y,w=80){ctx.fillStyle='#080b1b35';ctx.beginPath();ctx.ellipse(x,y,w/2,7,0,0,Math.PI*2);ctx.fill()}
function pose(c,im,f,x,y,flip=1,mul=1){c.save();c.translate(x,y);c.scale(flip,1);c.imageSmoothingEnabled=active?.material==='source';const s=f.scale*mul;c.drawImage(im,-f.anchor[0]*s,-f.anchor[1]*s,im.naturalWidth*s,im.naturalHeight*s);c.restore()}
function root(){let [x,y]=entryRoot;const t=time/total,d=active||bank[selected],m=d.motion;if(!$('movement').checked)return[x,y];
 if(m?.kind==='walk')x+=m.direction*m.distance*((loopCount%3)+t);
 if(m?.kind==='dash'){x+=m.distance*Math.min(1,Math.max(0,(t-.12)/.7));if(selected==='backdash')y-=18*Math.sin(t*Math.PI)}
 if(m?.kind==='jump')y-=m.height*Math.sin(t*Math.PI);
 if(m?.kind==='air'){const landing=selected==='airheavy'?durations.slice(0,-1).reduce((a,b)=>a+b,0):total;const p=.35+.65*Math.min(1,time/Math.max(1,landing));y-=m.height*4*p*(1-p)}
 if(selected==='E')x+=110*Math.max(0,Math.min(1,(time-14)/12));
 if(selected==='victim'){const p=phase(),u=elapsedPhase();x=entryRoot[0];if(p===2){x-=70*u;y-=90*u}if(p===3){x-=70+90*u;y-=90*(1-u)}if(p>=4)x-=160}
 return[x,y]}
const contactProfiles={
 raiden:{victim:[[36,21],[35,28],[28,24],[14,16],[13,30],[15,17]],throw:[[45,12],[36,15],[48,21],[40,21]]},
 nahida:{victim:[[38,24],[39,20],[35,22],[42,23],[40,24],[55,22]],throw:[[44,21],[44,22],[47,21],[46,25]]}};
const casterGripProfiles={raiden:[[0,0],[500,235],[500,235],[596,198],[588,172],[0,0]],nahida:[[0,0],[559,275],[559,275],[655,260],[588,172],[0,0]]};
const victimWrists=[[618,162],[630,175],[340,48],[346,43]];
function sourcePoint(point,f,root,flip=1){return[root[0]+(point[0]-f.anchor[0])*f.scale*flip,root[1]+(point[1]-f.anchor[1])*f.scale]}
function sourceAnchorFromPoint(point,f,target,flip=1){return[target[0]-(point[0]-f.anchor[0])*f.scale*flip,target[1]-(point[1]-f.anchor[1])*f.scale]}
function foeState(actor){let key='basic_0',x=860,y=550,flip=-1,contact=null;const p=phase(),u=elapsedPhase(),model=active.model,fd=active.foeData,profile=contactProfiles[model];
 if(selected==='throw'){
  if(p===0)return{key:'basic_0',x:actor[0]+210,y:550,flip:-1,contact:null};
  const casterGrips=casterGripProfiles[model];
  key=['basic_0','victim_0','victim_0','victim_1','victim_3','victim_5'][Math.min(p,5)];
  const native=fd[key],f={anchor:[native.ax,native.ay],scale:native.scale};
  const grip=sourcePoint(casterGrips[Math.min(p,5)],active.sourceFrames[p],actor);
  const q=profile.victim[Number(key.split('_')[1])];
  const attached=sourceAnchorFromPoint(q,f,grip,-1);
  if(time<32){[x,y]=attached;contact={caster:grip,target:sourcePoint(q,f,[x,y],-1),kind:'forearm/upper-arm clinch'};}
  else {const rel=active.foeData.victim_1,rf={anchor:[rel.ax,rel.ay],scale:rel.scale};const releaseGrip=sourcePoint(casterGrips[3],active.sourceFrames[3],actor);const releaseRoot=sourceAnchorFromPoint(profile.victim[1],rf,releaseGrip,-1);const t=Math.min(1,(time-32)/10);x=releaseRoot[0]+170*t;y=releaseRoot[1]+(550-releaseRoot[1])*t-65*Math.sin(Math.PI*t);key=t<.6?'victim_3':'victim_5';if(t>=1)y=550;}
 }
 if(selected==='victim'){
  key='throw_'+[0,1,2,2,3,3][Math.min(p,5)];flip=-1;x=770;
  if(p<2){const native=fd[key],f={anchor:[native.ax,native.ay],scale:native.scale};const wrist=sourcePoint(victimWrists[p],active.sourceFrames[p],actor);const q=profile.throw[Number(key.split('_')[1])];[x,y]=sourceAnchorFromPoint(q,f,wrist,-1);contact={caster:sourcePoint(q,f,[x,y],-1),target:wrist,kind:'wrist'};}
 }
 if(selected==='Q'&&active.branch==='hit'&&time>=52){
  const hits=active.cinematic.hitTicks.filter(t=>t<=time),lastHit=hits.at(-1),dt=lastHit===undefined?999:time-lastHit;
  key=hits.length===3?(time<132?'victim_3':'victim_5'):dt<10?'hurt_0':'victim_2';x=820+hits.length*15;y=hits.length===3?550-70*Math.max(0,(132-time)/14):dt<10?495-25*Math.sin(dt/10*Math.PI):495;
 }
 return{key,x,y,flip,contact}}
function drawEffect(name,x,y,alpha=1){const im=active?.fxImages[name],df=window.CLORINDE_FX?.[name];if(!im||!df)return;const f=active.material==='source'?df.source:df.fit;ctx.save();ctx.globalAlpha=alpha;ctx.imageSmoothingEnabled=active.material==='source';ctx.drawImage(im,x-f.anchor[0]*f.scale,y-f.anchor[1]*f.scale,im.width*f.scale,im.height*f.scale);ctx.restore()}
function stageFx(actor){if(!$('fx').checked||selected==='throw'||selected==='victim')return;const [x,y]=actor,events=active.events||[];
 if(selected==='Q'&&active.branch==='hit'){
  if(time>=42&&time<52){const a=(time-42)/10;ctx.save();ctx.strokeStyle='#c4b7ff';ctx.lineWidth=3;ctx.globalAlpha=a;ctx.beginPath();ctx.arc(x,y-220,24+24*a,0,Math.PI*2);ctx.stroke();ctx.restore()}
  if(time>=52&&time<62)drawEffect('sword',x+150,y-230,1-(time-52)/10);
 }
 for(const e of events){const dt=time-e.tick;if(dt<0||dt>8||e.kind==='grab'||e.kind==='release')continue;const shot=e.kind.includes('shot');
  if(shot){if(dt<3)drawEffect('gun',x+165,y-260,1-dt/3);drawEffect('bullet',x+190+dt*45,y-260,1-dt/9);if(active.branch==='hit'&&dt>=6)drawEffect('impact',x+400,y-245,(9-dt)/3)}
  else{const name=selected==='airheavy'?'down':(['light3','crouchheavy','Q'].includes(selected)?'diagonal':'sword');drawEffect(name,x+85,y-215,1-dt/9);if(active.branch==='hit'&&dt>=3&&dt<6)drawEffect('impact',x+360,y-215,(6-dt)/3)}}}
function cinematicStage(){if(selected!=='Q'||active?.branch!=='hit')return null;const c=active.cinematic;if(time<c.cutin[0])return '确认';if(time<c.cutin[1])return '头像切入';if(time<c.charge[1])return '蓄势';if(time<c.sustain[0])return '释放';if(time<c.fade[0])return '持续冲击';if(time<c.fade[1])return '收束';return '恢复'}
function backdrop(){const stage=cinematicStage();if(!stage||['确认','恢复','头像切入'].includes(stage)||!$('fx').checked)return;
 const c=active.cinematic,a=stage==='收束'?Math.max(0,(c.fade[1]-time)/(c.fade[1]-c.fade[0])):stage==='蓄势'?(time-42)/10:1;
 ctx.save();ctx.globalAlpha=a;const g=ctx.createLinearGradient(0,0,0,550);g.addColorStop(0,'#090c24');g.addColorStop(1,'#33306b');ctx.fillStyle=g;ctx.fillRect(0,0,1200,545);
 const glow=ctx.createRadialGradient(840,190,0,840,190,380);glow.addColorStop(0,'#7774aa30');glow.addColorStop(1,'#7774aa00');ctx.fillStyle=glow;ctx.fillRect(0,0,1200,545);ctx.restore()}
function cutin(){const stage=cinematicStage(),im=active?.material==='fit'?portraitFit:portrait;if(stage!=='头像切入'||!$('fx').checked||!im)return;const p=(time-12)/30,a=Math.min(1,p*5,(1-p)*5);ctx.save();ctx.globalAlpha=a;ctx.imageSmoothingEnabled=active.material==='source';ctx.fillStyle='#11162fee';ctx.fillRect(0,100,1200,220);ctx.drawImage(im,140,110,200,200);ctx.fillStyle='#eeeaff';ctx.font='bold 38px system-ui';ctx.fillText('克洛琳德',390,200);ctx.font='24px system-ui';ctx.fillText('残光将终',390,245);ctx.restore()}
function render(){ctx.fillStyle=$('background').value==='light'?'#f4f6fa':'#202333';ctx.fillRect(0,0,1200,650);backdrop();ctx.strokeStyle=$('background').value==='light'?'#aeb8cb':'#596078';ctx.beginPath();ctx.moveTo(40,545);ctx.lineTo(1160,545);ctx.stroke();const r=root(),p=phase(),f=sequence[p],im=active?.images[p];ctx.save();if($('mirror').checked){ctx.translate(1200,0);ctx.scale(-1,1)}if($('body').checked){shadow(r[0],550);if(im&&f)pose(ctx,im,f,...r,1);}
 if($('opponent').checked){const s=foeState(r),fd=active.foeData[s.key],fi=active?.foeImages[s.key];if(fd&&fi){shadow(s.x,545);pose(ctx,fi,{anchor:[fd.ax,fd.ay],scale:fd.scale},s.x,s.y,s.flip)}if(s.contact&&$('anchors').checked){ctx.strokeStyle='#52e1ba';ctx.beginPath();ctx.arc(...s.contact.target,7,0,Math.PI*2);ctx.stroke()}}stageFx(r);
 if($('anchors').checked){ctx.strokeStyle='#eb6b85';ctx.beginPath();ctx.moveTo(r[0]-10,r[1]);ctx.lineTo(r[0]+10,r[1]);ctx.moveTo(r[0],r[1]-10);ctx.lineTo(r[0],r[1]+10);ctx.stroke()}
 ctx.restore();cutin();ctx.fillStyle=$('background').value==='light'?'#47536a':'#bbc4dd';ctx.font='16px system-ui';ctx.fillText(`克洛琳德 · ${names[selected]} · ${Math.floor(time)}/${total} tick · ${$('material').value==='fit'?'拟合':'源图'}候选`,40,625);
 $('actionName').textContent=names[selected];$('clock').textContent=`${Math.floor(time)} / ${total} tick`;$('phase').textContent=active?.phases[p]||'';$('scrub').value=time;$('play').textContent=playing?'暂停':'播放';document.querySelectorAll('#timeline button').forEach((b,i)=>b.setAttribute('aria-pressed',i===p));
 const contact=foeState(r).contact;
 const state={selected,time,total,phase:p,branch:active.branch,model:active.model,cinematicStage:cinematicStage(),contact,root:r,frames:sequence.length,ready:!!im,events:(active?.events||[]).map(e=>({tick:e.tick,kind:e.kind})),fullStage:selected==='Q'&&active.branch==='hit'&&time>=12&&time<142};
 window.CLORINDE_PREVIEW_STATE=state;$('cv').dataset.preview=JSON.stringify(state);
 $('pair').textContent=($('opponent').checked?(active.model==='raiden'?'雷电将军':'纳西妲')+' · ':'')+(selected==='Q'?(cinematicStage()||'短收势'):selected==='throw'?(time<32?'接触与发力':'释放与落地'):selected==='victim'?'被投与起身衔接':'动作对照');}
async function choose(key){const v=++version,previousKey=selected,previousRoot=active?root():[410,550];playing=false;const base=bank[key],d={...base,...(base?.variants?.[$('enemyModel').value]||{})};if(!base)throw Error('缺动作：'+key);
 const mode=$('material').value,branch=$('branch').value,model=$('enemyModel').value,foeData=window.CLORINDE_OPPONENT_MODELS[model],short=key==='Q'&&branch!=='hit';const indices=short?d.shortBranch.indices:d.frames.map((f,i)=>i),all=mode==='source'?d.sourceFrames:d.frames;
 const nextSequence=indices.map(i=>all[i]),nextDurations=short?d.shortBranch.durations:d.durations,nextTotal=nextDurations.reduce((a,b)=>a+b,0);
 const [images,foePairs,fxPairs]=await Promise.all([Promise.all(nextSequence.map(f=>load(f.file))),Promise.all(Object.entries(foeData).map(async([k,f])=>[k,await load(f.file)])),Promise.all(Object.entries(window.CLORINDE_FX||{}).map(async([k,f])=>[k,await load((mode==='source'?f.source:f.fit).file)]))]);if(v!==version)return;
 if(previousKey!==key)entryRoot=key==='wakeup'&&['hit_knockdown','victim'].includes(previousKey)?previousRoot:[410,550];
 selected=key;time=0;loopCount=0;sequence=nextSequence;durations=nextDurations;total=nextTotal;
 active={...d,material:mode,branch,model,foeData,images,phases:indices.map(i=>d.phases[i]),events:short?d.shortBranch.events:d.events,foeImages:Object.fromEntries(foePairs),fxImages:Object.fromEntries(fxPairs)};$('scrub').max=total-1;$('timeline').replaceChildren();
 const bb=sequence.map((f,i)=>[-f.anchor[0]*f.scale,-f.anchor[1]*f.scale,(images[i].width-f.anchor[0])*f.scale,(images[i].height-f.anchor[1])*f.scale]);
 const left=Math.min(...bb.map(b=>b[0])),top=Math.min(...bb.map(b=>b[1])),right=Math.max(...bb.map(b=>b[2])),bottom=Math.max(...bb.map(b=>b[3]));
 const thumbnailScale=Math.min(146/Math.max(1,right-left),108/Math.max(1,bottom-top));
 sequence.forEach((f,i)=>{const b=document.createElement('button'),c=document.createElement('canvas'),s=document.createElement('span');b.className='frame';c.width=156;c.height=120;const cc=c.getContext('2d');cc.fillStyle='#161827';cc.fillRect(0,0,156,120);pose(cc,images[i],f,5-left*thumbnailScale,5-top*thumbnailScale,1,thumbnailScale);s.textContent=(i+1)+' · '+active.phases[i];b.append(c,s);b.onclick=()=>{playing=desiredPlaying=false;time=durations.slice(0,i).reduce((a,b)=>a+b,0);render()};$('timeline').append(b)});document.querySelectorAll('#actions button').forEach(b=>b.setAttribute('aria-pressed',b.dataset.key===key));$('note').textContent=d.status;const sourceLink=d.sourceFrames.find(f=>!f.file.startsWith('frames/idle-'))||d.sourceFrames[indices[0]];$('source').href=sourceLink.source||sourceLink.file;playing=desiredPlaying;last=0;render()}
function error(e){$('error').hidden=false;$('error').textContent=String(e)}
for(const id of config)$(id).onchange=()=>{save();if(id==='material'||id==='branch'||id==='enemyModel')choose(selected).catch(error);else render()};$('play').onclick=()=>{playing=desiredPlaying=!desiredPlaying;render()};$('restart').onclick=()=>{time=0;loopCount=0;playing=desiredPlaying=true;render()};$('prev').onclick=()=>{playing=desiredPlaying=false;time=Math.max(0,time-1);render()};$('next').onclick=()=>{playing=desiredPlaying=false;time=Math.min(total-1,time+1);render()};$('scrub').oninput=()=>{playing=desiredPlaying=false;time=+$('scrub').value;render()};
const groups={'攻击':['light1','light2','light3','heavy','crouchlight','crouchheavy','airlight','airheavy'],'元素技能':['E','Q'],'投技':['throw','victim'],'移动与防御':['idle','walk','backwalk','jump','forwarddash','backdash','crouch','standguard','crouchguard'],'受击与结算':['hit_knockdown','wakeup','victory','defeat']};
for(const [title,keys]of Object.entries(groups)){const g=document.createElement('div');g.className='group';g.textContent=title;$('actions').append(g);for(const key of keys){const b=document.createElement('button');b.className='action';b.textContent=names[key];b.dataset.key=key;b.disabled=!bank[key];b.onclick=()=>choose(key).catch(error);$('actions').append(b)}}
function tick(now){if(last&&playing){time+=Math.min(80,now-last)*.06*+$('speed').value;if(time>=total){if($('loop').checked){time%=total;loopCount++}else{time=total-1;playing=false}}}last=now;if(active)render();requestAnimationFrame(tick)}
Promise.all([load('portrait.png'),load('fit/portrait.png')]).then(([raw,fit])=>{portrait=raw;portraitFit=fit}).catch(error);choose('idle').then(()=>requestAnimationFrame(tick)).catch(error);
