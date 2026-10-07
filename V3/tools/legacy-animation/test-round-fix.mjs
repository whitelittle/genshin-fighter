import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace('cpu={2,2}','cpu={false,false}');
project.assets.scripts[0].source+=`\nlocal oldUpdate=OnUpdate
local started=false;local lastTitle;local stage=0
function OnUpdate(dt)
 oldUpdate(dt)
 if app and app.sceneName=='fight' and app.scene.state=='run' then
  local scene=app.scene;local sim=scene.sim;local A=require('gf_art')
  if not started then
   started=true
   assert(GF_RELEASE_ID=='dual-eye-grass-r31','release id')
   for _,key in ipairs({'raidenshogun','nahida'}) do
    assert(A.pose(key,'lo','idle')==A.animation(key,'lo','basic_0'),'selection body still old')
    assert(A.round(key).w==A.mod(key).round.s,'original HUD head size')
    assert(A.portrait(key).w==A.mod(key).portrait.s,'original burst portrait dimensions')
   end
  end
  assert(#scene.banners<=1,'stacked primary announcements')
  local title=scene.banners[1] and scene.banners[1].text
  if title and title~=lastTitle then
   lastTitle=title
   print('R18 TITLE '..title..' ROUND '..sim.round)
  end
  if title then
   local count=0
   for _,node in ipairs(scene.annL.items) do
    if node.kind=='text' and node.act and node.tv==title then count=count+1 end
   end
   assert(count<=1,'duplicate glyph/afterimage')
  end
  if sim.phase=='fight' and sim.round<=2 and stage<sim.round then
   stage=sim.round;sim.f[sim.round==1 and 2 or 1].hp=0
  end
  if sim.round==3 and sim.phase=='fight' and stage<3 then
   stage=3;print('R18 PASS three rounds, one title, fresh bodies, fresh HUD heads, fresh cutin')
  end
 end
end\n`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>l.level==='error');assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{
 await call('import',{format:'json',filename:'r18.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});
 await call('play',{action:'start'});await call('play',{action:'pause'});
 let saved=new Set();
 for(let i=0;i<900;i++){
  await call('play',{action:'step',args:{dt:1/20,light:true}});
  if(i%3)continue;
  const snap=await observe();
  for(const log of logs.filter(l=>l.text.startsWith('R18 TITLE'))){
   if(saved.has(log.text))continue;saved.add(log.text);
   const png=renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight);
   fs.mkdirSync('verification/round-fix',{recursive:true});fs.writeFileSync('verification/round-fix/stage-'+saved.size+'.png',png.data);
  }
  if(logs.some(l=>l.text.startsWith('R18 PASS')))break;
 }
 assert(logs.some(l=>l.text.startsWith('R18 PASS')),JSON.stringify(logs.slice(-5)));
 fs.writeFileSync('verification/round-fix/report.json',JSON.stringify({release:'dual-round-fix-r18',renderHz:20,checks:logs.filter(l=>l.text.startsWith('R18')).map(l=>l.text),method:'Actual bundled Lua Worker; CPU rendering. Browser GPU not verified.'},null,2));
 console.log(logs.filter(l=>l.text.startsWith('R18')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
