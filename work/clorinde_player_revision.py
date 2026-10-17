from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-actions-20261011'
p=O/'player.js';s=p.read_text(encoding='utf-8')
s=s.replace("Q:'Q · 残光截击'","Q:'Q · 残光将终'")
s=s.replace("'loop'];","'loop','enemyModel'];")
s=s.replace("const p=phase(),u=elapsedPhase();x=550;if(p===1)y-=80*u;if(p===2)y-=125;if(p===3){x+=100*u;y-=125*(1-u)}if(p>=4)x=650", "const p=phase(),u=elapsedPhase();x=entryRoot[0];if(p===2){x-=70*u;y-=90*u}if(p===3){x-=70+90*u;y-=90*(1-u)}if(p>=4)x-=160")
start=s.index('function foeState(');end=s.index('function drawEffect(',start)
s=s[:start]+'''const contactProfiles={
 raiden:{victim:[[35,20],[14,20],[14,19],[14,16],[13,30],[15,17]],throw:[[45,12],[36,15],[48,21],[40,21]]},
 nahida:{victim:[[38,22],[38,20],[35,22],[42,23],[40,24],[55,22]],throw:[[44,21],[44,22],[47,21],[46,25]]}};
const casterGrips=[[475,190],[402,226],[435,233],[251,194],[510,151],[279,173]];
const victimWrists=[[618,162],[630,175],[340,48],[346,43]];
function sourcePoint(point,f,root,flip=1){return[root[0]+(point[0]-f.anchor[0])*f.scale*flip,root[1]+(point[1]-f.anchor[1])*f.scale]}
function sourceAnchorFromPoint(point,f,target,flip=1){return[target[0]-(point[0]-f.anchor[0])*f.scale*flip,target[1]-(point[1]-f.anchor[1])*f.scale]}
function foeState(actor){let key='basic_0',x=860,y=550,flip=-1,contact=null;const p=phase(),u=elapsedPhase(),model=active.model,fd=active.foeData,profile=contactProfiles[model];
 if(selected==='throw'){
  key=['victim_0','victim_0','victim_1','victim_2','victim_3','victim_5'][Math.min(p,5)];
  const native=fd[key],f={anchor:[native.ax,native.ay],scale:native.scale};
  const grip=sourcePoint(casterGrips[Math.min(p,5)],active.sourceFrames[p],actor);
  const q=profile.victim[Number(key.split('_')[1])];
  const attached=sourceAnchorFromPoint(q,f,grip,-1);
  if(time<32){[x,y]=attached;contact={caster:grip,target:sourcePoint(q,f,[x,y],-1),kind:'wrist'};}
  else {const rel=active.foeData.victim_2,rf={anchor:[rel.ax,rel.ay],scale:rel.scale};const releaseGrip=sourcePoint(casterGrips[3],active.sourceFrames[3],actor);const releaseRoot=sourceAnchorFromPoint(profile.victim[2],rf,releaseGrip,-1);const t=Math.min(1,(time-32)/10);x=releaseRoot[0]+170*t;y=releaseRoot[1]+(550-releaseRoot[1])*t-65*Math.sin(Math.PI*t);key=t<.6?'victim_3':'victim_5';if(t>=1)y=550;}
 }
 if(selected==='victim'){
  key='throw_'+[0,1,2,2,3,3][Math.min(p,5)];flip=-1;x=770;
  if(p<2){const native=fd[key],f={anchor:[native.ax,native.ay],scale:native.scale};const wrist=sourcePoint(victimWrists[p],active.sourceFrames[p],actor);const q=profile.throw[Number(key.split('_')[1])];[x,y]=sourceAnchorFromPoint(q,f,wrist,-1);contact={caster:sourcePoint(q,f,[x,y],-1),target:wrist,kind:'wrist'};}
 }
 if(selected==='Q'&&active.branch==='hit'&&time>=52){
  const hits=active.cinematic.hitTicks.filter(t=>t<=time),lastHit=hits.at(-1),dt=lastHit===undefined?999:time-lastHit;
  key=dt<10?'hurt_1':time>=132?'hurt_0':'victim_2';x=820+hits.length*15;y=dt<10?550-25*Math.sin(dt/10*Math.PI):time<132?495:550;
 }
 return{key,x,y,flip,contact}}
''' +s[end:]
start=s.index('function backdrop()');end=s.index('function render()',start)
s=s[:start]+'''function cinematicStage(){if(selected!=='Q'||active?.branch!=='hit')return null;const c=active.cinematic;if(time<c.cutin[0])return '确认';if(time<c.cutin[1])return '头像切入';if(time<c.charge[1])return '蓄势';if(time<c.sustain[0])return '释放';if(time<c.fade[0])return '持续冲击';if(time<c.fade[1])return '收束';return '恢复'}
function backdrop(){const stage=cinematicStage();if(!stage||['确认','恢复','头像切入'].includes(stage)||!$('fx').checked)return;
 const c=active.cinematic,a=stage==='收束'?Math.max(0,(c.fade[1]-time)/(c.fade[1]-c.fade[0])):stage==='蓄势'?(time-42)/10:1;
 ctx.save();ctx.globalAlpha=a;const g=ctx.createLinearGradient(0,0,0,550);g.addColorStop(0,'#090c24');g.addColorStop(1,'#33306b');ctx.fillStyle=g;ctx.fillRect(0,0,1200,545);
 ctx.strokeStyle='#aab8ea';ctx.lineWidth=2;ctx.beginPath();ctx.arc(920,155,66,0,Math.PI*2);ctx.stroke();ctx.strokeStyle='#7675b0';ctx.beginPath();ctx.moveTo(50,470);ctx.lineTo(1150,470);ctx.moveTo(50,485);ctx.lineTo(1150,485);ctx.stroke();
 ctx.strokeStyle='#aba6ed';ctx.lineWidth=3;for(let i=0;i<3;i++){const x=260+i*350;ctx.beginPath();ctx.moveTo(x,460);ctx.lineTo(x+18,410);ctx.lineTo(x-8,350);ctx.lineTo(x+25,290);ctx.stroke()}ctx.restore()}
function cutin(){const stage=cinematicStage();if(stage!=='头像切入'||!$('fx').checked||!portrait)return;const p=(time-12)/30,a=Math.min(1,p*5,(1-p)*5);ctx.save();ctx.globalAlpha=a;ctx.fillStyle='#11162fee';ctx.fillRect(0,100,1200,220);ctx.fillStyle='#7976b3';ctx.fillRect(0,100,1200,3);ctx.fillRect(0,317,1200,3);ctx.drawImage(portrait,140,110,200,200);ctx.fillStyle='#eeeaff';ctx.font='bold 38px system-ui';ctx.fillText('克洛琳德',390,200);ctx.font='24px system-ui';ctx.fillText('残光将终',390,245);ctx.restore()}
''' +s[end:]
s=s.replace("shadow(r[0],545);if(im&&f)pose(ctx,im,f,...r,$('mirror').checked?-1:1);", "ctx.save();if($('mirror').checked){ctx.translate(1200,0);ctx.scale(-1,1)}if($('body').checked){shadow(r[0],550);if(im&&f)pose(ctx,im,f,...r,1);}")
s=s.replace("fd=foe[s.key]", "fd=active.foeData[s.key]")
s=s.replace("}}stageFx(r);", "}if(s.contact&&$('anchors').checked){ctx.strokeStyle='#52e1ba';ctx.beginPath();ctx.arc(...s.contact.target,7,0,Math.PI*2);ctx.stroke()}}stageFx(r);")
start=s.index(" if(selected==='Q'&&time<14");end=s.index(" if($('anchors')",start)
s=s[:start]+s[end:]
s=s.replace(" ctx.fillStyle=$('background').value==='light'?'#47536a'", " ctx.restore();cutin();ctx.fillStyle=$('background').value==='light'?'#47536a'")
s=s.replace("branch:$('branch').value,root:r", "branch:active.branch,model:active.model,cinematicStage:cinematicStage(),contact:foeState(r).contact,root:r")
s=s.replace("fullStage:selected==='Q'&&$('branch').value==='hit'&&time>=14", "fullStage:selected==='Q'&&active.branch==='hit'&&time>=12&&time<142")
s=s.replace("const mode=$('material').value,branch=$('branch').value,short=", "const mode=$('material').value,branch=$('branch').value,model=$('enemyModel').value,foeData=window.CLORINDE_OPPONENT_MODELS[model],short=")
s=s.replace("Object.entries(foe).map", "Object.entries(foeData).map")
s=s.replace("material:mode,branch,images", "material:mode,branch,model,foeData,images")
s=s.replace("id==='material'||id==='branch'", "id==='material'||id==='branch'||id==='enemyModel'")
# Full stage is determined by committed branch, including gun/impact events.
s=s.replace("$('branch').value==='hit'", "active.branch==='hit'")
p.write_text(s,encoding='utf-8')
for name in ['player.html','index.html']:
 p=O/name;h=p.read_text(encoding='utf-8');h=h.replace('<label>Q分支', '<label>对手角色<select id="enemyModel"><option value="raiden">雷电将军</option><option value="nahida">纳西妲</option></select></label><label>Q分支');p.write_text(h,encoding='utf-8')
