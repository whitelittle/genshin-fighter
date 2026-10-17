"""Preserve sub-tick input edges and resolve simultaneous jump attacks."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'outputs/tutorial-guard-v23-20261017';OUT=ROOT/'outputs/tutorial-short-press-v24-20261017'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True);(OUT/'verification').mkdir(exist_ok=True)
 def edit(rel,before,after):
  p=OUT/'source'/rel;s=p.read_text(encoding='utf-8');assert s.count(before)==1,(rel,before);p.write_text(s.replace(before,after),encoding='utf-8')
 edit('input/gf_input.lua','        pad.counts[bit] = c','''        -- A down/up pair between simulation ticks is still one physical press.
        if down then pad.pulse = (pad.pulse or 0) | bit end
        pad.counts[bit] = c''')
 edit('input/gf_touch.lua',"down = function() pad.touch = pad.touch | btn.bit; self.held[btn.id] = 6 end,", "down = function() pad.touch = pad.touch | btn.bit; pad.pulse = (pad.pulse or 0) | btn.bit; self.held[btn.id] = 6 end,")
 edit('input/gf_touch.lua',"            click = function() if btn.id == 'SK' or btn.id == 'BU' then pad.pulse = (pad.pulse or 0) | btn.bit end end,\n",'')
 edit('teaching/gf_sim_lumine_training.lua','function T:neutral(p)\n Base.neutral(self,p)', '''function T:neutral(p)
 -- A fresh jump plus attack in one sample belongs to the upcoming jump.
 -- Keep explicit skill/burst/throw/dash priorities and all other fighters intact.
 local now,pr=p.inNow,p.inPressed
 if p.key=='lumine' and pr&1~=0 and now&2==0 and pr&(16|32)~=0 and pr&(64|128|256|512)==0 then
  self:setState(p,'jumpsq')
  local forward=p.face>0 and 8 or 4;local back=p.face>0 and 4 or 8
  p.jumpDir=now&forward~=0 and 1 or now&back~=0 and -1 or 0
  p.trainingJumpAttack=pr&32~=0 and 32 or 16
  return
 end
 Base.neutral(self,p)''')
 order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
 changed=[p for p in order if sha(BASE/p)!=sha(OUT/p)]
 assert set(changed)=={'source/input/gf_input.lua','source/input/gf_touch.lua','source/teaching/gf_sim_lumine_training.lua'}
 (OUT/'genshin_fighter.lua').write_text('\n'.join((OUT/p).read_text(encoding='utf-8')for p in order),encoding='utf-8')
 result={'clientSha256':sha(OUT/'genshin_fighter.lua'),'baselineSha256':sha(BASE/'genshin_fighter.lua'),'onlyChangedSourceFiles':changed,'allArtRulesPaimonAndRenderingSourcesUnchanged':True,'behavior':'latch short keyboard/touch downs until next input tick; fresh simultaneous jump+light/heavy enters takeoff with existing attack buffer; touch skills pulse on down once, not again on click'}
 (OUT/'build-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':build()
