__loaders['gf_mode_arcade']=function()
local M={}
-- Campaign state lives outside a single two-fighter simulation.
function M.new(mine,roster,time)
 local pool={}
 for _,c in ipairs(roster) do if c.key~=mine then pool[#pool+1]=c.key end end
 local seed=math.floor(time*1000)%9973+1
 for i=#pool,2,-1 do
  seed=(seed*1103515245+12345)&0x7fffffff
  local j=seed%i+1;pool[i],pool[j]=pool[j],pool[i]
 end
 local ladder={}
 for i=1,math.min(6,#pool) do ladder[i]=pool[i] end
 return {ladder=ladder,step=1,player=mine,score=0}
end
function M.battle(ar,stages)
 local boss=ar.step==#ar.ladder
 return {chars={ar.player,ar.ladder[ar.step]},stage=stages[(ar.step-1)%#stages+1],
  mode='arcade',arcade=ar,cpu={false,boss and 4 or math.min(4,1+(ar.step+1)//2)}},boss
end
function M.recordWin(ar,stats)
 ar.score=ar.score+1000+(stats.maxCombo or 0)*50
 return ar.step>=#ar.ladder
end
function M.advance(ar) ar.step=ar.step+1;return ar end
return M
end
