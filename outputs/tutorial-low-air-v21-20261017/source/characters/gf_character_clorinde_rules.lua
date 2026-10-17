__loaders['gf_character_clorinde_rules']=function()
local D=require('gf_clorinde_rules_data')
return function(K)
 local function copy(t)local r={};for k,v in pairs(t)do r[k]=v end;return r end
 local w=copy(K.weapons.sword);w.reach=1
 for _,id in ipairs({'light1','light2','light3','heavy','crouchLight','crouchHeavy','airLight','airHeavy'})do local m=copy(w[id]);local d=D[id]
 m.startup,m.active,m.recovery=d.startup,d.active,d.recovery;m.level=d.level;m.damage=d.damage or m.damage;m.projectile=nil;m.fx=nil;m.airPush=nil;w[id]=m end
 K.characterWeapons=K.characterWeapons or {};K.characterWeapons.clorinde=w
 K.skills.clorinde={style='delivered',startup=12,active=8,recovery=18,damage=85,cd=150,hitstun=28,fx='lastlight'}
 K.bursts.clorinde={style='deliveredCinematic',damage=290,hits=3,range=380,confirm=6,finish=162}
 K.body.clorinde=copy(K.body.clorinde or K.body.default);K.body.clorinde.getupTicks=D.getupTotal
end
end
