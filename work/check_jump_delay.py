exec(open('work/check_normal_air.py',encoding='utf-8-sig').read().split('for hz in')[0])
c=RuntimeClient();c.env.GF_FIRST_SCENE='fight';c.env.GF_FIRST_ARGS=c.rt.table_from({'chars':c.rt.table_from(['lumine','lawachurl']),'mode':'training','seed':21});wait(c,"GF_APP() and GF_APP().scene and GF_APP().scene.state=='run' and GF_APP().scene.sim.phase=='fight' and not GF_APP().trans")
for delay in range(1,8):
 c.lua("(function()local s=GF_APP().scene;local a=s.sim.f[1];s.sim:setState(a,'idle');a.y=0;a.vy=0;a.airMove=nil;a.airMoveId=nil;a.inPrev=0;a.releaseMask=0;return true end)()")
 c.run(.2);c.key('SPACE',True)
 for _ in range(delay):c.step()
 c.key('J',True);c.step();c.key('J',False);c.key('SPACE',False);c.run(.15)
 print(delay,c.lua("GF_APP().scene.sim.f[1].airMoveId or 'none'"))
 c.run(1)
