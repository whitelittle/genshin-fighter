from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-sword-tip-20261014';O.mkdir(exist_ok=True)
def edit(rel,fn):
 p=R/rel;h=O/'history'/rel;h.parent.mkdir(parents=True,exist_ok=True)
 assert not h.exists(),'one-shot patch; inspect history before retries'
 shutil.copy2(p,h);p.write_text(fn(p.read_text(encoding='utf8')),encoding='utf8')
# Manual weapon-base and tip markers on the actual fitted source poses.
# Pixel centres/edges are converted to integer simulation coordinates (450 per pixel).
rows=json.loads((R/'runtime/clorinde-import.json').read_text(encoding='utf8'))['sources']
markers=[('light1','light1_2',6,9,(82,21.5),(115.5,21.5)),
 ('light3','light3_2',9,11,(63,36.5),(71.5,42.5)),('light3','light3_3',11,13,(58,37),(64.5,43.5)),
 ('crouchLight','crouchLight_2',6,8,(69,26.5),(77.5,26.5)),('crouchLight','crouchLight_3',8,9,(65,23.5),(74.5,23.5)),
 ('crouchHeavy','crouchHeavy_2',12,14,(57,35),(65.5,38.5)),('crouchHeavy','crouchHeavy_3',14,16,(54,33.5),(61.5,36.5)),
 ('airHeavy','airHeavy_2',10,12,(72,32),(96.5,54.5)),('airHeavy','airHeavy_3',12,14,(64,38),(101.5,75.5)),
 ('skill','skill_4',18,22,(68,27),(77.5,31.5))]
groups={};audit=[]
for move,pose,start,finish,hand,tip in markers:
 row=next(x for x in rows if x['pose']==pose);ax,ay=row['anchor']
 b={'pose':pose,'start':start,'finish':finish,'hx':round((hand[0]-ax)*450),'hy':round((ay-hand[1])*450),'tx':round((tip[0]-ax)*450),'ty':round((ay-tip[1])*450)}
 groups.setdefault(move,[]).append(b);audit.append(dict(b,move=move,source=row['file'],anchor=row['anchor'],basePixel=hand,tipPixel=tip))
(O/'blade-marker-audit.json').write_text(json.dumps({'scope':'manual source-pose markers; artwork/device acceptance pending','markers':audit},ensure_ascii=False,indent=2),encoding='utf8')
def literal(v):
 if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
 if isinstance(v,list):return '{'+','.join(map(literal,v))+'}'
 if isinstance(v,dict):return '{'+','.join('['+literal(k)+']='+literal(x) for k,x in v.items())+'}'
 return str(v)
def rules(s):
 s=s.replace('function() return {','function() local D={',1)
 assert s.rstrip().endswith('} end')
 s=s.rstrip()[:-4]+''' 
D.blades='''+literal(groups)+'''
function D.bladeAt(id,t)
 for _,b in ipairs(D.blades[id] or {}) do if t>=b.start and t<b.finish then return b end end
end
return D
end
'''
 return s
edit('runtime/source/characters/gf_clorinde_rules_data.lua',rules)
def view(s):
 s=s.replace("local tracer=procedural(30,8,0,4,{0,3,20,2,0,14,2,12,4,1,24,0,6,8,1,25,2,5,4,2},\n  {{136,78,245,130},{196,161,255,220},{247,239,255,255}})","local tracer=procedural(30,6,0,3,{0,2,20,2,0,14,2,10,2,1,24,1,6,4,2,25,2,4,2,3},\n  {{136,78,245,130},{190,133,255,170},{255,200,45,255},{255,241,161,255}})")
 s=s.replace("  if id==D.effectIds.gun then return muzzle end","  if id==D.effectIds.gun then return muzzle end\n  if id==D.effectIds.sword then return image(D.effectIds.bullet) end")
 s=s.replace("(f.airMoveId=='airLight' and 1 or 0)","1")
 old="     add(1,id=='airHeavy' and 'down' or id=='heavy' and 'diagonal' or 'sword',170,180,1-age/8)"
 new='''     local blade=Rules.bladeAt(id,t)
     if blade then
      -- Match the body buffer actually being displayed; never float a sword over
      -- an older idle/startup pose while the next body buffer is still loading.
      if v.front and v.front.key~=blade.pose then blade=nil end
      if blade then
       local hx,hy,tx,ty=blade.hx/100,blade.hy/100,blade.tx/100,blade.ty/100
       local dx,dy=tx-hx,ty-hy;local angle=math.atan(dy,dx);local cs,sn=math.cos(angle),math.sin(angle)
       local scale=math.sqrt(dx*dx+dy*dy)/193.5
       out[1]={id=D.effectIds.sword,x=x+face*(tx-(202.5*cs+2.25*sn)*scale),
        y=y+ty-(202.5*sn-2.25*cs)*scale,face=face,scale=scale,alpha=.7,
        rotation=face*math.deg(angle),swordTipX=x+face*tx,swordTipY=y+ty}
      end
     end'''
 assert old in s;s=s.replace(old,new)
 s=s.replace('e.scale,e.alpha,0,math.max','e.scale,e.alpha,e.rotation or 0,math.max')
 return s
