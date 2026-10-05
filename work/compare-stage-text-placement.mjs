import fs from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
// Compare on-screen placement of training-room text rows between preset (074356) and runtime-created (C template) builds.
const outs=[JSON.parse(fs.readFileSync('work/training-room-mobile-fix-latest.json')).out,JSON.parse(fs.readFileSync('work/training-room-runtime-text-latest.json')).out];
const sample=n=>/^TextArt\d+$/.test(n.name);
function capture(out){
 const save=JSON.parse(fs.readFileSync(out+'/simulator.save.json'));
 save.assets.scripts[0].source+=`
local probeUpdate=OnUpdate
local probeStarted=false
function OnUpdate(dt)
 probeUpdate(dt)
 if not probeStarted and loadingState=='ready' then probeStarted=true;teamChoice={{1,3,5},{2,4,6}};roleChoice={1,2};menuMode='roundload';menuReady={true,true};menuLoaded={false,false};menuDirty=true;resourceGate.request('battle',roleChoice)end
 if probeStarted and loadingState=='ready' and menuMode=='roundload' then menuMode='battle';menuDirty=true;menuDraw()end
end`;
 const s=createStudio(save);s.playStart({canvasId:'mobile-19.5-9'});
 for(let i=0;i<40000;i+=20){for(let k=0;k<20;k++)s.playStep(1/60,{observe:false});const r=s.playGet({view:true});if(r.scene.nodes.some(n=>n.name==='Timer')&&!r.scene.nodes.some(n=>n.name==='LoadingBar'))break;}
 for(let k=0;k<10;k++)s.playStep(1/60,{observe:false});
 const r=s.playGet({view:true});s.playStop();
 const byId=new Map(r.scene.nodes.map(n=>[n.id,n]));
 const underStage=n=>{let p=byId.get(n.parent);while(p){if(p.name==='CountryStage')return true;p=byId.get(p.parent);}return false;};
 const rows=new Map();for(const n of r.scene.nodes)if(sample(n)&&underStage(n))rows.set(n.name,{tx:n.matrix.tx,ty:n.matrix.ty,a:n.matrix.a,d:n.matrix.d,text:n.text});
 return rows;
}
const [preset,runtime]=outs.map(capture);
assert(preset.size>10000&&runtime.size===preset.size,`row counts ${preset.size} vs ${runtime.size}`);
let maxDelta=0,textMismatch=0;
for(const [name,a] of preset){const b=runtime.get(name);assert(b,'missing '+name);maxDelta=Math.max(maxDelta,Math.abs(a.tx-b.tx),Math.abs(a.ty-b.ty),Math.abs(a.a-b.a),Math.abs(a.d-b.d));if(a.text!==b.text)textMismatch++;}
const result={simulatorOnly:true,preset:outs[0],runtime:outs[1],rows:preset.size,maxMatrixDelta:maxDelta,textMismatch};
fs.writeFileSync(outs[1]+'/stage-placement-compare.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
assert(maxDelta<1e-6&&textMismatch===0);
