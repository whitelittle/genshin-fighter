import {readFileSync,writeFileSync} from 'node:fs';import assert from 'node:assert/strict';
import {createStudio} from 'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out=process.env.DUEL_COMBAT_OUT||'outputs/duel-vnext',save=JSON.parse(readFileSync(out+'/fighter.save.json')),source=save.assets.scripts[0].source;
const core=source.slice(0,source.indexOf('local spriteData='));
const apply=source.slice(source.indexOf('local function applyInput('),source.indexOf('local function copy('));
const snapshots=source.slice(source.indexOf('local function copy('),source.indexOf('local function NewRollbackSession('));
const module=source.slice(source.indexOf('local function NewRollbackSession('),source.indexOf('local menuEpoch=1'));
const tests=`
local function game()
 ${core}
 local spriteCache={}
 ${apply}
 ${snapshots}
 restart();phase='fight';f[1].x=-40;f[2].x=40;replaying=true
 return {capture=capture,restore=restore,input=applyInput,step=step}
end
local function run(g,n)for i=1,n do g.step()end end
local function setup(g,callback)local s=g.capture();callback(s);g.restore(s)end
local function attack(g,move,crouch,guard)
 g.input(2,'down',crouch and 1 or 0);g.input(2,'block',guard and 1 or 0)
 if move=='low' then g.input(1,'down',1);g.input(1,'clickLight',1)
 elseif move=='overhead' then g.input(1,'right',1);g.input(1,'clickHeavy',1)
 else g.input(1,'clickHeavy',1)end
 run(g,45);return g.capture().f[2].hp
end
${module}
local function canonical(v)
 if type(v)~='table'then return type(v)=='number' and string.format('%.17g',v)or tostring(v)end
 local keys={};for k in pairs(v)do keys[#keys+1]=k end;table.sort(keys,function(a,b)return tostring(a)<tostring(b)end)
 local r={};for _,k in ipairs(keys)do r[#r+1]=tostring(k)..'='..canonical(v[k])end;return '{'..table.concat(r,';')..'}'
end
function OnStart()
 assert(attack(game(),'low',false,true)==93,'low must beat stand guard')
 assert(attack(game(),'low',true,true)==99,'crouch guard must block low')
 assert(attack(game(),'overhead',true,true)==82,'overhead must beat crouch guard')
 assert(attack(game(),'overhead',false,true)==98,'stand guard must block overhead')
 assert(attack(game(),'mid',true,true)==98 and attack(game(),'mid',false,true)==98,'mid must block both')
 for _,crouch in ipairs({false,true})do
  local jumping=game();setup(jumping,function(s)s.f[1].y=50;s.f[1].vy=0 end)
  jumping.input(2,'down',crouch and 1 or 0);jumping.input(2,'block',1);jumping.input(1,'clickLight',1);run(jumping,15)
  assert(jumping.capture().f[2].hp==(crouch and 92 or 99),'jump attack guard height')
 end
 print('COMBAT_GUARD_PASS')
 local k=game();k.input(1,'skill',1);run(k,30)
 assert(k.capture().f[1].markLife>0 and k.capture().f[2].hp==100,'stiletto placement')
 k.input(1,'skill',1);run(k,20)
 assert(k.capture().f[1].markLife==0 and k.capture().f[2].hp==84,'teleport followup')
 print('COMBAT_KEQING_E_PASS')
 local d=game();setup(d,function(s)s.f[1].role=2 end)
 d.input(1,'skill',1);run(d,24);assert(d.capture().f[1].eStage==1,'e1')
 d.input(1,'skill',1);run(d,22);assert(d.capture().f[1].eStage==2,'e2')
 d.input(1,'skill',1);run(d,27);assert(d.capture().f[1].eStage==3,'e3')
 assert(d.capture().f[2].hp==61 and d.capture().f[2].down>0,'three-stage damage and knockdown')
 print('COMBAT_DILUC_E_PASS')
 local q=game();setup(q,function(s)s.f[1].meter=100 end);q.input(1,'ultimate',1);run(q,35)
 assert(q.capture().f[2].hp==62,'Keqing Q single hit');run(q,15);assert(q.capture().f[2].hp==62,'Q multiple visual slashes must not rehit')
 print('COMBAT_KEQING_Q_PASS')
 local bird=game();setup(bird,function(s)s.f[1].role=2;s.f[1].meter=100;s.f[1].x=-250;s.f[2].x=250 end)
 bird.input(1,'ultimate',1);run(bird,35);assert(bird.capture().f[2].hp==100,'phoenix must travel to range')
 run(bird,23);assert(bird.capture().f[2].hp==56,'phoenix ranged hit')
 print('COMBAT_DILUC_Q_PASS')
 local air=game();setup(air,function(s)s.f[2].launched=true;s.f[2].y=120;s.f[2].vy=-100;s.f[2].stun=75 end)
 run(air,28);assert(air.capture().f[2].down>0,'airborne to knockdown');run(air,45);assert(air.capture().f[2].wake>0,'knockdown to wake');run(air,20);assert(air.capture().f[2].wake==0,'getup complete')
 print('COMBAT_AIR_DOWN_PASS')
 local games,peers={game(),game()},{};for i=1,2 do peers[i]=NewRollbackSession(games[i],i)end
 local schedule={[1]={{1,'skill',1}},[38]={{1,'skill',1}},[100]={{2,'down',1},{2,'block',1}},[130]={{1,'down',1},{1,'clickLight',1}},[160]={{2,'down',0},{2,'block',0}},[180]={{2,'skill',1}},[204]={{2,'skill',1}},[228]={{2,'skill',1}},[300]={{1,'jump',1}}}
 for _,g in ipairs(games)do setup(g,function(s)s.f[2].role=2 end)end
 local transit={}
 for t=1,420 do
  for n=#transit,1,-1 do local p=transit[n];if p.due<=t then assert(peers[p.target]:receive(p.first,p.ack,p.payload));table.remove(transit,n)end end
  for _,e in ipairs(schedule[t]or{})do peers[e[1]]:queue(e[2],e[3])end
  for i=1,2 do peers[i]:advance();assert(not peers[i].error,peers[i].error)end
  if t%3==0 and t%17~=0 then for i=1,2 do local first,ack,payload=peers[i]:packet();transit[#transit+1]={due=t+3+(t+i)%5,target=3-i,first=first,ack=ack,payload=payload}end end
 end
 for t=421,500 do
  for n=#transit,1,-1 do local p=transit[n];assert(peers[p.target]:receive(p.first,p.ack,p.payload));table.remove(transit,n)end
  for i=1,2 do peers[i]:repair()end
  if peers[1].frame~=peers[2].frame then peers[peers[1].frame<peers[2].frame and 1 or 2]:advance()end
  for i=1,2 do local first,ack,payload=peers[i]:packet();assert(peers[3-i]:receive(first,ack,payload))end
 end
 for i=1,2 do peers[i]:repair();assert(peers[i].confirmed==peers[i].frame,'unconfirmed')end
 assert(canonical(games[1].capture())==canonical(games[2].capture()),'new action states must converge after late inputs')
 assert(peers[1].rollbacks+peers[2].rollbacks>0,'rollback not exercised')
 print('COMBAT_ROLLBACK_PASS')
end
`;
const d=structuredClone(save);d.assets.scripts[0].source=tests;d.serverLogic={version:1,rules:[]};const s=createStudio(d);s.playStart();const r=s.playGet({view:true});
const errors=r.logs.filter(l=>['error','lua-error'].includes(l.level));console.log(JSON.stringify(r.logs.map(l=>l.text).filter(Boolean)));assert.equal(errors.length,0,JSON.stringify(errors));
const passed=r.logs.map(l=>l.text).filter(t=>t?.startsWith('COMBAT_'));assert.equal(passed.length,7,'all combat checks must finish');
writeFileSync(out+'/combat-verification.json',JSON.stringify({simulatorVerified:true,deviceVerified:false,passed},null,2));
