__loaders['gf_lumine_training_rules']=function()
-- Teaching prototype: real move identities and cancels, shared trial artwork.
return function(K)
 K.characterWeapons.lumine={reach=1,
  light1={pose='slash',startup=10,active=4,recovery=16,damage=32,hitstun=24,blockstun=12,push=5,box={x=40,y=110,w=190,h=130},energy=0,cancel={'light2'}},
  light2={pose='slash',startup=8,active=4,recovery=18,damage=36,hitstun=26,blockstun=12,push=2,box={x=40,y=100,w=200,h=140},energy=0,cancel={'light3'}},
  light3={pose='slash',startup=12,active=5,recovery=24,damage=48,hitstun=26,blockstun=14,push=8,box={x=30,y=100,w=220,h=150},energy=0,cancel={}},
  heavy={pose='slash',startup=26,active=6,recovery=30,damage=70,hitstun=28,blockstun=18,push=12,box={x=30,y=100,w=220,h=160},energy=0,cancel={}},
  crouchLight={pose='slash',startup=9,active=4,recovery=16,damage=28,hitstun=18,blockstun=10,push=3,level='low',box={x=15,y=15,w=215,h=100},energy=4,cancel={}},
  crouchHeavy={pose='slash',startup=22,active=5,recovery=28,damage=58,hitstun=24,blockstun=14,push=6,level='low',knockdown=true,box={x=10,y=10,w=240,h=105},energy=8,cancel={}},
  airLight={pose='slash',startup=7,active=8,recovery=12,damage=30,hitstun=20,blockstun=12,push=4,level='high',box={x=5,y=-40,w=215,h=185},energy=4,cancel={}},
  airHeavy={pose='slash',startup=14,active=10,recovery=20,damage=60,hitstun=25,blockstun=16,push=6,level='high',spike=12,box={x=5,y=-100,w=235,h=230},energy=8,cancel={}},
 }
 K.skills.lumine={name='元素掌击',style='trainingPalm',startup=18,dur=6,recovery=24,cd=150,damage=54,hitstun=24,fx='wind'}
 K.bursts.lumine={name='元素释放',style='trainingBurst',startup=32,active=8,recovery=34,damage=160,hits=1,range=390,fx='wind'}
 -- New names are used only by the isolated Traveler teaching simulator.
 K.reactionName.quicken='原激化';K.reactionName.aggravate='超激化';K.reactionName.spread='蔓激化'
 K.reactionName.hyperbloom='超绽放';K.reactionName.burgeon='烈绽放';K.reactionName.shatter='碎冰'
end
end
