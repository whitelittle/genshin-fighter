import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace('cpu={2,2}','cpu={false,false}');
project.assets.scripts[0].source+=`
local originalUpdate=OnUpdate;local checked=false;local age=0
function OnUpdate(dt)
 originalUpdate(dt)
 if app and app.sceneName=='fight' and app.scene.state=='run' then
 local scene=app.scene;local sim=scene.sim;local S=require('gf_sim')
 if not checked then
  checked=true;assert(GF_RELEASE_ID=='nahida-pixel-viewfinder-r27','wrong simulator release')
  local R=require('gf_roster');local by={};for _,c in ipairs(R) do by[c.key]=c end
  local function fresh()
   local s=S.new({chars={by.raidenshogun,by.nahida},time=99});s.phase='fight';s.phaseT=0
   for _,f in ipairs(s.f) do s:setState(f,'idle');f.invul=0 end
   s.f[2].x=0;s.f[2].face=1;s.f[1].x=50000;s.f[1].face=-1;return s
  end
  for _,mode in ipairs({'hit','guard','evade'}) do
   local s=fresh();local p,d=s.f[2],s.f[1];assert(s:startSkill(p));assert(p.move.style=='capture')
   if mode=='evade' then d.x=100000 end
   local hits,blocks,first=0,0,0
   for i=1,110 do s:step(mode=='guard' and S.B.R or 0,0);for _,e in ipairs(s.events) do if e.type=='hit' and e.by==2 then hits=hits+1;first=i elseif e.type=='block' and e.by==2 then blocks=blocks+1 end end end
   if mode=='hit' then assert(hits==1 and first>=8 and first<=13 and d.hp<d.maxhp,'fast frame strike ranged impact') elseif mode=='guard' then assert(hits==0 and blocks==1,'capture guard') else assert(hits==0 and blocks==0,'reticle should miss escaped target') end
  end
  for _,side in ipairs({-1,1}) do
   local s=fresh();local p,d=s.f[2],s.f[1];p.x=0;p.face=side;d.x=side*50000;s:startSkill(p);local hits=0
   for i=1,80 do s:step(0,0);for _,e in ipairs(s.events) do if e.type=='hit' and e.by==2 then hits=hits+1;assert(p.captureHitT<=13 and p.hitstop>=10,'impact/frame pause mismatch') end end end
   assert(hits==1 and d.state=='idle','directional frame strike/recovery')
  end
  local s=fresh();local p,d=s.f[2],s.f[1];s:startSkill(p);d.x=-50000;for i=1,80 do s:step(0,0) end;assert(d.hp==d.maxhp,'frame must not home behind caster')
  print('NAHIDA PASS r27; E impact by frame 13, single hit/guard/escape; both directions; hitstop; no homing; native hover')
 end
 local p,d=sim.f[2],sim.f[1]
 if age==0 or age==130 or age==470 then
  sim.phase='fight';sim.phaseT=0;for _,f in ipairs(sim.f) do sim:setState(f,'idle');f.invul=0;f.hp=f.maxhp;f.ko=false;f.y=0;f.vx=0;f.vy=0;f.hitstop=0 end
  p.x=0;p.face=1;d.x=age==0 and 50000 or 14000;d.face=-1
  if age==0 then p.skillCd=0;sim:startSkill(p) elseif age==130 then p.energy=100;sim:startBurst(p) else sim:tryThrow(p) end
  scene:events()
 end
 age=age+1
 if age==12 then print('NAHIDASHOT e-flight') end
 if age==20 then assert(scene.views[2].captureBmp.used>0,'native sprite not drawn');print('NAHIDASHOT e-impact') end
 if age==90 then assert(scene.views[2].oy>20,'Nahida hover not applied to live view');print('NAHIDASHOT hover') end
 if age==225 then print('NAHIDASHOT q-domain') end
 if age==255 then print('NAHIDASHOT q-final') end
 if age==495 then print('NAHIDASHOT assistants') end
 if age==545 then print('NAHIDASHOT launched') end
 if age==680 then print('NAHIDA DONE') end
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
  for(const log of logs.filter(l=>l.text.startsWith('NAHIDASHOT'))){
   if(saved.has(log.text))continue;saved.add(log.text);
   fs.mkdirSync('verification/nahida-pixel-viewfinder',{recursive:true});fs.writeFileSync('verification/nahida-pixel-viewfinder/'+log.text.split(' ')[1]+'.png',renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight).data);
  }
  if(logs.some(l=>l.text==='NAHIDA DONE'))break;
 }
 assert(logs.some(l=>l.text.startsWith('NAHIDA PASS')),JSON.stringify(logs.slice(-5)));assert(saved.size===7,JSON.stringify(logs));
 fs.writeFileSync('verification/nahida-pixel-viewfinder/report.json',JSON.stringify({release:'nahida-pixel-viewfinder-r27',checks:logs.filter(l=>l.text.startsWith('NAHIDA')).map(l=>l.text),method:'Actual bundled Lua Worker; CPU rendering'},null,2));
 console.log(logs.filter(l=>l.text.startsWith('NAHIDA')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
