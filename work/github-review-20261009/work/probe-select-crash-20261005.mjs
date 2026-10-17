import fs from 'node:fs';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
// Simulator-only resource profile of the select -> battle transition. Not device memory.
const targets=(process.env.PROBE_OUTS||'outputs/basic-demo-20261005_050816,outputs/menu-art-return-20261005_050817').split(',');
const teams=JSON.parse(process.env.PROBE_TEAMS||'[[1,3,5],[2,4,6]]');
const result={simulatorOnly:true,deviceVerified:false,teams,targets:{}};
for(const out of targets){
 const save=JSON.parse(fs.readFileSync(out+'/simulator.save.json'));
 save.assets.scripts[0].source+=`
local probeUpdate=OnUpdate
local probeLast=nil
function OnUpdate(dt)
 probeUpdate(dt)
 local key=tostring(menuMode)..'/'..tostring(loadingState)..'/'..tostring(resourceGate.mode)
 if key~=probeLast then probeLast=key
  local ok,kb=pcall(function()return collectgarbage('count')end)
  local s=resourceGate.loader.stats or {}
  print('[PROBE] '..key..' luaKB='..tostring(ok and math.floor(kb) or 'n/a')..' created='..tostring(s.created)..' destroyed='..tostring(s.destroyed)..' caps='..tostring(resourceGate.caps[1])..','..tostring(resourceGate.caps[2]))
 end
end`;
 const s=createStudio(save);s.playStart({playerCount:2});
 const get=()=>s.playGet({view:true});
 const has=n=>get().scene.nodes.some(x=>x.name===n);
 const step=n=>{for(let i=0;i<n;i++)s.playStep(1/60,{observe:false});};
 const until=(p,label,max=30000)=>{for(let i=0;i<max;i+=20){if(p())return;step(20);}throw Error('Timeout '+label);};
 const settled=()=>until(()=>!has('LoadingBar'),'settle');
 const click=(p,n)=>{s.playSetView(p);const r=get();let node=r.scene.nodes.find(x=>x.name===n)||r.scene.nodes.find(x=>x.name===(n==='StartDuelHit'?'StartDuel':n));if(!node)throw Error('no '+n);let x=0,y=0;while(node){const ox=x,oy=y;x=node.matrix.a*ox+node.matrix.c*oy+node.matrix.tx;y=node.matrix.b*ox+node.matrix.d*oy+node.matrix.ty;node=r.scene.nodes.find(q=>q.id===node.parent);}s.playPointer('click',x,y,{observe:false});step(1);};
 const counts={};const mark=label=>{s.playSetView(1);const r=get();counts[label]={renderedNodes:r.scene.nodes.length};};
 for(let p=1;p<=2;p++){s.playSetView(p);settled();click(p,'StartDuelHit');settled();}
 mark('select');
 for(let p=1;p<=2;p++)for(const role of teams[p-1]){s.playSetView(p);settled();click(p,'GridCard'+role);settled();s.playSetView(3-p);settled();}
 mark('picked');
 click(1,'ReadyConfirm');step(120);click(2,'ReadyConfirm');
 s.playSetView(1);until(()=>has('Timer')&&!has('LoadingBar'),'battle',40000);mark('battle');
 const logs=get().logs.map(l=>l.text||'').filter(t=>/\[PROBE\]|LOAD METRIC|LOAD PHASE|RESOURCE\]|ERROR/.test(t));
 s.playStop();
 result.targets[out]={counts,logs};
 console.log(out);for(const l of logs)console.log('  '+l);console.log('  counts',JSON.stringify(counts));
}
fs.writeFileSync('work/probe-select-crash-20261005.json',JSON.stringify(result,null,2));
