local A=GF_REQUIRE('gf_art');local S=GF_REQUIRE('gf_sim');local R=GF_REQUIRE('gf_roster')
local V=GF_REQUIRE('gf_fview');local G=GF_REQUIRE('gf_gfx');local D=GF_REQUIRE('gf_furina_data')
local j=A.prepare('furina','lo');local count=0
repeat count=count+1;assert(count<600) until j:step(9000)
assert(j.completed==j.total)
local sim=S.new({chars={R[3],R[3]},rounds=2,time=99,seed=21})
local app={frame=0,t=0,scene={sim=sim},layers={front={}}}
local view=V.new(app,{body={},fx={},ghost={},shadow={}},sim.f[1],'lo')
local reserved=0;repeat reserved=reserved+1;assert(reserved<50) until view:reserveBody(320)
assert(#view.slots[1].kids==D.bodyPeak and #view.slots[2].kids==D.bodyPeak)
-- Two simultaneous preparation jobs must not rescale shared frames twice.
local j1,j2=A.prepare('furina','lo'),A.prepare('furina','lo')
assert(j1:step(9000) and j2:step(9000))
local pose=A.pose('furina','lo','idle');local anchor=pose.ax
assert(A.pose('furina','lo','idle').ax==anchor)
for _,state in ipairs({'idle','walk','back','crouch','jumpsq','air','land','block','cblock','hit','airhit','down','getup','win','lose','dash','backdash','throw','thrown','skill','burst','attack'}) do
 view.f.state=state;view.f.coat=0;view.f.frozen=0;view.f.hitstop=0;view.f.airMove=nil
 if state=='attack' then view.f.moveId='light1';view.f.move=view.f.kit.weapon.light1
 elseif state=='skill' then view.f.move=view.f.kit.skill
 elseif state=='burst' then view.f.move=view.f.kit.burst end
 for t=0,100 do
  sim.tick=sim.tick+1;app.frame=sim.tick;app.t=sim.tick/60;view.f.t=t
  local before=G.N.bitmap or 0;view:draw(320)
  assert((G.N.bitmap or 0)-before<=(320+320)*5,'Furina body and auxiliary slice budget')
  assert(#view.slots[1].kids==D.bodyPeak and #view.slots[2].kids==D.bodyPeak,'body expanded during draw')
  local expected=1 -- 20261013: user requires one physical scale across all actions.
  assert(math.abs(view.root.sx-view.f.face*expected)<.0001 and math.abs(view.root.sy-expected)<.0001,'body scale changed between actions')
 end
end
for _,id in ipairs({'airLight','airHeavy'}) do
 view.f.state='air';view.f.airMoveId=id;view.f.airMove=view.f.kit.weapon[id]
 for t=0,30 do view.f.airT=t;assert(A.pose('furina','lo',view:poseFor())) end
end
view.f.airMove=nil;view.f.state='attack';view.f.moveId='throwWhiff'
for t=0,28 do view.f.t=t;assert(A.pose('furina','lo',view:poseFor())) end
view.f.airMove=nil;view.f.state='idle';view.f.t=0
for i=1,12 do view:draw(320) end
local published=view.front.key
view.f.state='hit';view:onHit({heavy=false});view:draw(1)
assert(view.front.key==published and view.flash.used==view.poseImg.n,'flash must follow published frame')
view.f.frozen=10;view:draw(1);assert(view.flash.key==published..':ice')
