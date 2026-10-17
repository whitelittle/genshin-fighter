import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace('cpu={2,2}','cpu={false,false}');
project.assets.scripts[0].source+=`
local prev=OnUpdate;local phase=0;local age=0;local numbers=0;local dmg=0;local beginning;local poolBefore
function OnUpdate(dt)
 prev(dt)
 if not app then return end
 if app.qualityLoad and app.qualityLoad.target=='lo' then debugLow=(debugLow or 0)+1;if debugLow%50==0 then local p=G.secondPoolStatus();print('LOW POOL '..p.total..' free='..(p.freeFirst+p.freeSecond)..' target='..p.target..' pending='..G.pending()..' retiring='..tostring(p.retiring)) end end
 if phase==0 and app.sceneName=='fight' and app.scene.state=='run' then
  local R=require('gf_roster');assert(#R==2 and R[1].key=='raidenshogun' and R[2].key=='nahida','roster');assert(app.quality=='lo','default quality');assert(#app.scene.stage.sway>0,'grass fixture missing')
  app:go('options');app.scene.menu:input({'right'});assert(app.qualityLoad);assert(app.qualityLoad and app.sceneName=='quality_loading');phase=1;print('QUALITY LOADING')
 elseif phase==1 and not app.qualityLoad then
  assert(app.quality=='hi' and app.sceneName=='options');assert(G.secondPoolStatus().total>=24000 and G.secondPoolStatus().floor==24000,'HD pool prewarm');local A=require('gf_art');local hi=A.animation('nahida','hi','basic_0');local lo=A.animation('nahida','lo','basic_0');assert(hi.n>lo.n,'high fit not finer')
  print('QUALITY HIGH PASS preallocated=24000');app:go('fight',{chars={'raidenshogun','nahida'},mode='versus',cpu={false,false},time=99});phase=8
 elseif phase==8 and app.scene.state=='run' then app:go('options');app.scene.menu:input({'left'});phase=4;print('POOL RETIRE AFTER HD FIGHT')
 elseif phase==2 and app.scene.state=='run' then
  local sc=app.scene;local S=require('gf_sim');local sim=sc.sim;sim.phase='fight';sim.phaseT=0
  for _,f in ipairs(sim.f) do sim:setState(f,'idle');f.invul=0;f.coat=0 end
  sim.f[1].x=0;sim.f[2].x=14000;sim.f[1].energy=100;beginning=sim.f[2].hp
  local original=sc.fx.number
  sc.fx.number=function(self,x,y,value,element,big,label,hold)
   if type(value)=='number' and value>0 and element=='dendro' then numbers=numbers+1;dmg=dmg+value;assert(big and hold==1.3,'burst number visibility');print('NAHIDA NUMBER '..value) end
   return original(self,x,y,value,element,big,label,hold)
  end
  poolBefore=G.secondPoolStatus();assert(sim:startBurst(sim.f[1]));sc:events();age=0;phase=3
 elseif phase==3 then
  age=age+1;for _,blade in ipairs(app.scene.stage.sway or {}) do assert(math.abs(blade.node.r-blade.base)<=5.006,'grass spins');local rad=math.rad(blade.node.r);assert(math.abs(blade.node.x+math.sin(rad)*blade.h/2-blade.x)<0.03,'grass root moves') end
  if age==130 then print('QUALITY SHOT') end
  if age>=240 then
   assert(G.secondPoolStatus().created==poolBefore.created,'ordinary HD burst grew pool');assert(numbers==3 and dmg==241,'Nahida displayed damage count');assert(beginning-app.scene.sim.f[2].hp==dmg,'health/number mismatch');print('NAHIDA VISIBLE PASS damage='..dmg)
   app:go('fight',{chars={'raidenshogun','nahida'},mode='versus',cpu={false,false},time=99});phase=6
  end
 elseif phase==6 and app.scene.state=='run' then
  local S=require('gf_sim');local sim=app.scene.sim;sim.phase='fight';sim.phaseT=0
  for _,f in ipairs(sim.f) do sim:setState(f,'idle');f.invul=0;f.coat=0 end
  sim.f[1].x=0;sim.f[2].x=14000;sim.f[1].energy=100;assert(sim:startBurst(sim.f[1]));app.scene:events();age=0;phase=7
 elseif phase==7 then
  age=age+1
  if age==130 then print('RAIDEN HD SHOT') end
  if age>=250 then
   assert(app.scene.sim.f[1].state~='burst');assert(app.scene.burstEye.used>2000,'HD eye absent');print('RAIDEN HD PASS full burst and fitted eye without pool exhaustion')
   app:go('options');app.scene.menu:input({'left'});assert(app.qualityLoad);phase=4
  end
 elseif phase==4 and not app.qualityLoad then
  assert(app.quality=='lo' and G.secondPoolStatus().total==14000,'low pool did not shrink');local original=app.isMobile;app.isMobile=function() return true end;app:go('options')
  for _,it in ipairs(app.scene.items) do assert(it.id~='quality','mobile quality choice exposed') end
  assert(not app:setQuality('hi') and app:detectQuality()=='lo');app.isMobile=original
  print('QUALITY PASS default low, high 24000 prewarm, low shrink to 14000 before ready, mobile lock');phase=5
 elseif phase==5 then
  local B=require('gf_input').B;local held=app.input.pads[1].held
  if held==B.SK then print('KEY PASS I=E') elseif held==B.BU then print('KEY PASS O=Q') elseif held==B.TH then print('KEY PASS L=throw') end
 end
end
`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];const printed=new Set();async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>(l.level==='error'||l.level==='lua-error'));assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;for(const l of logs.filter(l=>l.text.startsWith('LOW POOL')))if(!printed.has(l.text)){printed.add(l.text);console.log(l.text)}return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{await call('import',{format:'json',filename:'raiden-nahida.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});await call('play',{action:'start'});await call('play',{action:'pause'});let captured=false;let raidenCaptured=false;
for(let i=0;i<160;i++){await step(10);await observe();if(!captured&&logs.some(l=>l.text==='QUALITY SHOT')){fs.mkdirSync('verification/quality-r31',{recursive:true});const snap=await observe();fs.writeFileSync('verification/quality-r31/nahida-hd-damage.png',renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight).data);captured=true;}if(!raidenCaptured&&logs.some(l=>l.text==='RAIDEN HD SHOT')){const snap=await observe();fs.writeFileSync('verification/quality-r31/raiden-hd-eye.png',renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight).data);raidenCaptured=true;}if(logs.some(l=>l.text.startsWith('QUALITY PASS')))break;}
assert(logs.some(l=>l.text.startsWith('QUALITY PASS')),JSON.stringify(logs.slice(-12)));
for(const [id,label] of [[16,'I=E'],[17,'O=Q'],[21,'L=throw']]){await call('play',{action:'key',args:{key:'KeyboardCraftspersonKey'+id+'Down'}});await step(1);await observe();assert(logs.some(l=>l.text==='KEY PASS '+label));await call('play',{action:'key',args:{key:'KeyboardCraftspersonKey'+id+'Up'}});await step(1);}
fs.writeFileSync('verification/quality-r31/pool-switch.json',JSON.stringify({method:'Actual split-file Lua Worker; HD fight construction, exit and quality downgrade with exact 14000 assertion',checks:logs.filter(l=>/QUALITY|NAHIDA|RAIDEN|KEY PASS/.test(l.text)).map(l=>l.text)},null,2));console.log(logs.filter(l=>/QUALITY|NAHIDA|RAIDEN|KEY PASS/.test(l.text)).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
