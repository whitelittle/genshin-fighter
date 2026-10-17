from pathlib import Path
import shutil
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-q-fx-20261014';O.mkdir(exist_ok=True)
for rel in ['runtime/source/characters/gf_character_clorinde_view.lua','runtime/source/battle/gf_battle_events.lua']:
 p=R/rel;h=O/'history'/rel;h.parent.mkdir(parents=True,exist_ok=True);assert not h.exists(),'one-shot patch';shutil.copy2(p,h)
p=R/'runtime/source/characters/gf_character_clorinde_view.lua';s=p.read_text(encoding='utf8')
s=s.replace(' local image=P.image',' local image=P.image\n local qGun,qBullet="clorindeQGunLegacy","clorindeQBulletLegacy"',1)
s=s.replace(' function P.image(id)',' function P.image(id)\n  if id==qGun then return image(D.effectIds.gun) end\n  if id==qBullet then return image(D.effectIds.bullet) end',1)
s=s.replace('    if shot then','''    if id=='burst' then
     if shot then
      out[1]={id=qGun,x=x+face*170,y=y+180,face=face,alpha=1-age/8,scale=1}
      out[2]={id=qBullet,x=x+face*(170+age*45),y=y+180,face=face,alpha=1-age/8,scale=1}
     else
      add(1,'sword',170,180,1-age/8)
     end
    elseif shot then''',1)
p.write_text(s,encoding='utf8')
p=R/'runtime/source/battle/gf_battle_events.lua';s=p.read_text(encoding='utf8').replace("if a.key=='clorinde' and e.projectileShot then", "if a.key=='clorinde' and (e.projectileShot or e.kind=='burst') then");p.write_text(s,encoding='utf8')
print('restored legacy Q shot/slash effects; impact only from actual hit; no rules changed')
