__loaders['gf_duo_rework_rules']=function()
return function(K)
 local function copy(t) local c={};for k,v in pairs(t) do c[k]=v end;return c end
 K.characterWeapons=K.characterWeapons or {}
 for _,row in ipairs({{'nahida','catalyst'},{'raidenshogun','polearm'}}) do
  local key,base=row[1],K.weapons[row[2]];local w=copy(base)
  local function move(id,from,values)
   local m=copy(base[from]);for k,v in pairs(values) do m[k]=v end;w[id]=m
  end
  if key=='nahida' then
   move('crouchLight','crouchLight',{startup=5,active=3,recovery=9,damage=23,lunge=0,push=4,box={x=35,y=0,w=145,h=60},fx='burstLow',cancel={'crouchHeavy','skill','burst'},reworkSheet='air',reworkFrames={0,0,1,0}})
   move('crouchHeavy','crouchHeavy',{startup=14,active=5,recovery=23,damage=54,lunge=0,push=4,hitstun=28,box={x=65,y=0,w=205,h=105},fx='burstLow',reworkSheet='air',reworkFrames={2,2,3,2}})
   move('forwardLight','light2',{damage=34,startup=8,recovery=13,lunge=38,box={x=50,y=100,w=190,h=100},reworkSheet='light',reworkFrames={4,5,6,7}})
   move('light3','light2',{damage=45,startup=9,recovery=17,push=13,box={x=70,y=100,w=190,h=150},cancel={'heavy','skill','burst'},reworkSheet='heavy',reworkFrames={0,1,2,3}})
   w.light2=copy(base.light2);w.light2.cancel={'light3','heavy','skill','burst'}
  else
   move('crouchLight','crouchLight',{startup=6,active=3,recovery=11,damage=28,lunge=12,push=7,box={x=60,y=0,w=215,h=45},fx='thrustLow',cancel={'crouchHeavy','skill','burst'},reworkSheet='air',reworkFrames={0,0,1,0}})
   move('crouchHeavy','crouchHeavy',{startup=12,active=4,recovery=25,damage=65,lunge=24,push=10,box={x=50,y=0,w=245,h=65},fx='sweep',reworkSheet='air',reworkFrames={2,2,3,2}})
   move('forwardLight','light1',{startup=8,recovery=14,damage=40,lunge=72,box={x=65,y=140,w=215,h=65},reworkSheet='light',reworkFrames={0,1,2,3}})
  end
  K.characterWeapons[key]=w
 end
 K.duoSkillVariants={
  nahida={
   down={style='zone',startup=13,recovery=19,damage=55,cd=140,delay=20,w=160,h=210,fx='capture',hitstun=24,blockstun=14,push=6,level='mid',energy=5,reworkVariant='seed',fixedOffset=240},
   up={style='projectile',startup=10,recovery=20,damage=52,cd=140,speed=10,w=90,h=100,y=230,life=35,fx='orb',hitstun=22,blockstun=14,push=6,level='mid',energy=5,reworkVariant='leaf'},
  },
  raidenshogun={
   down={style='zone',startup=14,recovery=20,damage=65,cd=150,delay=12,w=180,h=260,fx='eye',hitstun=25,blockstun=15,push=7,level='mid',energy=5,reworkVariant='thunder',fixedOffset=180},
   forward={style='rush',startup=10,recovery=22,damage=72,cd=150,speed=22,dur=8,w=160,h=210,fx='eye',hitstun=24,launch=16,reworkVariant='lunge'},
  },
 }
end
end
