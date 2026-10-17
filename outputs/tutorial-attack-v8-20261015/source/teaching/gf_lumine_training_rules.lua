__loaders['gf_lumine_training_rules']=function()
-- Teaching prototype: real move identities and cancels, shared trial artwork.
return function(K)
 K.characterWeapons.lumine={reach=1,
  light1={pose='slash',startup=10,active=4,recovery=16,damage=32,hitstun=24,blockstun=12,push=5,box={x=40,y=110,w=190,h=130},energy=0,cancel={'light2'}},
  light2={pose='slash',startup=8,active=4,recovery=18,damage=36,hitstun=26,blockstun=12,push=2,box={x=40,y=100,w=200,h=140},energy=0,cancel={'light3'}},
  light3={pose='slash',startup=12,active=5,recovery=24,damage=48,hitstun=26,blockstun=14,push=8,box={x=30,y=100,w=220,h=150},energy=0,cancel={}},
  heavy={pose='slash',startup=26,active=6,recovery=30,damage=70,hitstun=28,blockstun=18,push=12,box={x=30,y=100,w=220,h=160},energy=0,cancel={}},
 }
end
end
