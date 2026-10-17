import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace('cpu={2,2}','cpu={false,false}');
project.assets.scripts[0].source+=`
local originalUpdate=OnUpdate;local checked=false;local age=0;local which=1
function OnUpdate(dt)
 originalUpdate(dt)
 if app and app.sceneName=='fight' and app.scene.state=='run' then
 local scene=app.scene;local sim=scene.sim;local S=require('gf_sim')
 if not checked then
 checked=true
 local R=require('gf_roster');local by={};for _,c in ipairs(R) do by[c.key]=c end
 for id=1,2 do for _,wall in ipairs({-1,0,1}) do
  local s=S.new({chars={by.raidenshogun,by.nahida},time=99});s.phase='fight';s.phaseT=0
  for _,f in ipairs(s.f) do s:setState(f,'idle');f.invul=0 end
  local p,d=s.f[id],s.f[3-id];p.x=wall==0 and 0 or wall*(S.WALL-20000);p.face=id==1 and 1 or -1;d.x=p.x+p.face*14000
  s:step(0,0);s:tryThrow(p);assert(p.state=='throw','cannot grab at ordinary contact distance')
  local hits=0;local peak=0
  for i=1,150 do s:step(0,0);peak=math.max(peak,d.y);for _,e in ipairs(s.events) do if e.kind=='throw' then hits=hits+1 end end;assert(math.abs(d.x)<=S.WALL,'throw crossed wall') end
  assert(hits==1 and d.maxhp-d.hp==90 and d.state=='idle','throw impact/getup');assert(peak>=14000,'lift invisible')
 end end
 print('THROW PASS both characters; normal 140-unit contact; both walls; one impact; Raiden lift/Nahida assistant launch; getup')
 end
 local p,d=sim.f[which],sim.f[3-which]
 if age==0 then
 sim.phase='fight';sim.phaseT=0;for _,f in ipairs(sim.f) do sim:setState(f,'idle');f.invul=0;f.hp=f.maxhp;f.y=0;f.vx=0;f.vy=0 end
 p.x=0;p.face=which==1 and 1 or -1;d.x=p.x+p.face*14000;d.face=-p.face;sim:tryThrow(p);scene:events()
 end
 age=age+1
 if age==7 then assert(d.state=='thrown');print('THROWSHOT '..which..'-grab') end
 if age==21 then assert(d.state=='thrown');if which==1 then assert(d.y>9000,'victim lift missing') else assert(d.y==0,'assist throw must not physically lift before impact') end;print('THROWSHOT '..which..'-lift') end
 if age==55 then assert(d.hp==d.maxhp-90);print('THROWSHOT '..which..'-slam') end
 if age==155 then
 assert(d.state=='idle');if which==1 then which=2;age=0 else print('THROW DONE');age=156 end
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
 await call('import',{format:'json',filename:'r20.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});
 await call('play',{action:'start'});await call('play',{action:'pause'});
 const saved=new Set();
 for(let i=0;i<1400;i++){
  await call('play',{action:'step',args:{dt:1/60,light:true}});
  const snap=await observe();
  for(const log of logs.filter(l=>l.text.startsWith('THROWSHOT'))){
   if(saved.has(log.text))continue;saved.add(log.text);
   fs.mkdirSync('verification/throw-cinema',{recursive:true});fs.writeFileSync('verification/throw-cinema/'+log.text.split(' ')[1]+'.png',renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight).data);
  }
  if(logs.some(l=>l.text==='THROW DONE'))break;
 }
 assert(logs.some(l=>l.text.startsWith('THROW PASS')),JSON.stringify(logs.slice(-5)));assert(saved.size===6,JSON.stringify(logs));
 fs.writeFileSync('verification/throw-cinema/report.json',JSON.stringify({release:'nahida-integrated-r25',checks:logs.filter(l=>l.text.startsWith('THROW')).map(l=>l.text),method:'Actual bundled Lua Worker; CPU rendering'},null,2));
 console.log(logs.filter(l=>l.text.startsWith('THROW')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
