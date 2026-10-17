__loaders['gf_character_furina_rules']=function()
local D=require('gf_furina_rules_data')
return function(K)
 local function copy(t)local r={};for k,v in pairs(t) do r[k]=v end;return r end
 local w=copy(K.weapons.sword);w.reach=1
 for _,id in ipairs({'light1','light2','light3','heavy','crouchLight','crouchHeavy','airLight','airHeavy'}) do
  local m=copy(w[id]);local cd=D[id].combat
  m.startup,m.active,m.recovery=cd.startup,cd.active,cd.recovery
  m.box={x=cd.box[1],y=cd.box[2],w=cd.box[3],h=cd.box[4]};m.level=cd.level
  m.lunge=cd.lunge or 0;m.projectile=nil;m.fx=nil;m.airPush=nil
  w[id]=m
 end
 K.characterWeapons=K.characterWeapons or {};K.characterWeapons.furina=w
 K.skills.furina={style='salon',startup=18,active=6,recovery=24,damage=70,cd=140,hitstun=24,fx='salon'}
 K.bursts.furina={style='salonCinematic',damage=260,hits=3,range=380,fx='fanfare',confirm=12,finish=158}
 K.body.furina=copy(K.body.default);K.body.furina.flightHeights=D.flightHeights;K.body.furina.getupTicks=38
end
end
