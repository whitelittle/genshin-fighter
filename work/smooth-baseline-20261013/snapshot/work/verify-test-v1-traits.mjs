import{readFileSync,writeFileSync}from'node:fs';
let source=readFileSync('work/verify-vnext-combat.mjs','utf8');
source=source.replace("process.env.DUEL_COMBAT_OUT||'outputs/duel-vnext'","'outputs/test-v1'");
source=source.replace("print('COMBAT_ROLLBACK_PASS')",`print('COMBAT_ROLLBACK_PASS')
 local x=game();setup(x,function(s)s.f[1].role=9 end)
 x.input(1,'skill',1);run(x,75);x.input(1,'skill',1);run(x,75)
 assert(x.capture().f[1].eCharges==0,'Xiao must exhaust two charges')
 x.input(1,'skill',1);run(x,25);assert(x.capture().f[1].eCharges==0,'third E must be rejected')
 run(x,240);assert(x.capture().f[1].eCharges>=1,'Xiao charge recovery')
 setup(x,function(s)s.f[1].meter=100;s.f[1].stun=0;s.f[1].down=0;s.f[1].wake=0;s.f[1].attack=nil end)
 x.input(1,'ultimate',1);run(x,90);x.input(1,'jump',1);run(x,1);assert(x.capture().f[1].vy>500,'Xiao burst improves jump')
 print('TRAIT_XIAO_PASS')
 local h=game();setup(h,function(s)s.f[1].role=10;s.f[1].hp=80 end);h.input(1,'skill',1);run(h,65)
 assert(h.capture().f[1].hp==70 and h.capture().f[1].buffLife>0 and h.capture().f[2].hp==100,'Hu Tao E exchanges health for buff')
 h.input(1,'skill',1);run(h,25);assert(h.capture().f[1].hp==70,'active buff cannot spend health again')
 setup(h,function(s)s.f[1].meter=100 end);h.input(1,'ultimate',1);run(h,35);assert(h.capture().f[1].hp>70,'Hu Tao Q heals on hit')
 print('TRAIT_HUTAO_PASS')
 local g=game();setup(g,function(s)s.f[1].role=7 end);g.input(1,'skill',1);run(g,25);assert(g.capture().f[1].x< -40 and g.capture().f[2].hp<100,'Ganyu retreats and attacks')
 local j=game();setup(j,function(s)s.f[1].role=4 end);j.input(1,'skill',1);run(j,25);assert(j.capture().f[2].launched,'Jean E launches')
 local y=game();setup(y,function(s)s.f[1].role=8 end);y.input(1,'skill',1);run(y,75);assert(y.capture().f[1].seals==3,'Yanfei E fills seals');y.input(1,'clickHeavy',1);run(y,30);assert(y.capture().f[1].seals==0,'heavy consumes seals')
 print('TRAIT_CASTER_PASS')
 local l=game();setup(l,function(s)s.f[1].role=11 end);l.input(1,'skill',1);run(l,85);assert(l.capture().f[1].armorLife>0,'Lawachurl E grants one-hit armor');l.input(2,'clickLight',1);run(l,25);assert(l.capture().f[1].hp>88 and l.capture().f[1].armorLife==0,'armor mitigates and is consumed')
 print('TRAIT_ARMOR_PASS')`);
source=source.replace("assert.equal(passed.length,7,'all combat checks must finish');","assert.equal(passed.length,7,'all combat checks must finish');assert.equal(r.logs.filter(l=>l.text?.startsWith('TRAIT_')).length,4,'all trait checks must finish');");
source=source.replace("out+'/combat-verification.json'","out+'/traits-verification.json'");
writeFileSync('work/test-v1-traits-generated.mjs',source);await import('./test-v1-traits-generated.mjs');
