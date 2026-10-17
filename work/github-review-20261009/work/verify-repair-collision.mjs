import{readFileSync,writeFileSync}from'node:fs';import assert from'node:assert/strict';
import{createStudio}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/index.js';
const out=process.env.REPAIR_OUT||'outputs/test-repair-v1',save=JSON.parse(readFileSync(out+'/fighter.save.json'));
save.assets.scripts[0].source=save.assets.scripts[0].source.replace('PIXEL_TEMPLATE_INDEX=1073741845','PIXEL_TEMPLATE_INDEX=0')+`
Collision.verify=function()
 local seen={};for seed=1,210 do local x,y,z=Collision.stageId(seed,1),Collision.stageId(seed,2),Collision.stageId(seed,3);assert(x~=y and x~=z and y~=z);local key=x..':'..y..':'..z;assert(not seen[key]);seen[key]=true end
 local a={role=1,x=0,y=0,face=1,crouch=false,down=0,attack={kind='light'}}
 local b={role=2,x=100,y=0,face=-1,crouch=false,down=0}
 local s={range=100};assert(Collision.overlap(Collision.attack(a,s,100),Collision.hurt(b)))
 b.x=127;assert(not Collision.overlap(Collision.attack(a,s,100),Collision.hurt(b)))
 a.face=-1;b.x=-100;assert(Collision.overlap(Collision.attack(a,s,100),Collision.hurt(b)))
 b.y=180;assert(not Collision.overlap(Collision.attack(a,s,100),Collision.hurt(b)))
 a.role=2;a.face=1;a.x=0;a.y=0;a.attack={kind='super',t=34,startup=24};local bird=Collision.attack(a,{},570);assert(bird[1]>100,'firebird trail must not hit');assert(bird[3]>300,'firebird must travel');a.role=1;a.attack={kind='light'}
 local standing=Collision.hurt(b);b.crouch=true;local crouching=Collision.hurt(b);assert(crouching[4]<standing[4])
 a.x=-535;a.face=1;b.x=-520;b.y=0;b.crouch=false;Collision.push(a,b);assert(a.x==-535 and math.abs(b.x-a.x)>=52)
 b.role=11;a.x=0;b.x=40;Collision.push(a,b);assert(math.abs(b.x-a.x)>=68)
 resetRound();f[1].face=1;f[1].x=0;local spec=specs[f[1].role].light;f[2].x=spec.range+Collision.profiles[f[2].role].width-1
 f[1].attack={kind='light',t=spec.startup,startup=spec.startup,hit=false};hit(1,2);assert(f[2].hp<100,'edge contact must hit')
 resetRound();f[1].face=1;f[1].x=0;f[2].x=spec.range+Collision.profiles[f[2].role].width+1
 f[1].attack={kind='light',t=spec.startup,startup=spec.startup,hit=false};hit(1,2);assert(f[2].hp==100,'separated boxes must miss')
 resetRound();f[1].x=0;f[1].face=1;f[2].x=60;f[2].face=-1;f[2].block=true
 f[1].attack={kind='light',t=spec.startup,startup=spec.startup,hit=false};hit(1,2);assert(f[2].guardStun and f[2].hp>95)
 local health=f[2].hp;f[1].attack={kind='light',t=spec.startup,startup=spec.startup,hit=false};hit(1,2);assert(f[2].hp>=health-2,'guard stun must remain blockable')
 local state=packState();f[2].guardStun=false;local savedDraw=draw;draw=function()end;assert(unpackState(state));draw=savedDraw;assert(f[2].guardStun,'guard flag must serialize')
 Collision.results={1,2,0};local snap=capture();Collision.results={};restore(snap);assert(Collision.results[1]==1 and Collision.results[2]==2 and Collision.results[3]==0)
 print('COLLISION_UNIT_PASS')
end;local collisionOriginalInit=OnInit;function OnInit()collisionOriginalInit();Collision.verify()end`;
const s=createStudio(save);s.playStart();const r=s.playGet();const errors=r.logs.filter(l=>l.level==='lua-error'||l.level==='error');assert.equal(errors.length,0,JSON.stringify(errors));assert(r.logs.some(l=>l.text==='COLLISION_UNIT_PASS'));writeFileSync(out+'/collision-verification.json',JSON.stringify({simulatorOnly:true,edgeContact:true,separatedMiss:true,facingMirror:true,airMiss:true,crouchState:true,wallPush:true,largeBody:true,actualDamage:true,rollbackRoundResults:true,manualCalibrationPending:true},null,2));console.log('COLLISION_UNIT_PASS');

