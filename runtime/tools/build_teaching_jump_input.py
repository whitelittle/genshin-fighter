"""Isolated takeoff attack input repair; preserve the accepted asset bank."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-low-air-v21-20261017';OUT=ROOT/'outputs/tutorial-air-input-v22-20261017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
 p=OUT/'source/teaching/gf_sim_lumine_training.lua';text=p.read_text(encoding='utf-8')
 before='  str(p.state);str(p.element);str(p.aura);str(p.moveId);str(p.airMoveId)'
 assert text.count(before)==1
 text=text.replace(before,'  add(p.trainingJumpAttack)\n'+before)
 before=' return Base.fighterTick(self,p)\nend\nfunction T:callSupport()'
 assert text.count(before)==1
 after=''' -- A press during the four takeoff ticks belongs to this jump, even if released.
 -- Keep it on the fighter so deterministic snapshots and rollback retain it.
 if p.key=='lumine' and self.phase=='fight' and p.state=='jumpsq' then
  local attack=p.inPressed&(16|32)
  if attack~=0 then p.trainingJumpAttack=attack&32~=0 and 32 or 16 end
 else p.trainingJumpAttack=nil end
 Base.fighterTick(self,p)
 if p.key=='lumine' and p.state=='air' and p.trainingJumpAttack then
  local attack=p.trainingJumpAttack;p.trainingJumpAttack=nil
  self:startMove(p,attack==32 and 'airHeavy' or 'airLight')
 end
end
function T:callSupport()'''
 text=text.replace(before,after);p.write_text(text,encoding='utf-8')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert changed==['source/teaching/gf_sim_lumine_training.lua'],changed
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8')for p in order),encoding='utf-8');(OUT/'verification').mkdir(exist_ok=True)
 result={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'allArtRenderingInputBindingsAndPaimonSourceUnchanged':True,'ruleChange':'Lumine teaching takeoff attack press retained until first airborne tick; latest press wins; heavy wins simultaneous press'}
 (OUT/'build-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':build()
