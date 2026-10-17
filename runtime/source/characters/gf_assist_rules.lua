__loaders['gf_assist_rules']=function()
-- Immutable, independent assist moves; no provider or active fighter rules mutate.
local A={cooldown=480,profiles={}}
local function profile(key,t)
 t.key=key;t.active=t.active or 4;t.life=t.life or 44
 t.move={damage=t.damage,hitstun=22,blockstun=14,push=7,level='mid',energy=0,
         launch=t.launch,knockdown=t.knockdown,fx=t.fx,shake=4}
 A.profiles[key]=t
end
profile('nahida',{startup=14,damage=45,life=42,box={x=25,y=30,w=255,h=215},fx='burstSmall',name='草束牵制'})
profile('raidenshogun',{startup=16,damage=50,life=46,box={x=-90,y=0,w=180,h=310},spot=true,fx='eye',name='落雷协击'})
profile('furina',{startup=16,damage=44,box={x=35,y=40,w=280,h=190},fx='burst',name='水波协击'})
profile('kamisatoayaka',{startup=14,damage=46,launch=18,box={x=20,y=0,w=200,h=290},fx='rise',name='冰华上托'})
profile('clorinde',{startup=12,damage=42,life=40,box={x=70,y=115,w=430,h=85},fx='thrust',name='枪击支援'})
profile('arlecchino',{startup=18,damage=52,knockdown=true,box={x=45,y=20,w=270,h=180},fx='sweep',name='镰刃横扫'})
return A
end
