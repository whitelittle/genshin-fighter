"""Give guard lessons time to react; let approach dashes finish visibly."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-short-press-v24-20261017';OUT=ROOT/'outputs/tutorial-guard-pacing-v25-20261017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True);(OUT/'verification').mkdir(exist_ok=True)
 def edit(rel,before,after,count=1):
  p=OUT/'source'/rel;s=p.read_text(encoding='utf-8');assert s.count(before)==count,(rel,before);p.write_text(s.replace(before,after),encoding='utf-8')
 edit('teaching/gf_training_coach.lua',' self.startX=sim.f[1].x'," sim.f[2].trainingGuardPace=1\n self.startX=sim.f[1].x")
 edit('teaching/gf_training_coach.lua'," if self.age==1 and sim.phase=='fight'", " if self.age==61 and sim.phase=='fight'")
 edit('teaching/gf_training_coach.lua',' if b.state==\'attack\' and b.move then'," if self.age<=60 then self.label='准备一秒：站稳，看清接下来的蓄力动作' end\n if b.state=='attack' and b.move then")
 edit('teaching/gf_training_coach.lua',"if b.t<m.startup then self.label=(self.kind=='crouchGuard' and '压低蓄力：后下方蹲防' or '举拳蓄力：后方向站防')", "if b.t<m.startup then self.label=(self.kind=='evade' or self.kind=='punish') and '举拳蓄力：现在向后退开，走出攻击范围' or (self.kind=='crouchGuard' and '压低蓄力：后下方蹲防' or '举拳蓄力：后方向站防')")
 edit('teaching/gf_training_coach.lua',"self.label='丘丘王正在收招：现在可以反击'", "self.label='丘丘王正在收招：可以向前冲刺，再轻击反击'")
 edit('teaching/gf_training_coach.lua',' if self.age>220 and not self.success then',' if self.age>420 and not self.success then')
 edit('teaching/gf_sim_lumine_training.lua','  add(p.trainingJumpAttack)','  add(p.trainingJumpAttack);add(p.trainingGuardPace)')
 edit('teaching/gf_sim_lumine_training.lua','function T:startSkill(p)', '''function T:startMove(p,id)
 local ok=Base.startMove(self,p,id)
 if ok and p.key=='lawachurl' and p.trainingGuardPace==1 and p.move and (id=='light1' or id=='crouchHeavy') then
  -- Per-action copy: do not modify the shared kit or other lesson opponents.
  local m=clone(p.move);m.startup=id=='light1' and 90 or 96;m.recovery=math.max(m.recovery,120);p.move=m
 end
 return ok
end
function T:startSkill(p)''')
 edit('teaching/gf_training_lesson.lua',"if self.coach and self.lessons[index] then self.coach:prepare(self.lessons[index].kind) end", "if self.coach and self.lessons[index] then self.coach:prepare(self.lessons[index].kind) elseif self.coach then self.scene.sim.f[2].trainingGuardPace=nil end")
 edit('teaching/gf_training_lesson.lua'," or kind=='approach' and math.abs(p.foe.x-p.x)<=20000", " or kind=='approach' and math.abs(p.foe.x-p.x)<=20000 and p.state~='dash' and p.state~='backdash'")
 edit('teaching/gf_training_attack.lua',"if kind=='approach' then return math.abs(d.x-p.x)<=20000 end", "if kind=='approach' then return math.abs(d.x-p.x)<=20000 and p.state~='dash' and p.state~='backdash' end")
 edit('teaching/gf_training_attack.lua','旅行者，先靠近丘丘王，在能碰到它的距离停下来。','旅行者，可以走近，也可以向前冲刺接近丘丘王。冲刺结束后，在能碰到它的距离停下来。')
 edit('teaching/gf_training_lesson.lua','先退开躲过这一击，等到收招提示，再靠近用轻击反击。别在它准备时抢攻哦！','先看清举拳，再退开躲过这一击。看到收招提示，可以向前冲刺接近，再用轻击反击。')
 edit('teaching/gf_training_lesson.lua',"approach='按 A/D 调整距离，靠近后停下'", "approach='A/D 走近，或按 U 向前冲刺，结束后停下'")
 edit('teaching/gf_training_lesson.lua',"keyHints.punish='A/D 退开 → 收招时靠近 → J 轻击'", "keyHints.punish='A/D 退开 → 收招时 U 冲刺接近 → J 轻击'")
 edit('teaching/gf_training_lesson.lua',"approach='推动摇杆靠近，进入距离后松开'", "approach='推动摇杆走近，或点「冲」接近，结束后松开'")
 edit('teaching/gf_training_lesson.lua',"touchHints.punish='摇杆退开 → 收招时靠近 → 点「轻」'", "touchHints.punish='摇杆退开 → 收招时点「冲」接近 → 点「轻」'")
 edit('teaching/gf_training_lesson.lua',"approach='左摇杆调整距离，靠近后停下'", "approach='左摇杆走近，或按 '..p.dash..' 冲刺接近'")
 edit('teaching/gf_training_lesson.lua',"padHints.punish='左摇杆退开 → 收招时靠近 → '..p.light..' 轻击'", "padHints.punish='左摇杆退开 → 收招时 '..p.dash..' 冲刺 → '..p.light..' 轻击'")
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'));changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert set(changed)=={'source/teaching/gf_training_coach.lua','source/teaching/gf_sim_lumine_training.lua','source/teaching/gf_training_lesson.lua','source/teaching/gf_training_attack.lua'}
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8')for p in order),encoding='utf-8')
 r={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'guardReadyTicks':60,'guardStartupTicks':[90,96],'guardRecoveryMinimumTicks':120,'guardRetryAttemptLimit':420,'allArtRenderingAndInputSourcesUnchanged':True,'approach':'walk or dash; do not complete while dash/backdash is active','scope':'local teaching lesson pace; ordinary opponent kit unchanged'}
 (OUT/'build-manifest.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r))
if __name__=='__main__':build()
