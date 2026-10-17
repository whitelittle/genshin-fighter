import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source+=`
local prev=OnUpdate;local phase=0;local frames=0;local seen={}
local function press(action) app.input.menuQ[#app.input.menuQ+1]=action end
function OnUpdate(dt)
 prev(dt);if not app or not app.sceneName or not app.scene then return end
 local name,sc=app.sceneName,app.scene
 if not seen[name] then seen[name]=true;print('FLOW SCENE '..name) end
 if app.trans then return end
 if phase==0 and name=='title' and sc.t>.7 then press('ok');phase=1
 elseif phase==1 and name=='menu' then
  assert(#require('gf_roster')==2);sc.menu.sel=2;press('ok');phase=2
 elseif phase==2 and name=='menu' and sc.sub=='versus' then
  assert(sc.items[1].id=='vcpu' and sc.items[2].id=='online');press('ok');phase=3
 elseif phase==3 and name=='select' and sc.built==2 then
  press('ok');phase=4
 elseif phase==4 and name=='select' and sc.done[1] then press('ok');phase=5
 elseif phase==5 and name=='select' and sc.phase=='stage' then press('ok');phase=6
 elseif phase==6 and name=='fight' and sc.state=='run' then
  assert(sc.ai[1]==nil and sc.ai[2]~=nil,'single player control');sc.sim.winsNeeded=1
  local p,d=sc.sim.f[1],sc.sim.f[2];sc.sim:setState(d,'idle');d.invul=0;d.hp=1;sc.sim:hit(p,d,{damage=1000,hitstun=30,push=0},'heavy',{unblockable=true,ignoreInvul=true});sc:events();phase=7
 elseif phase==7 and name=='result' then
  assert(sc.menu.items[1].id=='again' and sc.menu.items[2].id=='select');press('ok');phase=8
 elseif phase==8 and name=='fight' and sc.state=='run' then
  assert(sc.sim.f[2].hp==sc.sim.f[2].maxhp and not sc.sim.f[2].ko,'rematch stale state');print('FLOW REMATCH PASS')
  sc:openPause();sc:pausePick('select');phase=9
 elseif phase==9 and name=='select' and sc.built==2 then
  assert(sc.mode=='versus');press('back');phase=10;print('FLOW RESELECT PASS')
 elseif phase==10 and name=='menu' then sc.menu.sel=2;press('ok');phase=11
 elseif phase==11 and name=='menu' and sc.sub=='versus' then sc.menu.sel=2;press('ok');phase=12
 elseif phase==12 and name=='online' then
  assert(sc.net and sc.net.io and sc.net.io.diag,'archived GFV2 missing');frames=frames+1
  if frames>=70 then assert(sc.net.io.diag.hello>=1,'GFV2 handshake not sent');press('back');phase=13;print('FLOW ONLINE PASS GFV2 lobby and handshake') end
 elseif phase==13 and name=='menu' then
  print('GFTEST PASS complete intro/title/menu/select/stage/VS/human fight/result/rematch/reselect/GFV2 lobby/menu');phase=14
 end
end
`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>(l.level==='error'||l.level==='lua-error'));assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{await call('import',{format:'json',filename:'raiden-nahida.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});await call('play',{action:'start'});await call('play',{action:'pause'});for(let i=0;i<350;i++){await step(10);await observe();if(logs.some(l=>l.text.includes('GFTEST PASS complete')))break;}let s=await observe();assert(logs.some(l=>l.text.includes('GFTEST PASS')),JSON.stringify(logs.slice(-5)));fs.mkdirSync('verification/full-demo-r31',{recursive:true});fs.writeFileSync('verification/full-demo-r31/report.json',JSON.stringify({checks:logs.filter(l=>l.text.startsWith('RAIDEN CHECK')||l.text.includes('GFTEST')).map(l=>l.text),method:'Actual bundled Lua full menu-driven lifecycle, human/CPU control, result and rematch, archived GFV2 lobby'},null,2));console.log(logs.filter(l=>l.text.includes('GFTEST PASS')||l.text.startsWith('FLOW')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
