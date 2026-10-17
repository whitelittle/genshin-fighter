import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const base='outputs/demo-online-light-rollback-diagnostic';
const out='outputs/seat-probe';mkdirSync(out,{recursive:true});
let source=readFileSync(base+'/fighter.lua','utf8');
const literal=s=>"'"+[...Buffer.from(s)].map(b=>'\\'+String(b).padStart(3,'0')).join('')+"'";
const replace=(a,b)=>{assert.equal(source.split(a).length,2,'anchor: '+a);source=source.replace(a,b);};
replace('local helloCount,joinCount,handshakeTime,receiveCount=0,0,0,0',`local helloCount,joinCount,handshakeTime,receiveCount=0,0,0,0
local seatProbeCount=0
local seatProbe=${literal('席位检测：尚未收到回调')}`);
replace(" script:RegisterServerSignalHandler('FighterSeat',function(_,params)\n  local assigned=tonumber(params[1]);if assigned~=1 and assigned~=2 then return end",` script:RegisterServerSignalHandler('FighterSeat',function(_,params)
  seatProbeCount=seatProbeCount+1
  local rawSlot=params and params[1]
  seatProbe=${literal('席位回调次数：')}..seatProbeCount..' | Slot='..tostring(rawSlot)
  print('[SEAT DEBUG] callback='..seatProbeCount..' Slot='..tostring(rawSlot))
  local assigned=tonumber(rawSlot);if assigned~=1 and assigned~=2 then
   seatProbe=seatProbe..${literal(' | 参数无效')};return
  end`);
const display=source.split('\n').find(l=>l.startsWith('  if label then label.text='));
assert.ok(display);replace(display,display.replace(/ end$/,`..'\\n'..seatProbe end`));
assert.ok(!/[^\x09\x0a\x20-\x7e]/.test(source));
writeFileSync(out+'/fighter_online_rollback_debug.lua',source);
const save=JSON.parse(readFileSync(base+'/fighter.save.json','utf8'));save.assets.scripts[0].source=source;
function panel(s){return s.playGet({view:true}).scene.nodes.find(n=>n.name==='BootDiagnostic').text;}
const waiting=structuredClone(save);waiting.serverLogic={version:1,rules:[]};const w=createStudio(waiting);w.playStart();for(let i=0;i<130;i++)w.playStep(1/60,{observe:false});assert.ok(panel(w).includes('尚未收到回调'),panel(w));
const s=createStudio(save);s.playStart({playerCount:2});for(let i=0;i<130;i++)s.playStep(1/60,{observe:false});
const results=[];for(const p of [1,2]){s.playSetView(p);const state=s.playGet({view:true});const text=panel(s);assert.ok(text.includes('席位回调次数：')&&text.includes('Slot='+p),text);assert.equal(state.logs.filter(l=>l.level==='lua-error'||l.level==='error').length,0);results.push({player:p,text});}
writeFileSync(out+'/verification.json',JSON.stringify({deviceVerified:false,waitingProbePersists:true,players:results},null,2));
console.log(JSON.stringify({file:out+'/fighter_online_rollback_debug.lua',bytes:Buffer.byteLength(source),waitingProbePersists:true,bothSeatCallbacksVerified:true}));
