import{readFileSync as read,writeFileSync as write}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const results=[];
for(const out of['outputs/group1-full-test','outputs/test-repair-v1']){
 const save=JSON.parse(read(out+'/fighter.save.json'));let code=save.assets.scripts[0].source.replace('PIXEL_TEMPLATE_INDEX=1073741845','PIXEL_TEMPLATE_INDEX=0');
 code=code.replace('local loadingPrefabIndex=nil','local loadingPrefabIndex=nil\nresourceGate.benchmark={created=0,destroyed=0,decoded=0}');
 code=code.replace('loadingInstances[j][n]=box','loadingInstances[j][n]=box;resourceGate.benchmark.created=resourceGate.benchmark.created+1');
 code=code.replace('game.DestroyClientUIControl(loadingInstances[j][n]);','resourceGate.benchmark.destroyed=resourceGate.benchmark.destroyed+1;game.DestroyClientUIControl(loadingInstances[j][n]);');
 code=code.replace('local done=unpackWork(frame);','local done=unpackWork(frame);resourceGate.benchmark.decoded=resourceGate.benchmark.decoded+1;');
 code=code.replace("loadingState='ready';loadingOverlay:SetVisible(false);menuDraw()", "print('[BENCH] '..resourceGate.benchmark.created..','..resourceGate.benchmark.destroyed..','..resourceGate.benchmark.decoded);loadingState='ready';loadingOverlay:SetVisible(false);menuDraw()");
 save.assets.scripts[0].source=code;const s=createStudio(save);s.playStart({playerCount:2});let steps=0;
 const get=()=>{const r=s.playGet({view:true});assert(!r.logs.some(l=>['error','lua-error'].includes(l.level)||/ERROR/.test(l.text||'')),JSON.stringify(r.logs.slice(-5)));return r;};
 const advance=()=>{steps++;s.playStep(1/60,{observe:false});};
 const settle=()=>{for(let i=0;i<10000;i++){if(!get().scene.nodes.some(n=>n.name==='LoadingText'))return;advance();}throw Error('load timeout');};
 const click=n=>{s.playClick(n,{observe:false});advance();settle();};
 const totals=()=>get().logs.filter(l=>l.text?.startsWith('[BENCH]')).at(-1).text.slice(8).split(',').map(Number);
 settle();click('StartDuelHit');const before=totals(),begin=steps;
 for(const role of[3,8,5,5,8,8,8])click('GridCard'+role);
 const after=totals();results.push({variant:out,route:'same-page select 3,8,5; retract 5,8; select/retract 8',created:after[0]-before[0],destroyed:after[1]-before[1],decodeWork:after[2]-before[2],simulatedUpdateCount:steps-begin,realDevice:false});s.playStop();console.log(results.at(-1));
}
assert(results[1].destroyed<results[0].destroyed,'pool reuse did not reduce repeated preview destruction');write('outputs/test-repair-v1/loading-comparison.json',JSON.stringify({scope:'same selection path, excludes new scene and startup; simulated update count is not phone timing',results},null,2));