edit('runtime/source/characters/gf_character_clorinde_view.lua',view)
edit('runtime/source/characters/gf_character_clorinde.lua',lambda s:s.replace("(id=='airLight' and 1 or 0)",'1'))
def sim(s):
 marker=' function S:skillUpdate(p)'
 helper=''' function S:clorindeSword(p,id,t)
  local blade=D.bladeAt(id,t);if not blade or p.connected then return end
  local a,b,c,d=self:hurtbox(p.foe);if not a then return end
  local hx,hy=p.x+p.face*blade.hx,p.y+blade.hy
  local tx,ty=p.x+p.face*blade.tx,p.y+blade.ty
  local lo,hi=math.min(hx,tx),math.max(hx,tx);local radius=12*C
  -- Integer samples along the actual blade; horizontal bounds stop at its tip.
  for i=0,12 do
   local x=hx+(tx-hx)*i//12;local y=hy+(ty-hy)*i//12
   if ctx.overlap(math.max(lo,x-radius),math.min(hi,x+radius),y-radius,y+radius,a,b,c,d) then
    return self:hit(p,p.foe,p.airMove or p.move,id=='skill' and 'skill' or id:find('Heavy') and 'heavy' or 'light',
     {x=math.max(a,math.min(b,x)),y=math.max(c,math.min(d,y))})
   end
  end
 end
'''
 s=s.replace(marker,helper+marker,1)
 s=s.replace("local box={x=60,y=0,w=220,h=230}","local box={x=60,y=0,w=220,h=230}\n   if window==2 then\n    local result=self:clorindeSword(p,'skill',t)\n    if result then p.skillHitMask=(p.skillHitMask or 0)|(1<<window) end\n    if p.t>=D.skillTotal then self:setState(p,p.y>0 and 'air' or 'idle') end\n    return\n   end",1)
 # E thrust damage remains 50 instead of inheriting the skill's total 85.
 s=s.replace("return self:hit(p,p.foe,p.airMove or p.move,id=='skill'", "local m=p.airMove or p.move\n    if id=='skill' then m={damage=50,hitstun=28,blockstun=16,push=8,level='mid',energy=8,shake=8} end\n    return self:hit(p,p.foe,m,id=='skill'")
 s=s.replace("{x=p.face==1 and a or b,y=math.max(c,math.min(d,p.y+D.shot.skill.y*C))}","{projectileShot=true,x=p.face==1 and a or b,y=math.max(c,math.min(d,p.y+D.shot.skill.y*C))}")
 s=s.replace("{x=p.face==1 and a or b,y=math.max(c,math.min(d,p.y+cfg.y*C))}","{projectileShot=true,x=p.face==1 and a or b,y=math.max(c,math.min(d,p.y+cfg.y*C))}")
 s=s.replace("if p.key~='clorinde' or (p.moveId~='light2' and p.moveId~='heavy') then return oldAttack(self,p) end", "if p.key~='clorinde' then return oldAttack(self,p) end\n  if p.moveId~='light2' and p.moveId~='heavy' and not D.blades[p.moveId] then return oldAttack(self,p) end")
 s=s.replace("if not m.whiff then firearm(self,p,m,t,p.moveId=='heavy' and 'heavy' or 'light') end", "if not m.whiff then\n   if D.blades[p.moveId] then self:clorindeSword(p,p.moveId,t)\n   else firearm(self,p,m,t,p.moveId=='heavy' and 'heavy' or 'light') end\n  end")
 s=s.replace("if p.key~='clorinde' or p.airMoveId~='airLight' then return oldAirAttack(self,p) end", "if p.key~='clorinde' or (p.airMoveId~='airLight' and p.airMoveId~='airHeavy') then return oldAirAttack(self,p) end")
 s=s.replace("  firearm(self,p,m,t,'light')", "  if p.airMoveId=='airHeavy' then self:clorindeSword(p,'airHeavy',t) else firearm(self,p,m,t,'light') end")
 return s
edit('runtime/source/battle/gf_sim_clorinde.lua',sim)
edit('runtime/source/battle/gf_sim_combat.lua',lambda s:s.replace('weapon = a.weapon, fx = m.fx','weapon = a.weapon, fx = m.fx, projectileShot = opts.projectileShot'))
edit('runtime/source/battle/gf_battle_events.lua',lambda s:s.replace("if a.key=='clorinde' and (e.kind=='skill' or e.kind=='burst' or e.kind=='light' or e.kind=='heavy') then", "if a.key=='clorinde' and e.projectileShot then"))
print('gold small projectile; long effect reused at sword tips; blade-bound collision')
