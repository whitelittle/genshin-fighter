import{readFileSync,writeFileSync}from'node:fs';import{execFileSync}from'node:child_process';import assert from'node:assert/strict';
const target=process.env.REPAIR_OUT||'outputs/test-repair-v1';
let code=readFileSync('work/verify-roster-v2.mjs','utf8').replace("const out='outputs/roster-v2'",`const out='${target}'`);
code=code.replace('[[12,24,27],[11,41,32]]','[[3,8,5],[4,11,17]]');
if(target.includes('midphase-final'))code=code.replace("const teams=full?[[3,8,5],[4,11,17]]:[[1,3,5],[2,4,6]];",'const teams=[[14,19,8],[18,11,13]];');
code=code.replace("s.playClick(name,{observe:false});step(1);", "const r=check(),n=r.scene.nodes.find(n=>n.name===name);assert.ok(n,name);let x=0,y=0,node=n;while(node){x=node.matrix.a*x+node.matrix.c*y+node.matrix.tx;y=node.matrix.b*0+node.matrix.d*y+node.matrix.ty;node=r.scene.nodes.find(m=>m.id===node.parent);}s.playPointer('click',x,y,{observe:false});step(1);");
code=code.replace("console.log('BOOT_PASS');", "settled();snap('home-fullscreen');console.log('BOOT_PASS');");
code=code.replace("snap('selection-empty');", "settled();snap('selection-empty');");
code=code.replace('const names=[];', 'const stageNames=[];const names=[];');
code=code.replace("snap('round-'+round);names.push", "snap('round-'+round);const name=check().scene.nodes.find(n=>n.name==='StageTitle').text;stageNames.push(name);s.playSetView(2);until(()=>has('Timer')&&!has('LoadingText'),'peer stage');assert.equal(check().scene.nodes.find(n=>n.name==='StageTitle').text,name,'stage must match on both clients');s.playSetView(1);names.push");
const begin=code.indexOf("until(()=>has('Rematch'),'results');");assert(begin>0);
code=code.slice(0,begin)+`
until(()=>has('Reselect'),'results');snap('result');console.log('RESULT_PASS');
click(2,'Reselect');
for(let p=1;p<=2;p++){s.playSetView(p);until(()=>has('GridCard1')&&!has('LoadingText'),'return selection '+p);assert(!has('Timer'),'old battle visible');snap('returned-selection-'+p);}
console.log('BOTH_RETURN_SELECTION_PASS');
writeFileSync(out+'/load-metrics.json',JSON.stringify(check().logs.filter(l=>/LOAD METRIC|RESOURCE/.test(l.text||'')),null,2));
assert.equal(new Set(stageNames).size,3,'three country scenes must not repeat');
writeFileSync(out+'/verification.json',JSON.stringify({simulatorOnly:true,sampledTeams:teams,rounds:names,stageNames,threeDifferentSynchronizedStages:true,incompleteTeamCannotStart:true,oneReadyCannotStart:true,roundBarrier:true,threeRounds:true,onePlayerResultReturnSynchronizesBoth:true,mapHiddenInSelection:true,deviceVerified:false},null,2));
`;
writeFileSync('work/verify-test-repair-generated.mjs',code);execFileSync(process.execPath,['work/verify-test-repair-generated.mjs'],{stdio:'inherit'});

