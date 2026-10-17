import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source+=`
local oldUpdate=OnUpdate;local age=0;local hold={};local baseCreated;local checked=false;local releaseDone=false;local firstDone=false;local destroyBaseline=0
function OnUpdate(dt)
 oldUpdate(dt)
 if app and app.sceneName=='fight' and app.scene.state=='run' then
 local scene=app.scene;local sim=scene.sim;local G=require('gf_gfx');age=age+1;scene.endT=0
 if not checked then
  checked=true;scene.ai={nil,nil};sim.phase='fight';sim.phaseT=0
  for _,p in ipairs(sim.f) do sim:setState(p,'idle');p.invul=0;p.energy=0 end
  local stat=G.secondPoolStatus();assert(stat.floor==14000 and stat.total==14000)
  baseCreated=stat.created
  while G.secondPoolStatus().freeFirst+G.secondPoolStatus().freeSecond>1800 do local n=G.image(G.root,G.RECT);n:size(0,0):on(true);hold[#hold+1]=n end
 end
 local stat=G.secondPoolStatus()
 assert(stat.total>=stat.floor,'capacity below baseline')
 if age==2 then assert(stat.created>baseCreated and stat.warnings>0,'warning did not create immediately');print('DYNAMIC WARNING immediate creation total='..stat.total) end
 if age==105 then
  assert(stat.total>14000 and stat.destroyed==0,'destroyed inside fight')
  for _,n in ipairs(hold) do G.release(n) end;hold={};releaseDone=true
 end
 if releaseDone and sim.phase=='fight' then assert(stat.destroyed==destroyBaseline,'idle surplus destroyed during battle total='..stat.total..' destroyed='..stat.destroyed..' baseline='..destroyBaseline) end
 if age==190 then
  print('DYNAMIC PREEND total='..stat.total..' free='..(stat.freeFirst+stat.freeSecond)..' destroyed='..stat.destroyed)
  assert(stat.destroyed==0,'fight shrink');sim:roundOver(1,'test');scene:events()
 end
 if age>300 and stat.destroyed>0 and not firstDone then
  firstDone=true;destroyBaseline=stat.destroyed;print('DYNAMIC ROUND reclaimed='..stat.destroyed..' total='..stat.total)
  -- Verify remaining pool nodes are live and can be reused after actual destruction.
  for i=1,180 do hold[#hold+1]=G.image(G.root,G.RECT) end
  for _,n in ipairs(hold) do G.release(n) end;hold={}
  sim.phase='fight';sim.phaseT=0;for _,p in ipairs(sim.f) do sim:setState(p,'idle');p.invul=0 end
  sim.f[1].energy=100;assert(sim:startBurst(sim.f[1]));scene:events()
 end
 if firstDone and age==720 then
  assert(stat.destroyed==destroyBaseline,'battle destroyed after restart')
  sim.phase='over';sim:emit({type='matchEnd',winner=1});scene:events()
 end
 if firstDone and age>950 then
  assert(stat.total>=14000 and stat.total<=14064,'match boundary did not reclaim surplus total='..stat.total..' free='..(stat.freeFirst+stat.freeSecond)..' pending='..G.pending()..' destroyed='..stat.destroyed)
  assert(stat.destroyed>destroyBaseline,'match-end cleanup not triggered')
  print('DYNAMIC MATCH reclaimed='..stat.destroyed..' total='..stat.total)
  print('DYNAMIC PASS immediate warning; zero fight destroys; round and match cleanup; baseline intact; reused nodes; burst after cleanup');age=-999999
 end
 end
end
`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>l.level==='error'||l.level==='lua-error');assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{
 await call('import',{format:'json',filename:'r19.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});
 await call('play',{action:'start'});await call('play',{action:'pause'});
 for(let i=0;i<2400;i++){
  await call('play',{action:'step',args:{dt:1/20,light:true}});
  if(i%10)continue;await observe();
  if(logs.some(l=>l.text.startsWith('DYNAMIC PASS')))break;
 }
 assert(logs.some(l=>l.text.startsWith('DYNAMIC PASS')),JSON.stringify(logs.slice(-5)));
 const snap=await observe();const png=renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight);
 fs.mkdirSync('verification/dynamic-pool',{recursive:true});fs.writeFileSync('verification/dynamic-pool/battle.png',png.data);
 fs.writeFileSync('verification/dynamic-pool/report.json',JSON.stringify({release:'dual-inbetweens-r28',checks:logs.filter(l=>l.text.startsWith('DYNAMIC')).map(l=>l.text),method:'Actual bundled Lua Worker; CPU rendering'},null,2));
 console.log(logs.filter(l=>l.text.startsWith('DYNAMIC')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
