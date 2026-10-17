"""New projectile and launcher state must replay deterministically."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'outputs/tutorial-wind-combo-v26-20261017'
sys.path[:0]=[str(ROOT/'runtime/tests')]
from mock_flow import RuntimeClient
RuntimeClient.source=OUT/'genshin_fighter.lua'
if len(sys.argv)>1:OUT=ROOT/sys.argv[1];RuntimeClient.source=OUT/'genshin_fighter.lua'
c=RuntimeClient()
r=c.lua('''(function()
local S=GF_REQUIRE('gf_sim_lumine_training');local R=GF_REQUIRE('gf_character_registry')
local function make()local s=S.new({chars={R.byKey.lumine,R.byKey.lawachurl},training=true,seed=21});s.phase='fight';s.freeze=0;for _,p in ipairs(s.f)do s:setState(p,'idle');p.x=(p.id==1 and -9000 or 9000)end;return s end
local n=0
for _,mask in ipairs({64,65,66})do
 local s=make();s:step(mask,0);for i=1,24 do s:step(0,0)end
 local snap=S.snapshot(s);assert(s:hash()==snap:hash())
 if #s.proj>0 then local x=s.proj[1].x;s.proj[1].x=x+1;assert(s:hash()~=snap:hash());s.proj[1].x=x end
 for i=1,180 do s:step(0,0);snap:step(0,0);assert(s:hash()==snap:hash())end;n=n+1
end
local s=make();s:step(34,0);for i=1,80 do s:step(0,0);if s.f[1].trainingLaunchHit then break end end
assert(s.f[1].trainingLaunchHit);local snap=S.snapshot(s);s.f[1].trainingLaunchHit=nil;assert(s:hash()~=snap:hash());s.f[1].trainingLaunchHit=true
s:step(9,0);snap:step(9,0);assert(s:hash()==snap:hash());assert(s.f[1].trainingChase)
for i=1,100 do s:step(0,0);snap:step(0,0);assert(s:hash()==snap:hash())end
-- An air-light skill cancel must not leave its old body as a visual override.
s=make();local p=s.f[1];s:setState(p,'air');p.y=10000;p.vy=0;s:startMove(p,'airLight');p.connected=true;p.inPressed=64
assert(s:tryCancel(p,p.airMove));assert(p.state=='skill' and not p.airMove and not p.airMoveId)
local P=GF_REQUIRE('gf_character_lumine_training');assert(P.poseFor({f=p})=='skill_0')
return n+2 end)()''')
result={'clientSha256':hashlib.sha256(RuntimeClient.source.read_bytes()).hexdigest(),'cases':r,'projectileAndJumpCancelReplay':True,'hashDistinguishesNewState':True,'airSkillClearsPreviousBody':True}
(OUT/'verification/wind-combo-snapshots.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
