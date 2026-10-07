import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source+=`\nlocal oldUpdate=OnUpdate;local started=false;local age=0;local hit={0,0};local actions={0,0};local done=false
function OnUpdate(dt)
 oldUpdate(dt)
 if app and app.sceneName=='fight' and app.scene.state=='run' then
  local scene=app.scene;local A=require('gf_art');local U=require('gf_util')
  if not started then
   started=true;assert(scene.ai[1] and scene.ai[2],'both AI required');assert(scene.mode=='demo','demonstration mode')
   for _,key in ipairs({'raidenshogun','nahida'}) do
    for _,which in ipairs({'face','round'}) do
     local img=A[which](key);local original=A.mod(key)[which];local bytes=U.decodeAll(original.d)
     assert(img.w==original.s and img.n==original.n,'original portrait dimensions')
     assert(#img.bytes==#bytes,'original portrait bytes')
     for i,v in ipairs(bytes) do assert(img.bytes[i]==v,'portrait changed') end
    end
   end
  end
  age=age+1
  for _,e in ipairs(scene.sim.events) do
   if e.type=='hit' then hit[e.by]=hit[e.by]+1 end
   if e.type=='swing' or e.type=='skill' or e.type=='burst' then actions[e.p]=actions[e.p]+1 end
  end
  assert(#scene.banners<=1,'stacked announcements')
  if not done and age>450 then
   assert(hit[1]>0 and hit[2]>0,'both AI should hit');assert(actions[1]>0 and actions[2]>0,'both AI should act')
   done=true;print('DEMO PASS original portraits, both AI; hits='..hit[1]..'/'..hit[2]..' actions='..actions[1]..'/'..actions[2])
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
 await call('import',{format:'json',filename:'r19.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});
 await call('play',{action:'start'});await call('play',{action:'pause'});
 for(let i=0;i<1000;i++){
  await call('play',{action:'step',args:{dt:1/20,light:true}});
  if(i%10)continue;await observe();
  if(logs.some(l=>l.text.startsWith('DEMO PASS')))break;
 }
 assert(logs.some(l=>l.text.startsWith('DEMO PASS')),JSON.stringify(logs.slice(-5)));
 const snap=await observe();const png=renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight);
 fs.mkdirSync('verification/ai-demo',{recursive:true});fs.writeFileSync('verification/ai-demo/battle.png',png.data);
 fs.writeFileSync('verification/ai-demo/report.json',JSON.stringify({release:'dual-scale-throw-r22',checks:logs.filter(l=>l.text.startsWith('DEMO')).map(l=>l.text),method:'Actual bundled Lua Worker; CPU rendering'},null,2));
 console.log(logs.filter(l=>l.text.startsWith('DEMO')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
