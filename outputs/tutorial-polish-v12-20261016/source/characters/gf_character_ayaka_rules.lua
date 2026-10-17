__loaders['gf_character_ayaka_rules']=function()
local D=require('gf_ayaka_rules_data')
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
 K.characterWeapons=K.characterWeapons or {};K.characterWeapons.kamisatoayaka=w
 K.skills.kamisatoayaka={style='iceBloomDelivered',startup=12,active=8,recovery=18,damage=85,cd=150,hitstun=28,fx='iceBloom'}
 K.bursts.kamisatoayaka={style='soumetsuCinematic',damage=290,hits=3,range=380,fx='soumetsu',confirm=52,finish=152}
 K.body.kamisatoayaka=copy(K.body.default);K.body.kamisatoayaka.getupTicks=40
end
end
