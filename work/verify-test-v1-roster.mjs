import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
import{renderPaintPng}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/host-png.js';
const out='outputs/test-v1',save=JSON.parse(readFileSync(out+'/fighter.save.json'));save.assets.scripts[0].source=save.assets.scripts[0].source.replace('local PIXEL_TEMPLATE_INDEX=1073741845','local PIXEL_TEMPLATE_INDEX=0');
const roster=JSON.parse(readFileSync(out+'/roster.json')),checks=[];
const check=s=>{const r=s.playGet({view:true});const e=r.logs.filter(l=>['error','lua-error'].includes(l.level)||/ERROR|失败/.test(l.text||''));assert.equal(e.length,0,JSON.stringify(e));return r;};
const step=(s,n)=>{for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});return check(s);};
const click=(s,p,name)=>{s.playSetView(p);s.playClick(name,{observe:false});};
const until=(s,name)=>{for(let n=0;n<1800;n+=30){if(check(s).scene.nodes.some(n=>n.name===name))return;step(s,30);}assert.fail('timeout '+name);};
for(let role=1;role<=roster.length;role++){
 const fixture=structuredClone(save);fixture.assets.scripts[0].source+='\nlocal rosterUpdate=OnUpdate\nfunction OnUpdate(dt)rosterUpdate(dt);if onlineReady and phase==\'fight\' then f[1].meter=100;f[2].meter=100 end end';
 const s=createStudio(fixture);s.playStart({playerCount:2});until(s,'StartDuel');for(let p=1;p<=2;p++){click(s,p,'StartDuel');click(s,p,'ChooseRole'+role);click(s,p,'ReadyConfirm');}until(s,'Timer');step(s,100);
 const r=check(s);assert.ok(r.scene.nodes.some(n=>n.name==='Name1'&&n.text.startsWith(roster[role-1][1])),'wrong roster '+role);
 s.playSetView(1);for(const[key,n]of[['KeyboardCraftspersonKey19Down',35],['KeyboardCharacterSkill1KeyDown',75],['KeyboardCharacterSkill2KeyDown',80],['KeyboardJumpKeyDown',50]]){s.playKey(key,{observe:false});step(s,n);}
 s.playKey('KeyboardCraftspersonKey15Down',{observe:false});step(s,1);assert.ok(check(s).scene.nodes.some(n=>n.name==='CommandBody'),'H failed');
 if([3,5,9,10,11].includes(role)){s.playKey('KeyboardCraftspersonKey15Down',{observe:false});step(s,1);const v=s.playGet({view:true,paint:true});writeFileSync(out+'/role-'+role+'.png',renderPaintPng(v.paint,v.canvasWidth,v.canvasHeight).data);}
 checks.push({role:roster[role-1][1],selectBoth:true,light:true,E:true,Q:true,jump:true,H:true});console.log('ROSTER_PASS '+roster[role-1][1]);
}
writeFileSync(out+'/roster-verification.json',JSON.stringify({simulatorOnly:true,checks},null,2));
// Exercise results/rematch with deterministic KO fixture; one vote cannot start a new match.
const fixture=structuredClone(save);fixture.assets.scripts[0].source+='\nlocal resultUpdate=OnUpdate\nfunction OnUpdate(dt)resultUpdate(dt);if onlineReady and menuEpoch==1 and phase==\'fight\' then f[2].hp=0 end end';
const s=createStudio(fixture);s.playStart({playerCount:2});until(s,'StartDuel');for(let p=1;p<=2;p++){click(s,p,'StartDuel');click(s,p,'ReadyConfirm');}until(s,'Rematch');
assert.ok(check(s).scene.nodes.some(n=>n.name==='Rematch'));click(s,1,'Rematch');step(s,10);assert.ok(check(s).scene.nodes.some(n=>n.name==='Rematch'),'one rematch vote started');click(s,2,'Rematch');step(s,240);assert.ok(!check(s).scene.nodes.some(n=>n.name==='Rematch')&&check(s).scene.nodes.some(n=>n.name==='Timer'),'both rematch failed');
writeFileSync(out+'/result-verification.json',JSON.stringify({simulatorOnly:true,twoWins:true,oneVoteWaits:true,bothRematch:true},null,2));console.log('RESULT_PASS');
