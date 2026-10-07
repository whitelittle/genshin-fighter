import fs from 'node:fs';import assert from 'node:assert/strict';import {Worker} from 'node:worker_threads';import {createRequire} from 'node:module';import {renderScenePng} from '../vendor/simulator/studio/host-png.js';
const require=createRequire(import.meta.url),canvas=require.resolve('@napi-rs/canvas');
const project=JSON.parse(fs.readFileSync('dist/projects/raiden-nahida.json'));
project.assets.scripts[0].source=project.assets.scripts[0].source.replace("GF_FIRST_SCENE='intro'","GF_FIRST_SCENE='fight'");
project.assets.scripts[0].source=project.assets.scripts[0].source.replace('cpu={2,2}','cpu={false,false}');
project.assets.scripts[0].source+=`\nlocal oldUpdate=OnUpdate;local checked=false;local age=0
function OnUpdate(dt)
 oldUpdate(dt)
 if app and app.sceneName=='fight' and app.scene.state=='run' then
  local scene=app.scene
  if not checked then
   checked=true;local S=require('gf_sim');local A=require('gf_art');local R=require('gf_roster');local by={};for _,c in ipairs(R) do by[c.key]=c end
   local function test(key,block,invul,far)
    local sim=S.new({chars={by[key],by.nahida},rounds=2,time=99});sim.phase='fight';sim.phaseT=0
    for _,p in ipairs(sim.f) do sim:setState(p,'idle');p.invul=0 end
    local p,d=sim.f[1],sim.f[2];p.x=0;d.x=far and 120000 or 14000;p.energy=100;d.invul=invul or 0
    assert(sim:startBurst(p));local hits,blocks,first,last,total=0,0,nil,nil,0;local cinema=false
    for i=1,400 do
     sim:step(0,block and S.B.R or 0)
     for _,e in ipairs(sim.events) do
      if e.type=='burst' then cinema=true end
      if e.type=='hit' and e.by==1 then hits=hits+1;first=first or i;last=i end
      if e.type=='block' and e.by==1 then blocks=blocks+1 end
     end
     if p.state~='burst' then total=i;break end
    end
    if key=='raidenshogun' then
     if block then assert(hits==0 and blocks==1 and not cinema,'block entered cinematic')
     elseif invul or far then assert(hits==0 and not cinema,'miss entered cinematic')
     else assert(hits==3 and cinema,'confirmed burst needs 3 hits');assert(total>=180 and last-first>=120,'burst too fast');assert(not p.cinematicConfirmed,'sequence never ended') end
    else assert(hits==3 and total>100,'Nahida original multi-hit burst') end
    if key=='raidenshogun' and not block and not invul and not far then
     for i=1,180 do sim:step(0,0) end
     assert(d.state=='idle' and not d.ko and not p.cinematicConfirmed,'victim did not recover')
    end
    return total
   end
   local duration=test('raidenshogun',false,nil,false);test('raidenshogun',true,nil,false);test('raidenshogun',false,40,false);test('raidenshogun',false,nil,true);test('nahida',false,nil,false)
   for _,side in ipairs({-1,1}) do
    for _,hp in ipairs({50,150,1000}) do
     local sim=S.new({chars={by.raidenshogun,by.nahida},rounds=2,time=99});sim.phase='fight';sim.phaseT=0
     local p,d=sim.f[1],sim.f[2];for _,f in ipairs(sim.f) do sim:setState(f,'idle');f.invul=0 end
     p.x=side*(S.WALL-10000);d.x=side*(S.WALL-5000);p.face=side;d.face=-side;p.energy=100;d.hp=hp
     assert(sim:startBurst(p))
     for i=1,600 do
      sim:step(0,0)
      assert(math.abs(p.x)<=S.WALL and math.abs(d.x)<=S.WALL,'outside stage wall')
      if p.cinematicConfirmed and p.t<70 then assert(math.abs(d.x-p.x)>=30000,'victim overlaps caster') end
      if p.state~='burst' then assert(not p.cinematicConfirmed,'cinematic state leaked after KO/state change') end
     end
     assert(sim.freeze==0 and not p.cinematicConfirmed,'frozen after sequence')
     if hp<300 then assert(sim.round==2 and not d.ko and d.hp==d.maxhp,'KO round reset failed') end
    end
   end
   print('BURST RECOVERY PASS both walls; KO on first/second hit; next-round reset; normal getup')
   for _,key in ipairs({'raidenshogun','nahida'}) do assert(A.portrait(key).w==A.mod(key).portrait.s,'cut-in portrait enlarged replacement') end
   print('BURST PASS Raiden 3 hits duration='..duration..' frames; block/miss no cinematic; Nahida original 3 hits; original portraits')
   local sim=scene.sim;sim.phase='fight';sim.phaseT=0;sim.f[1].x=0;sim.f[2].x=14000
   for _,p in ipairs(sim.f) do sim:setState(p,'idle');p.invul=0;p.hp=p.maxhp end
   sim.f[1].energy=100;sim:startBurst(sim.f[1]);scene:events();age=0
  end
  age=age+1
  if age==20 then print('BURSTSHOT cutin') end
  if age==95 then print('BURSTSHOT strike') end
  if age==175 then print('BURSTSHOT finisher') end
  if age==400 then assert(#scene.burstBg.items==0 or scene.burstBg.n==0,'background leaked');print('BURSTSHOT recovered');print('BURST DONE') end
 end
end\n`;
const worker=new Worker(`const {parentPort}=require('node:worker_threads');globalThis.OffscreenCanvas=function(w,h){return require(${JSON.stringify(canvas)}).createCanvas(w,h)};globalThis.postMessage=v=>parentPort.postMessage(v);let q=[];parentPort.on('message',data=>globalThis.onmessage?globalThis.onmessage({data}):q.push(data));import(${JSON.stringify('file://'+process.cwd()+'/dist/editor/simulator-worker.js')}).then(()=>{for(const data of q)globalThis.onmessage({data})});`,{eval:true});
let seq=0;const pending=new Map();worker.on('message',r=>{const p=pending.get(r.id);if(!p)return;pending.delete(r.id);r.ok?p.resolve(r.value):p.reject(Error(r.error));});worker.on('error',e=>{for(const p of pending.values())p.reject(e);});
const call=(action,body={})=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});worker.postMessage({id,action,body});});
let logs=[];async function observe(){const s=await call('play',{action:'get',args:{view:true,compact:true}});assert.equal(s.mountError,null);const errors=s.logs.filter(l=>l.level==='error');assert.equal(errors.length,0,JSON.stringify(errors));logs=s.logs;return s;}
async function step(n){for(let i=0;i<n;i++)await call('play',{action:'step',args:{dt:1/60,light:true}});}
async function capture(name){const s=await observe();const im=renderScenePng(s.scene,s.canvasWidth,s.canvasHeight);fs.mkdirSync('verification/dual-character',{recursive:true});fs.writeFileSync('verification/dual-character/'+name+'.png',im.data);return s;}
try{
 await call('import',{format:'json',filename:'r20.json',data:Buffer.from(JSON.stringify(project)).toString('base64')});
 await call('play',{action:'start'});await call('play',{action:'pause'});
 const saved=new Set();
 for(let i=0;i<1400;i++){
  await call('play',{action:'step',args:{dt:1/60,light:true}});
  if(i%5)continue;const snap=await observe();
  for(const log of logs.filter(l=>l.text.startsWith('BURSTSHOT'))){
   if(saved.has(log.text))continue;saved.add(log.text);
   fs.mkdirSync('verification/burst-cinema',{recursive:true});fs.writeFileSync('verification/burst-cinema/'+log.text.split(' ')[1]+'.png',renderScenePng(snap.scene,snap.canvasWidth,snap.canvasHeight).data);
  }
  if(logs.some(l=>l.text==='BURST DONE'))break;
 }
 assert(logs.some(l=>l.text.startsWith('BURST PASS')),JSON.stringify(logs.slice(-5)));assert(saved.size===4);
 fs.writeFileSync('verification/burst-cinema/report.json',JSON.stringify({release:'nahida-integrated-r25',checks:logs.filter(l=>l.text.startsWith('BURST')).map(l=>l.text),method:'Actual bundled Lua Worker; CPU rendering'},null,2));
 console.log(logs.filter(l=>l.text.startsWith('BURST')).map(l=>l.text).join('\n'));
}finally{await worker.terminate();}
