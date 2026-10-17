import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out='outputs/visual-cache';mkdirSync(out,{recursive:true});
const before=readFileSync('outputs/seat-probe/fighter_online_rollback_debug.lua','utf8');let source=before;
const replace=(a,b)=>{assert.equal(source.split(a).length,2,'anchor '+a.slice(0,80));source=source.replace(a,b);};
replace('local spriteCache={}',`local spriteCache={}
local visualNodes,visualCounts,visualValues={},{},{}
local rootNodes,actorNodes={},{}
local visualWrites,visualChanges,visualUpdates=0,0,0
local visualRate,visualLastWrites,visualLastChanges=0,0,0
local function rootNode(name)
 local node=rootNodes[name];if not node then node=root:FindChild(name);rootNodes[name]=node end;return node
end
local function actorNode(i,name)
 actorNodes[i]=actorNodes[i] or {};local node=actorNodes[i][name]
 if not node then node=actors[i]:FindChild(name);actorNodes[i][name]=node end;return node
end`);
const start=source.indexOf('  local data=spriteData[a.role][pose]');const end=source.indexOf('  spriteCache[i]=key',start);
assert.ok(start>0&&end>start);
source=source.slice(0,start)+`  local data=spriteData[a.role][pose];local pool=art:FindChild('Sprite')
  visualNodes[i]=visualNodes[i] or {};visualValues[i]=visualValues[i] or {}
  local nodes,values=visualNodes[i],visualValues[i]
  local count=#data.rows;local previous=visualCounts[i] or 2275
  for n=1,math.max(count,previous) do
   local node=nodes[n];if not node then node=pool:FindChild('P'..n);nodes[n]=node end
   local v=values[n];if not v then v={};values[n]=v end
   local r=data.rows[n];local visible=r~=nil
   if v.visible~=visible then node:SetVisible(visible);v.visible=visible;visualWrites=visualWrites+1 end
   if r then
    local x=(r[1]+r[3]/2-data.anchor[1])*data.scale
    local y=(data.anchor[2]-r[2]-r[4]/2)*data.scale
    local w,h=r[3]*data.scale,r[4]*data.scale
    if v.x~=x or v.y~=y then node:SetAnchoredPosition(x,y);v.x=x;v.y=y;visualWrites=visualWrites+1 end
    if v.w~=w or v.h~=h then node:SetSizeDelta(w,h);v.w=w;v.h=h;visualWrites=visualWrites+1 end
    if v.color~=r[5] then node.imageColor=r[5];v.color=r[5];visualWrites=visualWrites+1 end
   end
  end
  visualCounts[i]=count;visualChanges=visualChanges+1
`+source.slice(end);
// Cache lookups in rendering only. Input binding and lifecycle remain untouched.
const ds=source.indexOf('local function updateSprite(i)'),de=source.indexOf('function OnInit()',ds);
let drawing=source.slice(ds,de).replaceAll("actors[i]:FindChild('","actorNode(i,'").replaceAll('root:FindChild(','rootNode(');
drawing=drawing.replace('local function drawStage()\n',`local drawnStage=nil
local function drawStage()
 if drawnStage==stage then return end
 drawnStage=stage
`);
// This rotation was immediately overwritten by updateSprite; keep only the final rotation.
drawing=drawing.replace('  art:SetLocalRotation(0,0,a.down>0 and -90*a.face or (a.launched and -35*a.face or 0))\n','');
source=source.slice(0,ds)+drawing+source.slice(de);
replace('function OnUpdate(dt)\n handshakeTime=handshakeTime+dt',`function OnUpdate(dt)
 visualUpdates=visualUpdates+1
 handshakeTime=handshakeTime+dt`);
replace(' if handshakeTime>=1 then\n  handshakeTime=0',` if handshakeTime>=1 then
  visualRate=visualUpdates/handshakeTime;visualLastWrites=visualWrites;visualLastChanges=visualChanges
  visualUpdates=0;visualWrites=0;visualChanges=0
  handshakeTime=0`);
const display=source.split('\n').find(l=>l.startsWith('  if label then label.text='));assert.ok(display);
replace(display,display.replace("..debugNet.last", "..'LuaHz '..string.format('%.1f',visualRate)..' | Pose '..visualLastChanges..' | Writes '..visualLastWrites"));
assert.ok(!/[^\x09\x0a\x20-\x7e]/.test(source));
writeFileSync(out+'/fighter_online_rollback_debug.lua',source);
const save=JSON.parse(readFileSync('outputs/demo-online-light-rollback-diagnostic/fighter.save.json','utf8'));
function make(lua){const v=structuredClone(save);v.assets.scripts[0].source=lua;const s=createStudio(v);s.playStart({playerCount:2});return s;}
const a=make(before),b=make(source);const milestones=[];
const events={1:[1,'Light'],24:[2,'Heavy'],85:[1,'Jump'],130:[1,'RoleDiluc'],190:[2,'RoleKeqing'],250:[1,'SelectStage2'],280:[1,'Light'],330:[2,'Heavy'],400:[1,'Restart']};
// Use production control names from the save rather than inventing role/stage selectors.
const names=new Set(a.playGet({view:true}).scene.nodes.map(n=>n.name));
for(let n=0;n<470;n++){
 if(events[n]){const [p,name]=events[n];assert.ok(names.has(name),'missing test control '+name);for(const s of [a,b]){s.playSetView(p);s.playClick(name,{observe:false});}}
 for(const s of [a,b])s.playStep(1/60,{observe:false});
 if(n%10===0||n===469)for(const p of [1,2]){
  a.playSetView(p);b.playSetView(p);const x=a.playGet({view:true}),y=b.playGet({view:true});
  for(const v of [x,y])assert.equal(v.logs.filter(l=>['error','lua-error'].includes(l.level)||String(l.text).includes('ERROR:')).length,0,JSON.stringify(v.logs.slice(-5)));
  const clean=v=>v.scene.nodes.filter(n=>n.name!=='BootDiagnostic');
  assert.deepEqual(clean(x),clean(y),'visual mismatch frame '+n+' player '+p);
  if(n===469)milestones.push({player:p,diagnostic:y.scene.nodes.find(n=>n.name==='BootDiagnostic').text});
 }
}
// Rendering patch must leave the deterministic combat/session implementation byte-identical.
assert.equal(source.slice(0,source.indexOf('local spriteCache=')),before.slice(0,before.indexOf('local spriteCache=')));
assert.equal(source.slice(source.indexOf('local fields='),source.indexOf('local resendTime=')),before.slice(before.indexOf('local fields='),before.indexOf('local resendTime=')));
const report={simulatorVerified:true,deviceVerified:false,frames:470,checkedScenes:96,fullSceneMatchesExceptDiagnostic:true,combatAndRollbackCodeUnchanged:true,perRoleCounts:[1368,2274],existingResidentPool:4550,newPosePools:0,milestones};
writeFileSync(out+'/verification.json',JSON.stringify(report,null,2));console.log(JSON.stringify(report));
