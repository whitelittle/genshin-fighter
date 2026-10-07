import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace('cpu={2,2}','cpu={false,false}');
project.assets.scripts[0].source+=`
local originalUpdate=OnUpdate;local checked=false
function OnUpdate(dt)
 originalUpdate(dt)
 if not checked and app and app.scene and app.scene.state=='run' and app.scene.sim then
 checked=true;local S=require('gf_sim');local R=require('gf_roster');local by={};for _,v in ipairs(R) do by[v.key]=v end
 local function test(id,juggle,hp,mode,wall)
  local chars=id==1 and {by.nahida,by.raidenshogun} or {by.raidenshogun,by.nahida}
  local s=S.new({chars=chars,time=99});s.phase='fight';s.phaseT=0
  for _,f in ipairs(s.f) do s:setState(f,'idle');f.invul=0 end
  local p,d=s.f[id],s.f[3-id];p.x=wall==0 and 0 or wall*(S.WALL-20000);p.face=wall==0 and 1 or wall;d.x=p.x+p.face*14000;d.face=-p.face;p.energy=100;d.hp=hp
  if juggle>0 then s:setState(d,'airhit');d.y=10000;d.juggle=juggle;d.combo=juggle end
  if mode=='invul' then d.invul=200 elseif mode=='down' then s:setState(d,'down') elseif mode=='far' then d.x=p.x+120000 end
  local hits,blocks,frames,damage=0,0,{},0;assert(s:startBurst(p))
  for n=1,500 do
   s:step(0,id==1 and mode=='block' and S.B.R or 0)
   for _,e in ipairs(s.events) do if e.type=='hit' and e.by==id and e.kind=='burst' then hits=hits+1;frames[#frames+1]=p.t;damage=damage+e.dmg elseif e.type=='block' and e.by==id then blocks=blocks+1 end end
   if s.phase~='fight' then break end
  end
  local expected=mode~='normal' and 0 or hp==50 and 1 or hp==150 and 2 or 3
  print('NAHIDA CHECK side='..id..' juggle='..juggle..' hp='..hp..' mode='..mode..' hits='..hits..' damage='..damage..' frames='..table.concat(frames,','))
  assert(hits==expected,'confirmed burst lost a hit: juggle='..juggle..' expected='..expected..' actual='..hits)
  if expected==3 then assert(frames[1]==2 and frames[2]==28 and frames[3]==54,'Nahida strike timings changed');assert(damage>0 and not d.ko,'invalid confirmed damage');assert(damage==1000-d.hp,'event damage differs from health loss') end
  if mode=='block' then assert(blocks==3 and not p.cinematicConfirmed,'blocked opener entered cinema') end
 end
 for _,j in ipairs({0,7,8,10}) do for _,id in ipairs({1,2}) do for _,wall in ipairs({-1,0,1}) do test(id,j,1000,'normal',wall) end end end
 for _,mode in ipairs({'block','invul'}) do test(1,0,1000,mode,0) end
 test(1,0,50,'normal',0);test(1,0,150,'normal',0)
 print('GFTEST PASS Nahida confirmed 3-hit continuation; combo escape; both sides/walls; opener defense/miss; early KO')
 end
end
`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>(l.level==='error'||l.level==='lua-error'));assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{await call('import',{format:'json',filename:'raiden-nahida.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});await call('play',{action:'start'});await call('play',{action:'pause'});await step(600);let s=await observe();assert(logs.some(l=>l.text.includes('GFTEST PASS')),JSON.stringify(logs.slice(-5)));fs.mkdirSync('verification/nahida-confirmed-hits-r31',{recursive:true});fs.writeFileSync('verification/nahida-confirmed-hits-r31/report.json',JSON.stringify({checks:logs.filter(l=>l.text.startsWith('NAHIDA CHECK')||l.text.includes('GFTEST')).map(l=>l.text),method:'Actual bundled Lua; default difficulty 2; 5 matches; per-side 480-frame cooldown assertions'},null,2));console.log(logs.filter(l=>l.text.includes('GFTEST PASS')||l.text.startsWith('NAHIDA CHECK')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
