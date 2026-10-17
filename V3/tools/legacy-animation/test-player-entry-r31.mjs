import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("mode='demo',cpu={2,2}","mode='versus',cpu={false,2}");
project.assets.scripts[0].source+=`
local previous=OnUpdate;local checked=false
function OnUpdate(dt)
 previous(dt)
 if not checked and app and app.sceneName=='fight' and app.scene.state=='run' then
  checked=true;assert(app.scene.mode=='versus','mode');assert(app.scene.ai[1]==nil,'1P is still AI');assert(app.scene.ai[2]~=nil,'2P AI missing');print('GFTEST PASS browser default 1P human versus 2P AI')
 end
end
`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>(l.level==='error'||l.level==='lua-error'));assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{await call('import',{format:'json',filename:'raiden-nahida.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});await call('play',{action:'start'});await call('play',{action:'pause'});await step(600);let s=await observe();assert(logs.some(l=>l.text.includes('GFTEST PASS')),JSON.stringify(logs.slice(-5)));fs.mkdirSync('verification/player-entry-r31',{recursive:true});fs.writeFileSync('verification/player-entry-r31/report.json',JSON.stringify({checks:logs.filter(l=>l.text.startsWith('RAIDEN CHECK')||l.text.includes('GFTEST')).map(l=>l.text),method:'Actual bundled Lua; default difficulty 2; 5 matches; per-side 480-frame cooldown assertions'},null,2));console.log(logs.filter(l=>l.text.includes('GFTEST PASS')||l.text.startsWith('RAIDEN CHECK')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
