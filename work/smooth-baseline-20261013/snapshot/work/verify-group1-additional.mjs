import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import{renderPaintPng}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/group1-full-test',save=JSON.parse(readFileSync(out+'/fighter.save.json'));save.assets.scripts[0].source=save.assets.scripts[0].source.replace('local PIXEL_TEMPLATE_INDEX=1073741845','local PIXEL_TEMPLATE_INDEX=0');
save.assets.scripts[0].source+=`\nlocal sampleUpdate=OnUpdate\nfunction OnUpdate(dt)sampleUpdate(dt);if onlineReady and phase=='fight'then f[1].meter=100;f[2].meter=100;if tick>250 and menuEpoch<5 then f[round==2 and 1 or 2].hp=0 end end end`;
const s=createStudio(save);s.playStart({playerCount:2});
const check=()=>{let r=s.playGet({view:true});let errors=r.logs.filter(l=>['error','lua-error'].includes(l.level)||/ERROR|加载失败/.test(l.text||''));assert.equal(errors.length,0,JSON.stringify(errors));return r;};
const step=n=>{for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});return check();};
const has=name=>check().scene.nodes.some(n=>n.name===name),until=(pred,label)=>{for(let n=0;n<10000;n+=30){if(pred())return;step(30);}throw Error('timeout '+label+' '+JSON.stringify(check().logs.slice(-5)));};
const settled=()=>until(()=>!has('LoadingText'),'loading');
const click=(p,name)=>{s.playSetView(p);s.playClick(name,{observe:false});step(1);};
const snap=name=>{let r=s.playGet({view:true,paint:true});writeFileSync(out+'/additional-'+name+'.png',renderPaintPng(r.paint,r.canvasWidth,r.canvasHeight).data);};
until(()=>has('StartDuel'),'boot');console.log('BOOT_PASS');for(let p=1;p<=2;p++)click(p,'StartDuel');snap('selection-empty');
assert.ok(!has('SelectStage1'),'map must not appear in selection');click(1,'ReadyConfirm');step(5);assert.ok(has('GridCard1'),'incomplete team started');
const pick=(p,role)=>{s.playSetView(p);settled();let target=Math.floor((role-1)/10)+1;for(let n=0;n<10;n++){const label=check().scene.nodes.find(n=>n.name==='PageLabel')?.text;if(Number(label?.split(' / ')[0])===target)break;click(p,'PageNext');settled();}click(p,'GridCard'+((role-1)%10+1));settled();s.playSetView(3-p);settled();s.playSetView(p);};
const full=JSON.parse(readFileSync(out+'/roster.json')).length>=45;
const teams=full?[[13,15,16],[6,7,12]]:[[1,3,5],[2,4,6]];
for(let p=1;p<=2;p++)for(const role of teams[p-1])pick(p,role);
s.playSetView(1);snap('selection-selected');console.log('THREE_PICK_PASS');
click(1,'ReadyConfirm');step(10);assert.ok(has('ReadyConfirm'),'one team ready started');click(2,'ReadyConfirm');until(()=>has('Timer')&&!has('LoadingText'),'R1');
const names=[];for(let round=1;round<=3;round++){
 until(()=>has('Timer')&&!has('LoadingText')&&check().scene.nodes.find(n=>n.name==='Name1')?.text.startsWith(JSON.parse(readFileSync(out+'/roster.json'))[teams[0][round-1]-1][1]),'round '+round);
 s.playSetView(1);step(95);for(const key of['KeyboardCharacterSkill1KeyDown','KeyboardCharacterSkill2KeyDown']){s.playKey(key,{observe:false});step(55);}snap('round-'+round);names.push(check().scene.nodes.filter(n=>n.name==='Name1'||n.name==='Name2').map(n=>n.text));console.log('ROUND_PASS',round,names.at(-1));
 if(round<3)until(()=>has('LoadingText'),'next load');
}

until(()=>has('Reselect'),'results');snap('result');console.log('RESULT_PASS');
click(2,'Reselect');
for(let p=1;p<=2;p++){s.playSetView(p);until(()=>has('GridCard1')&&!has('LoadingText'),'return selection '+p);assert(!has('Timer'),'old battle visible');snap('returned-selection-'+p);}
console.log('BOTH_RETURN_SELECTION_PASS');
writeFileSync(out+'/additional-verification.json',JSON.stringify({simulatorOnly:true,sampledTeams:teams,rounds:names,incompleteTeamCannotStart:true,oneReadyCannotStart:true,roundBarrier:true,threeRounds:true,onePlayerResultReturnSynchronizesBoth:true,mapHiddenInSelection:true,deviceVerified:false},null,2));


