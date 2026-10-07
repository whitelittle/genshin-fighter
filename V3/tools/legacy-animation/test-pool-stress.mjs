import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source+=`
local oldUpdate=OnUpdate;local age=0;local matches=0;local hits=0;local bursts=0;local checked=false;local poolPeak=0;local savedPeak=0
function OnUpdate(dt)
 oldUpdate(dt)
 if app and app.sceneName=='fight' and app.scene.state=='run' then
  local scene=app.scene;local sim=scene.sim;local G=require('gf_gfx');age=age+1
  if not checked then checked=true;scene.endT=0;print('POOL START total='..G.counts.img) end
  for _,e in ipairs(sim.events) do if e.type=='hit' then hits=hits+1 end;if e.type=='burst' then bursts=bursts+1 end end
  poolPeak=math.max(poolPeak,G.counts.peakImg)
  -- Exercise both bursts back-to-back after each restart, plus full rendered AI matches.
  if sim.phase=='fight' and sim.tick%450==100 then sim.f[1].energy=100;sim.f[2].energy=100 end
  if sim.phase=='over' then
   matches=matches+1;scene.endT=0;sim.round=1;for _,p in ipairs(sim.f) do p.wins=0 end;sim:startRound(false)
   if matches>=3 then assert(hits>30 and bursts>=4,'missing live combat');print('POOL PASS matches='..matches..' renderFrames='..age..' hits='..hits..' bursts='..bursts..' peak='..poolPeak..' total='..G.counts.img);age=-999999 end
  end
  if age%1000==0 then print('POOL LIVE frames='..age..' peak='..poolPeak..' total='..G.counts.img) end
  assert(#scene.banners<=1,'stacked round titles');assert(G.counts.img>=14000,'fight pool not expanded')
  scene.endT=0
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
 for(let i=0;i<28000;i++){
  await call('play',{action:'step',args:{dt:1/20,light:true}});
  if(i%160)continue;await observe();
  if(logs.some(l=>l.text.startsWith('POOL PASS')))break;
 }
 assert(logs.some(l=>l.text.startsWith('POOL PASS')),JSON.stringify(logs.slice(-5)));
 const snap=await observe();const png=renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight);
 fs.mkdirSync('verification/pool-stress',{recursive:true});fs.writeFileSync('verification/pool-stress/battle.png',png.data);
 fs.writeFileSync('verification/pool-stress/report.json',JSON.stringify({release:'nahida-preview-pool-r23',checks:logs.filter(l=>l.text.startsWith('POOL')).map(l=>l.text),method:'Actual bundled Lua Worker; CPU rendering'},null,2));
 console.log(logs.filter(l=>l.text.startsWith('POOL')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
