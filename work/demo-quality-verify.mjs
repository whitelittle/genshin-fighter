import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const traces=[];
for(const profile of ['fine','standard','light','compatible','minimum']){
 const save=JSON.parse(readFileSync(`outputs/demo-solo-${profile}/fighter.save.json`));
 save.assets.scripts[0].source+=`\nlocal priorStart=OnStart\nfunction OnStart()priorStart();aiEnabled=false;f[1].x=-40;f[2].x=40;f[1].meter=100;draw()end\nlocal priorDraw=draw\ndraw=function()priorDraw();local v={tick,phase,remaining,freeze};for i=1,2 do for _,k in ipairs({'x','y','vy','hp','meter','role','stun','down','wake','airHits','comboDamage'})do v[#v+1]=f[i][k]end;v[#v+1]=f[i].attack and f[i].attack.kind or 'none';v[#v+1]=f[i].attack and f[i].attack.t or 0 end;stats.text=table.concat(v,'|')end`;
 const s=createStudio(save);s.playStart();const trace=[];
 for(let q=0;q<2;q++)for(const k of ['KeyboardMoveBackwardKeyDown','KeyboardMoveRightKeyDown','KeyboardMoveBackwardKeyUp','KeyboardMoveRightKeyUp'])s.playKey(k,{observe:false});s.playKey('KeyboardCraftspersonKey20Down',{observe:false});s.playKey('KeyboardCraftspersonKey20Up',{observe:false});
 for(let n=0;n<35;n++){s.playStep(1/30,{observe:false});if(n%5===0){const r=s.playGet({view:true});assert.equal(r.logs.filter(l=>['error','lua-error'].includes(l.level)).length,0);trace.push(r.scene.nodes.find(n=>n.name==='Stats').text);}}
 if(traces.length)assert.deepEqual(trace,traces[0].trace,'combat changed across '+profile);traces.push({profile,trace});
}
writeFileSync('assets/demo/quality-verification.json',JSON.stringify({simulatorVerified:true,deviceVerified:false,tests:{fiveProfilesRuntimeBoot:true,identicalCombatTrace:true},traces},null,2));console.log('All five profiles have identical combat traces');
