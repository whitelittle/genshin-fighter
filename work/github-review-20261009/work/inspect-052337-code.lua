local loadingRegistry={}
local function loadingKey(parent)
 if parent.name=='Sprite' then return parent.parent.parent.name..'/Art/Sprite' end
 if parent.name=='Phoenix' then return parent.parent.name..'/Phoenix' end
 return parent.name
end
local function loadingFind(parent,name)
 local pool=loadingRegistry[loadingKey(parent)]
 return pool and pool[name] or parent:FindChild(name)
end

local loadingJobs={{path={"Keqing","Art","Sprite"},prefix="P",count=3964},{path={"Keqing","Phoenix"},prefix="F",count=338},{path={"Diluc","Art","Sprite"},prefix="P",count=3964},{path={"Diluc","Phoenix"},prefix="F",count=338}}


local root,actors,hpBars,status,timerText,stats
local tick,acc,phase,round,wins,remaining,freeze,intermission=0,0,'fight',1,{0,0},60,0,0
local stage,roleChoice=1,{1,2}
local roundIntro=90
local input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
local aiEnabled=false
local seat,onlineReady,joined,sendSeq,stateSeq,receivedState=0,false,false,0,0,0
local lastInputSeq={0,0}
local controls,controlPlayer={},1
local publishState
local replaying=false
local originalPrint=print
local function print(...)if not replaying then originalPrint(...)end end

local directions,lastDirection,motionMove={},5,nil
local heldButtons={}
local commands={{sequence={2,3,6,2,3,6},button='heavy',move='super'},{sequence={6,2,3},button='heavy',move='rising'},{sequence={2,3,6},button='light',move='special'},{sequence={2,3,6},button='heavy',move='special'}}
local specs={
 {speed=235,light={startup=6,active=3,recovery=12,range=112,damage=8,stun=16,push=24},low={startup=7,active=4,recovery=16,range=120,damage=7,stun=17,push=18,height='low'},heavy={startup=17,active=4,recovery=25,range=150,damage=19,stun=27,push=45,height='high'},special={startup=11,active=8,recovery=26,range=138,damage=16,stun=25,push=36,dash=470}},
 {speed=180,light={startup=12,active=4,recovery=18,range=138,damage=12,stun=20,push=30},low={startup=13,active=4,recovery=21,range=145,damage=10,stun=20,push=22,height='low'},heavy={startup=25,active=5,recovery=31,range=180,damage=25,stun=33,push=52,height='high'},special={startup=27,active=7,recovery=35,range=240,damage=22,stun=31,push=48,}}
}
local f={{},{}}
local moveNames={{light='\229\191\171\229\137\145',low='\228\184\139\230\174\181\230\150\169',heavy='\233\135\141\229\135\187',special='\233\155\183\233\156\134\231\170\129\232\191\155\230\150\169',rising='\233\155\183\229\133\137\229\141\135\230\150\169'},{light='\230\140\165\229\137\145',low='\228\184\139\230\174\181\230\150\169',heavy='\233\135\141\229\135\187',special='\231\129\171\231\132\176\233\135\141\230\150\169',rising='\231\131\136\231\132\176\229\141\135\230\150\169'}}
local phaseNames={['KEQING WINS MATCH']='\229\136\187\230\153\180\232\181\162\229\190\151\230\175\148\232\181\155',['DILUC WINS MATCH']='\232\191\170\229\141\162\229\133\139\232\181\162\229\190\151\230\175\148\232\181\155',['DRAW ROUND']='\230\156\172\229\155\158\229\144\136\229\185\179\229\177\128',['KEQING WINS ROUND']='\229\136\187\230\153\180\232\181\162\229\190\151\230\156\172\229\155\158\229\144\136',['DILUC WINS ROUND']='\232\191\170\229\141\162\229\133\139\232\181\162\229\190\151\230\156\172\229\155\158\229\144\136'}
specs[1].rising={startup=8,active=7,recovery=32,range=100,heightRange=190,damage=14,stun=27,push=25}
specs[2].rising={startup=12,active=8,recovery=38,range=125,heightRange=190,damage=18,stun=30,push=32}
specs[1].super={startup=16,active=10,recovery=38,range=310,heightRange=220,damage=38,stun=40,push=65}
specs[2].super={startup=24,active=12,recovery=45,range=370,heightRange=220,damage=44,stun=44,push=75}
moveNames[1].super='\229\164\169\232\161\151\229\183\161\230\184\184';moveNames[2].super='\233\187\142\230\152\142'
specs[1].overhead={startup=21,active=4,recovery=26,range=140,damage=18,stun=26,push=42,height='high'}
specs[2].overhead={startup=29,active=5,recovery=32,range=175,damage=24,stun=32,push=50,height='high'}
moveNames[1].overhead='\228\184\138\230\174\181\230\150\169';moveNames[2].overhead='\228\184\138\230\174\181\230\150\169'

specs[1].heavy.height=nil;specs[2].heavy.height=nil
 specs[1].special={startup=9,active=1,recovery=17,range=0,damage=0,stun=0,push=0}
 specs[1].teleport={startup=10,active=5,recovery=26,range=145,damage=16,stun=28,push=32}
 specs[2].special={startup=18,active=5,recovery=24,range=180,damage=10,stun=32,push=15}
 specs[2].e2={startup=14,active=5,recovery=25,range=190,damage=11,stun=34,push=15}
 specs[2].e3={startup=21,active=6,recovery=33,range=210,damage=18,stun=36,push=40}
 specs[2].super.active=36;specs[2].super.range=570;specs[2].super.heightRange=100
 moveNames[1].special='\233\155\183\230\165\148';moveNames[1].teleport='\230\152\159\230\150\151\229\189\146\228\189\141'
 moveNames[2].special='\233\128\134\231\132\176\228\185\139\229\136\131\194\183\228\184\128';moveNames[2].e2='\233\128\134\231\132\176\228\185\139\229\136\131\194\183\228\186\140';moveNames[2].e3='\233\128\134\231\132\176\228\185\139\229\136\131\194\183\228\184\137'
specs[3]={speed=220,light={startup=8,active=4,recovery=16,range=165,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=180,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=210,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=230,damage=14,stun=30,push=40},super={startup=24,active=10,recovery=42,range=360,heightRange=230,damage=40,stun=42,push=65}}
moveNames[3]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\233\156\156\232\162\173",super="\229\135\155\229\134\189\232\189\174\232\136\158"}
specs[4]={speed=215,light={startup=9,active=4,recovery=16,range=135,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=150,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=180,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=16,active=6,recovery=28,range=200,damage=15,stun=30,push=40},super={startup=24,active=10,recovery=42,range=330,heightRange=230,damage=40,stun=42,push=65}}
moveNames[4]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\233\163\142\229\142\139\229\137\145",super="\232\146\178\229\133\172\232\139\177\228\185\139\233\163\142"}
specs[5]={speed=185,light={startup=10,active=4,recovery=16,range=225,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=240,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=270,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=18,active=6,recovery=28,range=290,damage=16,stun=30,push=40},super={startup=24,active=10,recovery=42,range=420,heightRange=230,damage=40,stun=42,push=65}}
moveNames[5]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\232\185\166\232\185\166\231\130\184\229\188\185",super="\232\189\176\232\189\176\231\129\171\232\138\177"}
specs[6]={speed=190,light={startup=11,active=4,recovery=16,range=235,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=250,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=280,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=20,active=6,recovery=28,range=300,damage=17,stun=30,push=40},super={startup=24,active=10,recovery=42,range=430,heightRange=230,damage=40,stun=42,push=65}}
moveNames[6]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\232\139\141\233\155\183",super="\232\148\183\232\150\135\231\154\132\233\155\183\229\133\137"}
specs[7]={speed=205,light={startup=8,active=4,recovery=16,range=275,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=290,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=320,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=22,active=6,recovery=28,range=340,damage=14,stun=30,push=40},super={startup=24,active=10,recovery=42,range=470,heightRange=230,damage=40,stun=42,push=65}}
moveNames[7]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\229\177\177\230\179\189\233\186\159\232\191\185",super="\233\153\141\228\188\151\229\164\169\229\141\142"}
specs[8]={speed=200,light={startup=9,active=4,recovery=16,range=205,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=220,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=250,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=270,damage=16,stun=30,push=40},super={startup=24,active=10,recovery=42,range=400,heightRange=230,damage=40,stun=42,push=65}}
moveNames[8]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\228\184\185\228\185\166\231\171\139\231\186\166",super="\229\135\173\230\173\164\231\187\147\229\165\145"}
specs[9]={speed=250,light={startup=10,active=4,recovery=16,range=145,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=160,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=16,active=6,recovery=28,range=210,damage=17,stun=30,push=40,dash=650},super={startup=24,active=10,recovery=42,range=340,heightRange=230,damage=40,stun=42,push=65}}
moveNames[9]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\233\163\142\232\189\174\228\184\164\231\171\139",super="\233\157\150\229\166\150\229\130\169\232\136\158"}
specs[10]={speed=230,light={startup=11,active=4,recovery=16,range=125,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=140,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=170,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=18,active=6,recovery=28,range=190,damage=18,stun=30,push=40,dash=380},super={startup=24,active=10,recovery=42,range=320,heightRange=230,damage=40,stun=42,push=65}}
moveNames[10]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\232\157\182\229\188\149\230\157\165\231\148\159",super="\229\174\137\231\165\158\231\167\152\230\179\149"}
specs[11]={speed=150,light={startup=8,active=4,recovery=16,range=175,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=190,damage=8,stun=20,push=22,height='low'},heavy={startup=22,active=5,recovery=28,range=220,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=20,active=6,recovery=28,range=240,damage=24,stun=30,push=40},super={startup=24,active=10,recovery=42,range=370,heightRange=230,damage=40,stun=42,push=65}}
moveNames[11]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\229\178\169\232\186\175\229\134\178\230\146\158",super="\229\177\177\229\180\169\233\156\135\229\156\176"}
local roleClass={}
roleClass[12]='trap'
specs[12]={speed=225,light={startup=8,active=4,recovery=16,range=180,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=21,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=340,damage=17,stun=30,push=40},super={startup=24,active=10,recovery=42,range=450,heightRange=230,damage=40,stun=42,push=65}}
moveNames[12]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\233\135\142\229\185\178\229\189\185\229\146\146\194\183\230\157\128\231\148\159\230\168\177",super="\229\164\167\229\175\134\230\179\149\194\183\229\164\169\231\139\144\230\152\190\231\156\159"}
roleClass[13]='shielddash'
specs[13]={speed=225,light={startup=8,active=4,recovery=16,range=130,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=21,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=180,damage=17,stun=30,push=40,dash=350},super={startup=24,active=10,recovery=42,range=290,heightRange=230,damage=40,stun=42,push=65}}
moveNames[13]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\229\145\156\229\150\181\231\148\186\233\163\158\232\182\179",super="\231\167\152\230\179\149\194\183\230\131\138\229\150\156\231\137\185\230\180\190"}
roleClass[14]='launch'
specs[14]={speed=225,light={startup=8,active=4,recovery=16,range=130,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=21,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=180,damage=17,stun=30,push=40},super={startup=24,active=10,recovery=42,range=290,heightRange=230,damage=40,stun=42,push=65}}
moveNames[14]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\231\165\158\233\135\140\230\181\129\194\183\229\134\176\229\141\142",super="\231\165\158\233\135\140\230\181\129\194\183\233\156\156\231\129\173"}
roleClass[15]='stance'
specs[15]={speed=225,light={startup=8,active=4,recovery=16,range=130,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=21,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=180,damage=17,stun=30,push=40},super={startup=24,active=10,recovery=42,range=290,heightRange=230,damage=40,stun=42,push=65}}
moveNames[15]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\231\165\158\233\135\140\230\181\129\194\183\233\149\156\232\138\177",super="\231\165\158\233\135\140\230\181\129\194\183\230\176\180\229\155\191"}
roleClass[16]='bruiser'
specs[16]={speed=180,light={startup=8,active=4,recovery=16,range=130,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=25,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=180,damage=22,stun=30,push=40},super={startup=24,active=10,recovery=42,range=290,heightRange=230,damage=40,stun=42,push=65}}
moveNames[16]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\233\173\148\230\157\128\231\187\157\230\138\128\194\183\232\181\164\231\137\155\229\143\145\231\160\180\239\188\129",super="\230\156\128\230\129\182\233\172\188\231\142\139\194\183\228\184\128\230\150\151\232\189\176\228\184\180\239\188\129\239\188\129"}
roleClass[17]='heal'
specs[17]={speed=225,light={startup=8,active=4,recovery=16,range=130,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=21,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=180,damage=12,stun=30,push=40},super={startup=24,active=10,recovery=42,range=290,heightRange=230,damage=40,stun=42,push=65}}
moveNames[17]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\230\181\183\230\156\136\228\185\139\232\170\147",super="\230\181\183\228\186\186\229\140\150\231\190\189"}
roleClass[18]='beam'
specs[18]={speed=225,light={startup=8,active=4,recovery=16,range=180,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=21,active=5,recovery=28,range=385,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=20,active=6,recovery=28,range=340,damage=17,stun=30,push=40},super={startup=24,active=10,recovery=42,range=450,heightRange=230,damage=40,stun=42,push=65}}
moveNames[18]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\230\179\170\230\176\180\229\149\138\239\188\140\230\136\145\229\191\133\229\129\191\232\191\152",super="\230\189\174\230\176\180\229\149\138\239\188\140\230\136\145\229\183\178\229\189\146\230\157\165"}
roleClass[19]='mark'
specs[19]={speed=225,light={startup=8,active=4,recovery=16,range=180,damage=9,stun=18,push=24},low={startup=10,active=4,recovery=20,range=135,damage=8,stun=20,push=22,height='low'},heavy={startup=21,active=5,recovery=28,range=190,damage=21,stun=30,push=45},overhead={startup=25,active=4,recovery=28,range=150,damage=18,stun=26,push=35,height='high'},rising={startup=12,active=6,recovery=34,range=140,heightRange=200,damage=16,stun=30,push=32},special={startup=14,active=6,recovery=28,range=340,damage=17,stun=30,push=40},super={startup=24,active=10,recovery=42,range=450,heightRange=230,damage=40,stun=42,push=65}}
moveNames[19]={light='\230\153\174\233\128\154\230\148\187\229\135\187',low='\228\184\139\230\174\181\230\148\187\229\135\187',heavy='\233\135\141\229\135\187',rising='\229\141\135\231\169\186\230\148\187\229\135\187',overhead='\228\184\138\230\174\181\230\148\187\229\135\187',special="\230\137\128\233\151\187\233\129\141\232\174\161",super="\229\191\131\230\153\175\229\185\187\230\136\144"}

local function recordDirection()
 local x=(input.right and 1 or 0)-(input.left and 1 or 0)
 local d=input.down and (x+2) or (x+5)
 if d~=lastDirection then directions[#directions+1]={d=d,t=tick};lastDirection=d end
 while #directions>32 do table.remove(directions,1)end
end
local function setDirection(key,value)input[key]=value;recordDirection()end
local function matchesMotion(sequence)
 local nextStep=#sequence;local newer=tick
 for n=#directions,1,-1 do
  local event=directions[n];local d=event.d
  if f[controlPlayer].face==-1 then if d==1 or d==3 then d=4-d elseif d==4 or d==6 then d=10-d end end
  if tick-event.t>(#sequence>3 and 42 or 24) or newer-event.t>12 then return false end
  if d~=5 then
   if d~=sequence[nextStep] then return false end
   if nextStep==#sequence and tick-event.t>8 then return false end
   nextStep=nextStep-1;newer=event.t
   if nextStep==0 then return true end
  end
 end
 return false
end
local function pressAttack(button)
 recordDirection()
 for _,command in ipairs(commands)do
  if command.button==button and matchesMotion(command.sequence)then
   input.light=0;input.heavy=0;input.special=12;motionMove=command.move;directions={};print('COMMAND '..command.move);return
  end
 end
 input[button]=12
end
local function clamp(x,a,b)return math.max(a,math.min(b,x))end
local function ready(i)local a=f[i];return a.hp>0 and a.stun<=0 and a.down<=0 and a.wake<=0 and not a.launched and not a.attack end
local function canCancel(i,kind)
 local a=f[i];local atk=a.attack
 if not atk or not atk.connected or a.stun>0 or a.down>0 or a.wake>0 or a.y>0 then return false end
 if atk.kind~='light' and atk.kind~='low' then return false end
 local s=specs[f[i].role][atk.kind];local t=atk.t-(atk.startup+s.active)
 if t<0 or t>8 then return false end
 return (kind=='light' and atk.kind=='light' and a.chainCount<2) or kind=='heavy' or kind=='special' or kind=='rising' or kind=='super' or kind=='overhead' or kind=='teleport'
end
local function startAttack(i,kind)
 local a=f[i]
 if kind=='special' and a.role==1 and (a.markLife or 0)>0 then kind='teleport' end
 if kind=='special' and a.role==2 then
  local current=a.attack
  local stage=((a.eWindow or 0)>0 or current and(current.kind=='special' or current.kind=='e2'))and(a.eStage or 0)+1 or 1
  if stage>3 then return false end
  if stage==2 then kind='e2' elseif stage==3 then kind='e3' end
 end
 if kind=='heavy' then
 local c=controls[i] and controls[i].input or input
 if c.down then kind='rising'elseif(a.face==1 and c.right)or(a.face==-1 and c.left)then kind='overhead'end
end
local cancel=canCancel(i,kind)
 if a.role==2 and a.attack and(kind=='e2' or kind=='e3')then
  local old=a.attack;local os=specs[2][old.kind]
  cancel=a.stun<=0 and a.down<=0 and old.t>=old.startup+os.active and old.t<=old.startup+os.active+os.recovery
 end
 if not ready(i) and not cancel then return false end
 if (kind=='special' or kind=='teleport' or kind=='e2' or kind=='e3' or kind=='rising' or kind=='low') and a.y>0 then return false end
 if kind=='super' and (a.meter<100 or a.y>0) then return false end
 if kind=='special' and a.role==9 and (a.eCharges or 2)<=0 then return false end
 if kind=='special' and a.role==10 and (a.buffLife or 0)>0 then return false end
 if kind=='special' and a.role==9 then a.eCharges=(a.eCharges or 2)-1;a.eRecharge=240 end
 if kind=='super' then a.meter=a.meter-100;print('SUPER '..i)end
 a.chainCount=cancel and a.chainCount+1 or 1
 local startup=specs[f[i].role][kind].startup
 if cancel and kind=='heavy' then startup=math.max(8,startup-6)end
 if a.role==2 and(kind=='special' or kind=='e2' or kind=='e3')then a.eStage=kind=='special' and 1 or(kind=='e2' and 2 or 3);a.eWindow=45 end
 if a.role==7 and kind=='special' then a.x=clamp(a.x-a.face*85,-535,535)end
 a.attack={kind=kind,t=0,hit=false,connected=false,startup=startup};a.crouch=kind=='low';a.block=false;return true
end
-- Editable initial profiles: local coordinates originate at the feet.
-- [line 175 data omitted, len=3872782] local Collision={results={},profiles={},moves={},stageData={
function Collision.stageId(seed,number) return 1 end
for role=1,45 do Collision.profiles[role]={push=26,width=26,height=166,crouch=94}end
for _,role in ipairs({5,19,39})do Collision.profiles[role]={push=25,width=25,height=146,crouch=84}end
Collision.profiles[11]={push=42,width=40,height=202,crouch=130}
function Collision.world(a,l,b,r,t)
 if a.face<0 then l,r=-r,-l end
 return {a.x+l,a.y+b,a.x+r,a.y+t}
end
function Collision.overlap(a,b)
 return a[1]<=b[3]and a[3]>=b[1]and a[2]<=b[4]and a[4]>=b[2]
end
function Collision.hurt(a)
 local p=Collision.profiles[a.role];local height=a.crouch and p.crouch or p.height
 if a.down>0 then height=38 end
 return Collision.world(a,-p.width,0,p.width,height)
end
function Collision.attack(a,s,range)
 local roleMoves=Collision.moves[a.role];local override=roleMoves and roleMoves[a.attack.kind]
 if override then return Collision.world(a,override[1],override[2],override[3],override[4])end
 -- The travelling firebird owns a box at its current simulation position.
 -- Decorative trails do not turn the space behind it into a beam hitbox.
 if a.role==2 and a.attack.kind=='super'then
  local center=95+math.max(0,a.attack.t-a.attack.startup)*14
  return Collision.world(a,center-78,10,center+78,128)
 end
 local bottom,top=42,142
 if s.height=='low'then bottom,top=0,66
 elseif s.height=='high'then bottom,top=90,174
 elseif a.attack.kind=='rising'then bottom,top=20,s.heightRange or 200
 elseif a.attack.kind=='super'then bottom,top=12,s.heightRange or 190 end
 return Collision.world(a,8,bottom,range,top)
end
function Collision.push(a,b)
 if a.down>0 or b.down>0 then return end
 local pa,pb=Collision.profiles[a.role],Collision.profiles[b.role]
 local aa={a.x-pa.push,a.y,a.x+pa.push,a.y+pa.height}
 local bb={b.x-pb.push,b.y,b.x+pb.push,b.y+pb.height}
 if not Collision.overlap(aa,bb)then return end
 local direction=b.x>=a.x and 1 or -1;local penetration=pa.push+pb.push-math.abs(b.x-a.x)
 local ax,bx=a.x,b.x
 a.x=clamp(ax-direction*penetration/2,-535,535);b.x=clamp(bx+direction*penetration/2,-535,535)
 local remaining=pa.push+pb.push-math.abs(b.x-a.x)
 if remaining>0 then
  if a.x==-535 or a.x==535 then b.x=clamp(b.x+direction*remaining,-535,535)
  elseif b.x==-535 or b.x==535 then a.x=clamp(a.x-direction*remaining,-535,535)end
 end
end

local roundWinner=0
local function resetRound()
 for i=1,2 do f[i]={x=i==1 and -185 or 185,y=0,vy=0,hp=100,role=roleChoice[i],meter=0,face=i==1 and 1 or -1,stun=0,down=0,wake=0,launched=false,airHits=0,attack=nil,block=false,crouch=false,chainCount=0,comboHits=0,comboDamage=0,comboOwner=0,comboDisplay=0,flash=0,walk=0}end
 remaining=60;phase='intro';roundIntro=90;freeze=0;intermission=0;input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false}
 directions={};lastDirection=5;motionMove=nil;heldButtons={}
 controls={}
 for i=1,2 do controls[i]={input={left=false,right=false,down=false,block=false,light=0,heavy=0,special=0,jump=false},directions={},lastDirection=5,heldButtons={}}end
 input=controls[1].input
end
local function withControl(i,callback)
 local savedInput,savedDirections,savedLast,savedMotion,savedHeld,savedPlayer=input,directions,lastDirection,motionMove,heldButtons,controlPlayer
 local c=controls[i];input=c.input;directions=c.directions;lastDirection=c.lastDirection;motionMove=c.motionMove;heldButtons=c.heldButtons;controlPlayer=i
 callback()
 c.directions=directions;c.lastDirection=lastDirection;c.motionMove=motionMove;c.heldButtons=heldButtons
 input=savedInput;directions=savedDirections;lastDirection=savedLast;motionMove=savedMotion;heldButtons=savedHeld;controlPlayer=savedPlayer
end
local function restart()Collision.results={};round=1;wins={0,0};tick=0;resetRound()end
local function finish(winner)
 roundWinner=winner;Collision.results[round]=winner
 if winner>0 then wins[winner]=wins[winner]+1 end
 if wins[1]>=2 or wins[2]>=2 then phase=winner==1 and 'KEQING WINS MATCH' or 'DILUC WINS MATCH' else phase=winner==0 and 'DRAW ROUND' or (winner==1 and 'KEQING WINS ROUND' or 'DILUC WINS ROUND') end
 intermission=150;print('ROUND_END '..phase)
end
local function hit(i,j)
 local a,b=f[i],f[j];local atk=a.attack;local s=specs[f[i].role][atk.kind]
 if (a.role==1 or a.role==10)and atk.kind=='special'then return end
 if atk.hit or b.hp<=0 or b.down>0 or b.wake>0 then return end
 if b.launched and b.airHits>=5 then return end
 if s.height=='low' and b.y>20 then return end
 local distance=(b.x-a.x)*a.face
 local range=s.range
 if a.role==5 or a.role==6 or a.role==7 or a.role==8 then if atk.kind=='special'then range=math.min(range,90+(atk.t-atk.startup)*45)end end
 if a.role==2 and atk.kind=='super' then range=90+math.max(0,atk.t-atk.startup)*14 end
 if not Collision.overlap(Collision.attack(a,s,range),Collision.hurt(b))then return end
 atk.hit=true
 local blocked=b.block and b.y==0 and b.face==-a.face and (b.stun<=0 or b.guardStun) and not b.attack
 if s.height=='low' and not b.crouch then blocked=false end
 if (s.height=='high' or a.y>20) and b.crouch then blocked=false end
 local base=s.damage
 local cls=roleClass[a.role]
 if(a.stanceLife or 0)>0 then base=base+3 end
 if cls=='shotgun'and atk.kind=='special'then base=base+(a.charges or 0)*2;a.charges=0 end
 if cls=='trap'and atk.kind=='super'then base=base+(a.totems or 0)*4;a.totems=0 end
 if cls=='debt'and atk.kind=='heavy'and(b.debt or 0)>0 then base=base+7;b.debt=0 end
 if cls=='mark'and atk.kind=='heavy'and(b.marked or 0)>0 then base=base+5;b.marked=0 end
 if a.role==8 and(atk.kind=='heavy'or atk.kind=='super')then base=base+(a.seals or 0)*3;a.seals=0 end
 if a.role==10 and(a.buffLife or 0)>0 then base=base+4 end
 if a.role==6 and atk.kind=='special'then base=base+(b.conductive or 0)*3;b.conductive=0 end
 local damage=blocked and math.max(1,math.floor(base*.15))or base
 if a.role==8 and not blocked and(atk.kind=='light'or atk.kind=='special')then a.seals=atk.kind=='special'and 3 or math.min(3,(a.seals or 0)+1)end
 if a.role==6 and not blocked and atk.kind=='light'then b.conductive=math.min(3,(b.conductive or 0)+1)end
 if(b.role==11 or roleClass[b.role]=='shield'or roleClass[b.role]=='shielddash'or roleClass[b.role]=='shieldrange')and(b.armorLife or 0)>0 then damage=math.max(1,math.floor(damage*.6));b.armorLife=0 end
 if a.role==10 and not blocked and atk.kind=='super'then a.hp=math.min(100,a.hp+12)end
 if a.role==3 and not blocked and atk.kind=='special'then b.chill=90 end
 if cls=='shotgun'and not blocked and atk.kind=='light'then a.charges=math.min(3,(a.charges or 0)+1)end
 if cls=='mark'and not blocked and atk.kind=='special'then b.marked=180 end
 if cls=='debt'and not blocked and atk.kind=='special'then b.debt=180 end
 if cls=='vortex'and not blocked and atk.kind=='super'then b.x=clamp(a.x+a.face*90,-535,535)end
 if cls=='heal'and atk.kind=='super'then a.hp=math.min(100,a.hp+12)end
 if cls=='debt'and atk.kind=='super'then a.hp=math.min(100,a.hp+10)end
 local airFollow=b.launched and not blocked
 if airFollow then damage=math.max(1,math.floor(damage*math.max(.4,1-.15*(b.airHits+1))))end
 if not blocked then
  atk.connected=true
  if b.stun>0 and b.comboOwner==i then a.comboHits=a.comboHits+1;a.comboDamage=a.comboDamage+damage else a.comboHits=1;a.comboDamage=damage end
  b.comboOwner=i;a.comboDisplay=90
 end
 a.meter=math.min(100,a.meter+(blocked and 4 or damage*.9));b.meter=math.min(100,b.meter+damage*1.2);
 b.hp=math.max(0,b.hp-damage);b.stun=blocked and 8 or s.stun;b.guardStun=blocked;b.flash=blocked and 0 or 7;b.attack=nil;b.x=clamp(b.x+a.face*(blocked and 10 or (airFollow and s.push*.45 or s.push)),-535,535)
 if airFollow then
  b.airHits=b.airHits+1;b.stun=75;b.block=false;b.crouch=false
  if b.airHits>=5 or atk.kind=='heavy' or atk.kind=='overhead' or atk.kind=='super' or atk.kind=='special' then b.vy=math.min(b.vy,-300)
  elseif atk.kind=='rising' then b.vy=math.max(220,360-b.airHits*45)
  else b.vy=math.max(b.vy,240-b.airHits*25)end
  print('JUGGLE '..j..' count='..b.airHits)
 elseif not blocked and(atk.kind=='rising'or((a.role==4 or roleClass[a.role]=='launch'or roleClass[a.role]=='launchrange')and atk.kind=='special')or((roleClass[a.role]=='bruiser'or roleClass[a.role]=='selfbuff')and atk.kind=='super'))then
  b.launched=true;b.airHits=0;b.stun=75;b.block=false;b.crouch=false;b.y=math.max(b.y,8);b.vy=520;print('LAUNCH '..j)
 elseif not blocked and (atk.kind=='heavy' or atk.kind=='overhead' or atk.kind=='super' or atk.kind=='teleport' or atk.kind=='e3') then
  b.down=45;b.stun=0;b.block=false;b.crouch=false;b.y=0;b.vy=0;print('KNOCKDOWN '..j)
 elseif not blocked and (atk.kind=='light' or atk.kind=='low') then b.stun=math.max(b.stun,24)end
 freeze=blocked and 2 or 4;print((blocked and 'BLOCK' or 'HIT')..' '..i..'>'..j..' damage='..damage..' move='..atk.kind)
end
local function advance(i)
 local a=f[i]
 a.stanceLife=math.max(0,(a.stanceLife or 0)-1);a.marked=math.max(0,(a.marked or 0)-1);a.debt=math.max(0,(a.debt or 0)-1)
 a.chill=math.max(0,(a.chill or 0)-1);a.buffLife=math.max(0,(a.buffLife or 0)-1);a.armorLife=math.max(0,(a.armorLife or 0)-1)
 if a.role==9 then a.eRecharge=math.max(0,(a.eRecharge or 0)-1);if a.eRecharge==0 and(a.eCharges or 2)<2 then a.eCharges=(a.eCharges or 2)+1;a.eRecharge=240 end end
 a.markLife=math.max(0,(a.markLife or 0)-1);a.eWindow=math.max(0,(a.eWindow or 0)-1)
 if a.stun>0 then a.eWindow=0 end
 if a.stun>0 then a.stun=a.stun-1 end;if a.stun<=0 then a.guardStun=false end
 if a.flash>0 then a.flash=a.flash-1 end
 if a.comboDisplay>0 then a.comboDisplay=a.comboDisplay-1 end
 if a.down>0 then a.down=a.down-1;if a.down==0 then a.wake=18;print('GETUP '..i)end;return end
 if a.wake>0 then a.wake=a.wake-1;return end
 if a.y>0 or a.vy>0 then
  a.y=a.y+a.vy/60;a.vy=a.vy-1100/60
  if a.launched and a.y>240 then a.y=240;a.vy=math.min(a.vy,0)end
  if a.y<=0 then
   a.y=0;a.vy=0
   if a.launched then a.launched=false;a.airHits=0;a.down=45;a.stun=0;a.attack=nil;print('AIR_LAND_KNOCKDOWN '..i)end
  end
 end
 if a.attack then
  local atk=a.attack;local s=specs[f[i].role][atk.kind];atk.t=atk.t+1
  if a.role==1 and atk.kind=='special' and atk.t==atk.startup then
   local distance=(f[3-i].x-a.x)*a.face;a.markX=clamp(a.x+a.face*clamp(distance-50,80,230),-535,535);a.markLife=180
  elseif atk.kind=='teleport' and atk.t==atk.startup then a.x=a.markX or a.x;a.markLife=0 end
  if a.role==2 and(atk.kind=='special' or atk.kind=='e2' or atk.kind=='e3')then a.eWindow=45 end
  if atk.t==atk.startup then
   local cls=roleClass[a.role]
   if atk.kind=='special'then
    if cls=='shield'or cls=='shielddash'or cls=='shieldrange'then a.armorLife=180 end
    if cls=='stance'or cls=='bruiser'or cls=='air'then a.stanceLife=300 end
    if cls=='selfbuff'then a.hp=math.max(1,a.hp-6);a.stanceLife=300 end
    if cls=='heal'then a.hp=math.min(100,a.hp+6)end
    if cls=='trap'then a.totems=math.min(3,(a.totems or 0)+1)end
    if cls=='air'then a.vy=260 end
   end
   if a.role==10 and atk.kind=='special'then a.hp=math.max(1,a.hp-10);a.buffLife=360 end
   if a.role==4 and atk.kind=='super'then a.hp=math.min(100,a.hp+8)end
   if a.role==9 and atk.kind=='super'then a.buffLife=360 end
   if a.role==11 and atk.kind=='special'then a.armorLife=180 end
  end
  if atk.t>=atk.startup and atk.t<atk.startup+s.active then hit(i,3-i)end
  if atk.t>=atk.startup+s.active+s.recovery then a.attack=nil;a.chainCount=0 end
 end
end
local function step()
 if phase=='roundLoad'then return end
 tick=tick+1
 if phase=='intro' then roundIntro=roundIntro-1;if roundIntro<=0 then phase='fight' end;return end
 if phase~='fight' then
  if wins[1]<2 and wins[2]<2 then intermission=intermission-1;if intermission<=0 then phase='roundLoad'end end;return
 end
 if freeze>0 then freeze=freeze-1;return end
 for i=1,2 do f[i].meter=math.min(100,f[i].meter+.045)end
 remaining=math.max(0,remaining-1/60)
 for i=1,2 do if ready(i) then f[i].face=f[3-i].x>=f[i].x and 1 or -1 end end
 local a,b=f[1],f[2]
 for i=1,2 do withControl(i,function()
  local p=f[i]
  input.light=math.max(0,input.light-1);input.heavy=math.max(0,input.heavy-1);input.special=math.max(0,input.special-1)
  if p.attack then
   if input.special>0 and startAttack(i,motionMove)then input.special=0 elseif input.heavy>0 and startAttack(i,'heavy')then input.heavy=0 elseif input.light>0 and startAttack(i,'light')then input.light=0 end
  end
  if ready(i) then
   p.crouch=input.down and p.y==0;p.block=input.block and p.y==0
   if input.special>0 and startAttack(i,motionMove)then input.special=0 elseif input.heavy>0 and startAttack(i,'heavy')then input.heavy=0 elseif input.light>0 and startAttack(i,p.crouch and 'low' or 'light')then input.light=0 end
   if not p.attack and not p.block and not p.crouch then local move=(input.right and 1 or 0)-(input.left and 1 or 0);p.x=clamp(p.x+move*specs[f[i].role].speed*((p.chill or 0)>0 and .8 or 1)/60,-535,535);if move~=0 then p.walk=p.walk+.2 end end
   if input.jump and p.y==0 and not p.block and not p.attack then p.vy=p.role==9 and(p.buffLife or 0)>0 and 600 or 465 end
  end
  input.jump=false
 end)end
 if aiEnabled and canCancel(2,'heavy') then startAttack(2,'heavy')end
 if aiEnabled and ready(2) then
  local dist=math.abs(a.x-b.x);b.block=false;b.crouch=false
  if a.attack and dist<170 and tick%90<50 and b.y==0 then b.block=true;b.crouch=specs[a.role][a.attack.kind].height=='low'
  elseif b.meter>=100 and dist<330 and tick%90==0 then startAttack(2,'super')
  elseif dist<250 and tick%(b.role==1 and 80 or 100)==0 then startAttack(2,a.y>30 and 'rising' or 'special')
  elseif dist>(b.role==1 and 98 or 124) then b.x=clamp(b.x+b.face*specs[b.role].speed/60,-535,535);b.walk=b.walk+.16
  elseif tick%35==0 then startAttack(2,tick%105==0 and 'low' or (tick%70==0 and 'heavy' or 'light'))end
 end
 for i=1,2 do local c=f[i];if c.attack and c.attack.kind=='special' then local s=specs[f[i].role].special;if s.dash and c.attack.t>=s.startup-4 and c.attack.t<s.startup+s.active then c.x=clamp(c.x+c.face*s.dash/60,-535,535)end end end
 
 local gap=b.x-a.x
 Collision.push(a,b)
 advance(1);advance(2)
 if a.hp<=0 or b.hp<=0 or remaining<=0 then finish(a.hp==b.hp and 0 or (a.hp>b.hp and 1 or 2))end
end

-- Incremental base64 + LZ token decoder. Stored art remains compressed until requested.
local b64values={}
do local chars='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
 for n=1,#chars do b64values[string.byte(chars,n)]=n-1 end
end
local function unpackCost(frame)return math.ceil(#frame.data/256)+math.ceil(frame.tokens/128)+math.ceil(frame.count/128)end
local function framePixel(frame,n)
 local at=(n-1)*5+1;local x,y,w,h,index=string.byte(frame.raw,at,at+4)
 return x,y,w,h,frame.palette[index]
end
local function unpackWork(frame)
 local d=frame.decoder
 if not d then d={phase=1,at=1,z={},out={},pos=1,row=1,parts={},rawPos=1,x=0,y=0};frame.decoder=d end
 if d.phase==1 then
  local last=math.min(#frame.data,d.at+255)
  for at=d.at,last,4 do
   local a=b64values[string.byte(frame.data,at)]or 0;local b=b64values[string.byte(frame.data,at+1)]or 0
   local c=b64values[string.byte(frame.data,at+2)]or 0;local e=b64values[string.byte(frame.data,at+3)]or 0
   d.z[#d.z+1]=a*4+math.floor(b/16)
   if string.byte(frame.data,at+2)~=61 then d.z[#d.z+1]=(b%16)*16+math.floor(c/4)end
   if string.byte(frame.data,at+3)~=61 then d.z[#d.z+1]=(c%4)*64+e end
  end
  d.at=last+1;if d.at>#frame.data then d.phase=2 end
 elseif d.phase==2 then
  for n=1,128 do
   if d.pos>#d.z then break end
   local token=d.z[d.pos];d.pos=d.pos+1
   if token<128 then for k=1,token+1 do d.out[#d.out+1]=d.z[d.pos];d.pos=d.pos+1 end
   else local length=token-128+3;local distance=d.z[d.pos]*256+d.z[d.pos+1];d.pos=d.pos+2
    for k=1,length do d.out[#d.out+1]=d.out[#d.out-distance+1]end
   end
  end
  if d.pos>#d.z then d.z=nil;d.phase=3 end
 else
  local chunk={}
  for n=1,128 do
   if d.row>frame.count then break end
   local at=d.rawPos;local header=d.out[at];local flag=math.floor(header/64);local index=header%64+1;local w,h
   if flag==0 then
    local coordinate=d.out[at+1];local dx=math.floor(coordinate/16);local dy=coordinate%16
    d.x=d.x+(dx%2==0 and dx/2 or-(dx+1)/2);d.y=d.y+(dy%2==0 and dy/2 or-(dy+1)/2)
    local size=d.out[at+2];w=math.floor(size/16)+1;h=size%16+1;d.rawPos=at+3
   elseif flag==1 then d.x=d.out[at+1];d.y=d.out[at+2];local size=d.out[at+3];w=math.floor(size/16)+1;h=size%16+1;d.rawPos=at+4
   else d.x=d.out[at+1];d.y=d.out[at+2];w=d.out[at+3];h=d.out[at+4];d.rawPos=at+5 end
   chunk[#chunk+1]=string.char(d.x,d.y,w,h,index);d.row=d.row+1
  end
  d.parts[#d.parts+1]=table.concat(chunk)
  if d.row>frame.count then frame.raw=table.concat(d.parts);frame.rows=true;frame.decoder=nil;return true end
 end
 return false
end

-- [line 446 data omitted, len=1967524] local spriteData={{{scale=2.3333333333333335,anchor={32.4041
local poseIds={{["idle"]=1,["windup"]=2,["slash"]=3,["rising"]=4,["walk1"]=5,["walk2"]=6,["crouch"]=7,["crouchGuard"]=8,["guard"]=9,["hurt"]=10,["airHurt"]=11,["down"]=12,["low"]=13,["jump"]=14,["teleport"]=15,["qRelease"]=16,["getup"]=17,["eThrow"]=18},{["idle"]=1,["windup"]=2,["slash"]=3,["rising"]=4,["walk1"]=5,["walk2"]=6,["crouch"]=7,["crouchGuard"]=8,["guard"]=9,["hurt"]=10,["airHurt"]=11,["down"]=12,["low"]=13,["jump"]=14,["getup"]=15,["e1"]=16,["e2"]=17,["e3Windup"]=18,["idle2"]=19,["qCharge"]=20,["qRelease"]=21,["e3"]=22},{["basic0"]=1,["basic1"]=2,["basic2"]=3,["basic3"]=4,["basic4"]=5,["basic5"]=6,["basic6"]=7,["basic7"]=8,["basic8"]=9,["basic9"]=10,["basic10"]=11,["basic11"]=12,["basic12"]=13,["basic13"]=14,["basic14"]=15,["basic15"]=16,["attack0"]=17,["attack1"]=18,["attack2"]=19,["attack3"]=20,["attack4"]=21,["attack5"]=22,["attack6"]=23,["attack7"]=24,["attack8"]=25,["attack9"]=26,["attack10"]=27,["attack11"]=28,["attack12"]=29,["attack13"]=30,["attack14"]=31,["attack15"]=32,["connections0"]=33,["connections1"]=34,["connections2"]=35,["connections3"]=36,["connections4"]=37,["connections5"]=38,["connections6"]=39,["connections7"]=40,["connections8"]=41,["connections9"]=42,["connections10"]=43,["connections11"]=44,["connections12"]=45,["connections13"]=46,["connections14"]=47,["connections15"]=48},{["basic0"]=1,["basic1"]=2,["basic2"]=3,["basic3"]=4,["basic4"]=5,["basic5"]=6,["basic6"]=7,["basic7"]=8,["basic8"]=9,["basic9"]=10,["basic10"]=11,["basic11"]=12,["basic12"]=13,["basic13"]=14,["basic14"]=15,["basic15"]=16,["attack0"]=17,["attack1"]=18,["attack2"]=19,["attack3"]=20,["attack4"]=21,["attack5"]=22,["attack6"]=23,["attack7"]=24,["attack8"]=25,["attack9"]=26,["attack10"]=27,["attack11"]=28,["attack12"]=29,["attack13"]=30,["attack14"]=31,["attack15"]=32,["connections0"]=33,["connections1"]=34,["connections2"]=35,["connections3"]=36,["connections4"]=37,["connections5"]=38,["connections6"]=39,["connections7"]=40,["connections8"]=41,["connections9"]=42,["connections10"]=43,["connections11"]=44,["connections12"]=45,["connections13"]=46,["connections14"]=47,["connections15"]=48},{["basic0"]=1,["basic1"]=2,["basic2"]=3,["basic3"]=4,["basic4"]=5,["basic5"]=6,["basic6"]=7,["basic7"]=8,["basic8"]=9,["basic9"]=10,["basic10"]=11,["basic11"]=12,["basic12"]=13,["basic13"]=14,["basic14"]=15,["basic15"]=16,["attack0"]=17,["attack1"]=18,["attack2"]=19,["attack3"]=20,["attack4"]=21,["attack5"]=22,["attack6"]=23,["attack7"]=24,["attack8"]=25,["attack9"]=26,["attack10"]=27,["attack11"]=28,["attack12"]=29,["attack13"]=30,["attack14"]=31,["attack15"]=32,["connections0"]=33,["connections1"]=34,["connections2"]=35,["connections3"]=36,["connections4"]=37,["connections5"]=38,["connections6"]=39,["connections7"]=40,["connections8"]=41,["connections9"]=42,["connections10"]=43,["connections11"]=44,["connections12"]=45,["connections13"]=46,["connections14"]=47,["connections15"]=48},{["basic0"]=1,["basic1"]=2,["basic2"]=3,["basic3"]=4,["basic4"]=5,["basic5"]=6,["basic6"]=7,["basic7"]=8,["basic8"]=9,["basic9"]=10,["basic10"]=11,["basic11"]=12,["basic12"]=13,["basic13"]=14,["basic14"]=15,["basic15"]=16,["attack0"]=17,["attack1"]=18,["attack2"]=19,["attack3"]=20,["attack4"]=21,["attack5"]=22,["attack6"]=23,["attack7"]=24,["attack8"]=25,["attack9"]=26,["attack10"]=27,["attack11"]=28,["attack12"]=29,["attack13"]=30,["attack14"]=31,["attack15"]=32,["connections0"]=33,["connections1"]=34,["connections2"]=35,["connections3"]=36,["connections4"]=37,["connections5"]=38,["connections6"]=39,["connections7"]=40,["connections8"]=41,["connections9"]=42,["connections10"]=43,["connections11"]=44,["connections12"]=45,["connections13"]=46,["connections14"]=47,["connections15"]=48},{["basic0"]=1,["basic1"]=2,["basic2"]=3,["basic3"]=4,["basic4"]=5,["basic5"]=6,["basic6"]=7,["basic7"]=8,["basic8"]=9,["basic9"]=10,["basic10"]=11,["basic11"]=12,["basic12"]=13,["basic13"]=14,["basic14"]=15,["basic15"]=16,["attack0"]=17,["attack1"]=18,["attack2"]=19,["attack3"]=20,["attack4"]=21,["attack5"]=22,["attack6"]=23,["attack7"]=24,["attack8"]=25,["attack9"]=26,["attack10"]=27,["attack11"]=28,["attack12"]=29,["attack13"]=30,["attack14"]=31,["attack15"]=32,["connections0"]=33,["connections1"]=34,["connections2"]=35,["connections3"]=36,["connections4"]=37,["connections5"]=38,["connections6"]=39,["connections7"]=40,["connections8"]=41,["connections9"]=42,["connections10"]=43,["connections11"]=44,["connections12"]=45,["connections13"]=46,["connections14"]=47,["connections15"]=48},{["basic0"]=1,["basic1"]=2,["basic2"]=3,["basic3"]=4,["basic4"]=5,["basic5"]=6,["basic6"]=7,["basic7"]=8,["basic8"]=9,["basic9"]=10,["basic10"]=11,["basic11"]=12,["basic12"]=13,["basic13"]=14,["basic14"]=15,["basic15"]=16,["attack0"]=17,["attack1"]=18,["attack2"]=19,["attack3"]=20,["attack4"]=21,["attack5"]=22,["attack6"]=23,["attack7"]=24,["attack8"]=25,["attack9"]=26,["attack10"]=27,["attack11"]=28,["attack12"]=29,["attack13"]=30,["attack14"]=31,["attack15"]=32,["connections0"]=33,["connections1"]=34,["connections2"]=35,["connections3"]=36,["connections4"]=37,["connections5"]=38,["connections6"]=39,["connections7"]=40,["connections8"]=41,["connections9"]=42,["connections10"]=43,["connections11"]=44,["connections12"]=45,["connections13"]=46,["connections14"]=47,["connections15"]=48},{["basic0"]=1,["basic1"]=2,["basic2"]=3,["basic3"]=4,["basic4"]=5,["basic5"]=6,["basic6"]=7,["basic7"]=8,["basic8"]=9,["basic9"]=10,["basic10"]=11,["basic11"]=12,["basic12"]=13,["basic13"]=14,["basic14"]=15,["basic15"]=16,["attack0"]=17,["attack1"]=18,["attack2"]=19,["attack3"]=20,["attack4"]=21,["attack5"]=22,["attack6"]=23,["attack7"]=24,["attack8"]=25,["attack9"]=26,["attack10"]=27,["attack11"]=28,["attack12"]=29,["attack13"]=30,["attack14"]=31,["attack15"]=32,["connections0"]=33,["connections1"]=34,["connections2"]=35,["connections3"]=36,["connections4"]=37,["connections5"]=38,["connections6"]=39,["connections7"]=40,["connections8"]=41,["connections9"]=42,["connections10"]=43,["connections11"]=44,["connections12"]=45,["connections13"]=46,["connections14"]=47,["connections15"]=48}}
local phoenixData={{scale=4,anchor={44.8,26},rows={{8,24,1,1,4294796811},{8,25,1,1,4294741011},{9,24,2,1,4293279240},{9,25,1,2,4294796811},{9,29,1,2,4293279240},{10,25,1,2,4293279240},{10,30,1,1,4293279240},{11,26,1,2,4293279240},{11,30,1,1,4294796811},{11,31,1,1,4293279240},{12,27,4,1,4293279240},{12,28,2,1,4294796811},{12,30,1,2,4294741011},{13,31,2,1,4294757469},{13,32,1,1,4293279240},{14,22,1,1,4294741011},{14,28,2,1,4294741011},{14,32,1,1,4294741011},{15,22,1,1,4294757469},{15,23,1,1,4294748204},{15,29,1,1,4294796811},{15,32,1,1,4294748204},{16,27,1,1,4294796811},{16,28,1,1,4294748204},{16,29,1,1,4294741011},{17,27,4,1,4294741011},{17,28,1,1,4294757469},{18,26,1,1,4293279240},{18,28,2,1,4294763922},{19,29,1,1,4294796811},{20,28,1,1,4294757469},{21,26,2,1,4293279240},{21,27,1,2,4294748204},{22,27,3,1,4294748204},{22,28,1,1,4294741011},{23,24,1,2,4293279240},{23,26,1,1,4294796811},{23,28,3,1,4294796811},{23,30,1,1,4293279240},{24,10,1,2,4294796811},{24,24,1,1,4293279240},{24,25,1,1,4294796811},{24,26,2,1,4294748204},{24,29,2,1,4293279240},{25,24,2,1,4294796811},{25,25,3,1,4294748204},{25,27,2,1,4294757469},{26,7,1,1,4294796811},{26,26,1,1,4294757469},{26,28,4,1,4293279240},{27,7,1,1,4294741011},{27,8,2,1,4294796811},{27,11,1,1,4294757469},{27,26,4,1,4294763922},{27,27,2,1,4294741011},{27,30,1,1,4293279240},{28,25,1,1,4294757469},{28,29,1,1,4293279240},{29,22,1,1,4293279240},{29,27,1,1,4294796811},{29,29,3,1,4294796811},{29,35,1,1,4294741011},{29,36,1,1,4294796811},{30,27,1,1,4294741011},{30,28,1,1,4294796811},{30,35,1,1,4294757469},{30,36,2,1,4294741011},{31,8,1,1,4294741011},{31,26,1,1,4294748204},{31,27,1,1,4294757469},{31,28,1,1,4294748204},{31,30,2,1,4293279240},{31,35,1,1,4294763922},{32,8,1,1,4294796811},{32,26,1,1,4294796811},{32,27,1,1,4294748204},{32,28,1,1,4294763922},{32,29,1,1,4294748204},{32,35,1,1,4294741011},{33,9,1,1,4294757469},{33,10,1,1,4294796811},{33,11,1,1,4293279240},{33,12,1,1,4294796811},{33,27,1,1,4294796811},{33,28,1,1,4294741011},{33,29,1,1,4294757469},{34,10,1,1,4294763922},{34,11,1,2,4294748204},{34,13,1,1,4294757469},{34,27,3,2,4293279240},{34,29,1,1,4294741011},{35,11,1,1,4293279240},{35,12,1,1,4294741011},{35,13,1,1,4294763922},{35,14,1,1,4294748204},{35,17,1,1,4294796811},{35,25,1,1,4294757469},{35,26,1,1,4294741011},{35,29,1,1,4293279240},{35,32,1,2,4293279240},{36,12,1,1,4293279240},{36,13,1,1,4294733623},{36,14,1,1,4294757469},{36,15,6,1,4293279240},{36,17,1,2,4294748204},{36,29,1,1,4294796811},{36,30,1,3,4293279240},{36,33,1,1,4294733623},{36,34,1,1,4294741011},{37,2,1,2,4293279240},{37,7,4,2,4293279240},{37,13,4,1,4293279240},{37,14,1,1,4294741011},{37,16,5,1,4293279240},{37,17,1,1,4294733623},{37,18,1,1,4294763922},{37,28,2,1,4293279240},{37,29,5,1,4294741011},{37,30,1,1,4293279240},{37,31,2,1,4294741011},{37,32,1,1,4293279240},{37,33,1,1,4294757469},{37,34,1,1,4294748204},{38,3,2,2,4293279240},{38,9,4,1,4293279240},{38,14,3,1,4293279240},{38,17,2,1,4293279240},{38,18,1,1,4294733623},{38,19,1,1,4294748204},{38,30,1,1,4294741011},{38,32,1,1,4294752880},{38,33,1,1,4294763922},{39,5,4,1,4293279240},{39,10,2,3,4293279240},{39,19,1,1,4294733623},{39,20,1,1,4293279240},{39,23,1,1,4294741011},{39,30,2,1,4294757469},{39,31,1,2,4294748204},{40,4,2,1,4293279240},{40,6,1,1,4294796811},{40,17,2,1,4294796811},{40,18,1,2,4293279240},{40,20,4,1,4294796811},{41,6,1,1,4293279240},{41,7,1,1,4294741011},{41,8,1,1,4294796811},{41,10,1,1,4293279240},{41,11,2,1,4294796811},{41,12,1,1,4293279240},{41,13,1,2,4294796811},{41,18,1,2,4294796811},{41,22,4,1,4293279240},{41,28,5,1,4293279240},{41,30,1,1,4294796811},{42,6,1,2,4294796811},{42,8,2,2,4294748204},{42,10,1,1,4294796811},{42,12,1,1,4294741011},{42,13,1,1,4294796811},{42,14,1,2,4294741011},{42,16,1,1,4294796811},{42,17,1,3,4294741011},{42,21,1,1,4293279240},{42,29,2,1,4294796811},{43,2,1,1,4293279240},{43,6,1,2,4294741011},{43,10,1,3,4294748204},{43,13,1,1,4294757469},{43,14,1,1,4294741011},{43,15,2,1,4294748204},{43,16,1,2,4294741011},{43,18,2,2,4294748204},{43,21,1,1,4294796811},{43,31,1,1,4293279240},{44,3,1,1,4294796811},{44,7,2,1,4294741011},{44,8,1,2,4294757469},{44,10,1,1,4294748204},{44,11,2,1,4294763922},{44,12,1,1,4294757469},{44,13,1,1,4294763922},{44,14,1,1,4294757469},{44,16,1,1,4294757469},{44,17,1,1,4294748204},{44,20,1,2,4294741011},{44,23,1,1,4293279240},{44,29,1,1,4293279240},{44,30,1,1,4294796811},{45,5,1,2,4294748204},{45,8,1,1,4294748204},{45,9,1,2,4294763922},{45,12,1,2,4294762148},{45,14,1,1,4294763452},{45,15,1,1,4294752880},{45,16,1,3,4294763922},{45,19,1,3,4294748204},{45,22,1,2,4294796811},{45,29,1,2,4294741011},{46,7,1,3,4294763922},{46,10,1,1,4294762148},{46,11,1,2,4294763452},{46,13,1,1,4294739790},{46,14,1,1,4294733623},{46,15,1,1,4294755992},{46,16,1,1,4294733623},{46,17,1,2,4294763452},{46,19,1,1,4294763922},{46,20,1,2,4294757469},{46,22,2,1,4294748204},{46,23,1,1,4294796811},{46,24,1,2,4293279240},{46,28,3,1,4294796811},{46,29,1,1,4294757469},{47,10,1,1,4294796811},{47,11,2,1,4293279240},{47,12,1,1,4294739790},{47,13,1,1,4294763452},{47,14,1,3,4294796811},{47,17,1,1,4294739790},{47,18,1,1,4294752880},{47,19,1,1,4294763452},{47,20,1,1,4294762148},{47,21,1,1,4294757469},{47,23,1,2,4294741011},{47,29,1,1,4294741011},{48,12,2,2,4293279240},{48,14,1,1,4294733623},{48,15,1,1,4294796811},{48,16,2,1,4294741011},{48,17,1,1,4294748204},{48,18,1,1,4294796811},{48,19,1,1,4294752880},{48,20,1,1,4294763452},{48,21,1,2,4294763922},{48,23,1,2,4294748204},{48,25,1,2,4293279240},{48,29,2,1,4294796811},{49,14,2,2,4293279240},{49,17,1,1,4294757469},{49,18,2,1,4294741011},{49,19,2,1,4294796811},{49,20,1,1,4294733623},{49,21,1,2,4294752880},{49,23,1,1,4294763922},{49,24,1,1,4294748204},{49,25,1,1,4294741011},{49,26,2,1,4294796811},{49,27,3,2,4293279240},{49,31,1,1,4294796811},{50,16,2,1,4293279240},{50,17,1,1,4294796811},{50,20,1,3,4294796811},{50,23,1,1,4294755992},{50,24,1,2,4294757469},{50,29,5,1,4293279240},{51,15,1,1,4293279240},{51,17,2,5,4293279240},{51,22,1,2,4294796811},{51,24,1,1,4294755992},{51,25,1,1,4294757469},{51,26,1,1,4294748204},{52,16,1,1,4294733623},{52,22,2,2,4293279240},{52,24,1,1,4294796811},{52,25,1,1,4294763452},{52,26,1,1,4294757469},{52,27,2,1,4294796811},{52,28,2,1,4293279240},{53,9,1,1,4293279240},{53,16,2,1,4293279240},{53,17,1,2,4294733623},{53,19,1,2,4294741011},{53,21,1,1,4294733623},{53,24,2,1,4293279240},{53,25,1,1,4294739790},{53,26,1,1,4294763922},{54,10,2,1,4293279240},{54,13,1,3,4293279240},{54,17,1,1,4294796811},{54,18,1,1,4294748204},{54,19,1,1,4294757469},{54,20,1,2,4294763922},{54,22,1,1,4294762148},{54,23,2,1,4294739790},{54,25,1,1,4294796811},{54,26,1,1,4294752880},{54,27,1,2,4294741011},{55,11,1,4,4293279240},{55,15,1,1,4294796811},{55,16,1,1,4294748204},{55,17,1,1,4294757469},{55,18,1,1,4294763922},{55,19,1,1,4294739790},{55,20,1,1,4293279240},{55,22,1,1,4294796811},{55,24,1,1,4294762148},{55,25,1,1,4294733623},{55,26,1,1,4294748204},{55,27,1,2,4294757469},{55,29,1,1,4294733623},{56,11,1,2,4293279240},{56,13,1,1,4294796811},{56,14,1,1,4294741011},{56,15,1,1,4294748204},{56,16,1,1,4294757469},{56,17,1,1,4294752880},{56,18,1,1,4293279240},{56,24,1,1,4294733623},{56,25,1,1,4294763922},{56,26,1,1,4294752880},{56,27,2,1,4294763452},{56,28,1,1,4294763922},{57,13,1,1,4294741011},{57,14,1,1,4294748204},{57,15,1,1,4294763922},{57,16,1,1,4294752880},{57,17,1,1,4294796811},{57,25,2,1,4294741011},{57,26,1,1,4294763922},{57,28,1,1,4294762148},{58,13,1,1,4293279240},{58,14,1,1,4294741011},{58,15,1,1,4294748204},{58,26,1,1,4294762148},{58,27,1,1,4294752880},{59,24,1,1,4293279240},{59,25,2,1,4294748204},{59,26,1,1,4294757469},{60,23,1,1,4293279240},{60,24,2,1,4294796811},{60,26,1,1,4294796811},{61,22,1,1,4294741011},{61,23,1,1,4294796811},{61,25,1,1,4293279240},{62,23,1,2,4294741011},{62,25,1,1,4294733623},{63,23,1,2,4294752880}}},{scale=4,anchor={44.8,26},rows={{0,24,1,1,4294736191},{7,29,4,1,4293275397},{7,30,2,1,4294077212},{9,30,3,1,4293275397},{11,29,3,1,4294077212},{12,26,1,2,4293275397},{12,28,1,1,4294077212},{13,25,2,2,4293275397},{13,27,1,1,4294077212},{13,28,1,1,4294812711},{13,34,1,1,4294077212},{14,27,1,1,4294812711},{14,28,1,1,4294821707},{15,25,1,1,4293275397},{15,26,1,1,4294077212},{15,27,2,1,4294826615},{15,28,1,1,4294077212},{16,25,1,1,4294077212},{16,26,1,1,4294812711},{16,28,4,1,4293275397},{17,12,1,1,4294077212},{17,26,1,2,4294821707},{18,9,1,1,4293275397},{18,12,1,1,4293275397},{18,22,1,1,4294077212},{18,26,2,1,4294826615},{18,27,3,1,4294812711},{19,10,1,1,4294077212},{19,11,1,1,4294812711},{19,12,1,1,4294077212},{19,13,1,1,4293275397},{19,22,1,1,4294812711},{19,23,1,1,4294821707},{20,12,1,1,4294812711},{20,13,1,1,4294077212},{20,19,1,1,4293275397},{20,23,1,1,4294826615},{20,26,1,1,4294821707},{20,28,2,1,4294610735},{20,31,1,1,4293275397},{21,13,2,1,4294812711},{21,14,2,1,4294077212},{21,23,1,1,4294821707},{21,26,2,1,4294826615},{21,27,2,1,4294077212},{22,16,3,1,4293275397},{22,28,1,1,4294077212},{22,29,1,1,4293275397},{23,14,2,1,4294812711},{23,15,1,1,4293275397},{23,25,1,1,4294077212},{23,26,1,2,4294821707},{23,28,1,1,4294812711},{23,29,1,1,4294077212},{23,30,2,2,4293275397},{24,15,1,1,4294077212},{24,17,2,2,4293275397},{24,26,1,1,4294812711},{24,27,1,1,4294831545},{24,28,1,1,4294821707},{24,29,2,1,4294812711},{24,32,1,2,4293275397},{25,12,1,2,4293275397},{25,14,2,1,4294077212},{25,15,3,1,4294812711},{25,16,1,1,4294077212},{25,26,1,1,4294077212},{25,27,1,1,4294821707},{25,28,1,1,4294831545},{25,30,1,1,4294077212},{25,31,2,1,4294812711},{25,32,2,1,4293275397},{26,13,1,1,4294610735},{26,16,1,1,4294812711},{26,17,1,1,4294077212},{26,18,1,1,4293275397},{26,27,2,1,4294077212},{26,28,1,1,4294826615},{26,29,1,1,4294821707},{26,30,1,1,4294812711},{27,14,1,1,4294812711},{27,16,2,1,4294821707},{27,17,2,1,4294812711},{27,18,1,1,4294077212},{27,19,1,1,4293275397},{27,21,2,1,4293275397},{27,28,2,1,4294821707},{27,29,1,2,4294826615},{27,31,1,1,4294077212},{28,15,1,1,4294821707},{28,18,1,1,4294610735},{28,19,1,1,4294077212},{28,20,2,1,4293275397},{28,29,1,1,4294831545},{28,30,4,1,4294826615},{28,31,1,1,4293275397},{29,15,1,1,4294610735},{29,16,2,1,4294826615},{29,17,1,2,4294821707},{29,19,2,1,4294812711},{29,21,1,1,4294077212},{29,27,1,1,4293275397},{29,28,1,1,4294812711},{29,29,1,1,4294826615},{29,31,1,1,4294077212},{30,17,1,1,4294826615},{30,18,1,1,4294821707},{30,20,1,1,4294077212},{30,21,1,1,4294610735},{30,28,2,1,4294077212},{30,29,1,1,4294812711},{30,31,1,1,4294812711},{30,33,3,1,4293275397},{31,16,2,1,4293275397},{31,17,1,1,4294831545},{31,18,1,1,4294826615},{31,19,1,1,4294821707},{31,20,1,1,4294610735},{31,21,2,1,4294812711},{31,29,1,1,4294610735},{32,17,1,2,4294750597},{32,19,1,1,4294826615},{32,20,1,1,4294812711},{32,22,1,2,4293275397},{32,28,2,1,4293275397},{32,29,1,1,4294821707},{32,32,1,1,4293275397},{33,17,1,2,4294736191},{33,19,1,1,4294759573},{33,20,1,2,4294821707},{33,22,1,2,4294077212},{33,29,1,1,4294812711},{33,32,1,1,4294077212},{34,15,2,1,4293275397},{34,17,4,1,4293275397},{34,18,1,1,4294077212},{34,19,1,1,4294750597},{34,20,1,1,4294826615},{34,21,1,1,4294821707},{34,22,1,2,4294610735},{34,29,1,1,4294610735},{34,31,2,1,4294812711},{35,16,3,1,4293275397},{35,18,4,1,4293275397},{35,19,1,1,4294736191},{35,20,1,1,4294746733},{35,21,1,1,4294826615},{35,22,1,1,4294821707},{35,23,3,1,4294812711},{35,29,1,2,4294077212},{36,19,5,1,4293275397},{36,20,2,1,4294077212},{36,21,1,1,4294759573},{36,22,1,1,4294826615},{36,24,1,1,4293275397},{36,28,7,1,4293275397},{36,29,4,1,4294077212},{36,30,1,2,4294826615},{37,21,1,1,4294750597},{37,22,1,1,4294759573},{37,24,1,1,4294610735},{37,30,1,1,4294746733},{37,31,1,2,4293275397},{38,17,1,1,4294077212},{38,20,6,1,4293275397},{38,21,1,1,4294736191},{38,22,1,1,4294746733},{38,23,1,1,4294821707},{38,24,2,1,4294812711},{38,30,1,2,4293275397},{39,18,1,1,4294812711},{39,21,1,2,4294077212},{39,23,1,1,4294826615},{39,31,1,1,4293275397},{40,17,1,1,4293275397},{40,18,1,1,4294610735},{40,21,5,1,4293275397},{40,22,2,1,4294077212},{40,23,1,1,4294750597},{40,24,3,1,4294821707},{40,25,1,1,4293275397},{40,29,1,2,4293275397},{41,18,1,1,4294821707},{41,19,1,1,4294736191},{41,23,2,1,4294610735},{41,25,1,1,4294077212},{41,29,1,1,4293275397},{41,30,1,1,4294077212},{42,19,1,1,4294077212},{42,22,5,1,4293275397},{42,25,3,1,4294812711},{42,29,1,1,4294821707},{43,23,2,1,4294077212},{43,24,1,1,4294826615},{43,28,2,1,4294077212},{43,29,1,1,4294826615},{44,24,1,1,4294746733},{44,26,2,1,4294077212},{44,27,7,1,4293275397},{44,29,2,1,4294077212},{45,21,1,1,4294077212},{45,23,4,1,4293275397},{45,24,1,1,4294610735},{45,25,1,1,4294821707},{45,28,6,1,4293275397},{45,31,1,1,4294077212},{46,24,1,1,4294746733},{46,25,2,1,4294826615},{46,26,1,1,4294610735},{46,29,1,2,4293275397},{47,22,1,1,4294077212},{47,24,1,1,4294077212},{47,26,1,1,4294812711},{47,29,5,1,4293275397},{48,22,1,1,4294821707},{48,24,2,1,4293275397},{48,25,1,1,4294750597},{48,26,1,1,4294821707},{49,23,1,1,4294826615},{49,25,1,1,4294736191},{49,26,1,1,4294826615},{50,23,1,1,4294746733},{50,24,1,1,4294759573},{50,25,1,1,4294077212},{50,26,1,1,4294750597},{51,23,1,1,4293275397},{51,24,1,2,4294750597},{51,26,1,1,4294746733},{51,27,1,2,4294812711},{52,24,2,1,4293275397},{52,25,1,1,4294831545},{52,26,1,1,4294812711},{52,27,1,2,4294826615},{52,29,1,1,4294610735},{53,25,1,1,4294610735},{53,26,1,1,4294826615},{53,27,1,2,4294767821},{54,25,1,1,4294077212},{54,26,1,1,4294821707},{54,27,1,1,4294767821},{54,28,1,1,4294831545},{55,25,1,1,4293275397},{55,26,2,1,4294826615},{55,27,1,1,4294831545},{56,23,2,1,4293275397},{56,25,1,1,4294077212},{56,27,1,1,4294077212},{57,24,2,1,4293275397},{57,25,1,1,4294812711},{57,26,1,1,4294610735},{58,23,1,1,4294077212},{58,25,2,1,4294077212},{59,23,1,2,4294610735},{60,24,1,1,4294610735},{60,25,1,1,4294759573},{61,24,1,2,4294746733},{62,25,1,1,4294746733}}}}
-- [line 449 data omitted, len=805748] local portraitData={{textArt=true,palette={"0000001F","00000
-- [line 450 data omitted, len=378920] local thumbData={{textArt=true,palette={"28262CF3","00000019
local portraitPool=908
local roleNames={"\229\136\187\230\153\180","\232\191\170\229\141\162\229\133\139","\229\135\175\228\186\154","\231\144\180","\229\143\175\232\142\137","\228\184\189\232\142\142","\231\148\152\233\155\168","\231\131\159\231\187\175","\233\173\136"}
local poolCaps={1369,2335,1923,1529,1164,1757,1774,1746,1472}
local resourceGate={busy=true,mode='menu',caps={0,0},request=nil,collision=Collision}
local spriteCache={}
local visualNodes,visualCounts,visualValues={},{},{}
local rootNodes,actorNodes={},{}
local visualWrites,visualChanges,visualUpdates=0,0,0
local visualRate,visualLastWrites,visualLastChanges=0,0,0
local uiParents={["BackHome"]="SelectScreen",["ReadyConfirm"]="SelectScreen",["ReadyConfirmText"]="ReadyConfirm",["PageLabel"]="SelectScreen",["PageNext"]="SelectScreen",["PagePrev"]="SelectScreen",["GridCard10"]="SelectScreen",["GridFace10"]="GridCard10",["GridRed10"]="GridCard10",["GridBlue10"]="GridCard10",["GridPlate10Corner1_1"]="GridCard10",["GridPlate10Corner1_-1"]="GridCard10",["GridPlate10Corner-1_1"]="GridCard10",["GridPlate10Corner-1_-1"]="GridCard10",["GridPlate10Middle"]="GridCard10",["GridPlate10"]="GridCard10",["GridCard9"]="SelectScreen",["GridFace9"]="GridCard9",["GridRed9"]="GridCard9",["GridBlue9"]="GridCard9",["GridPlate9Corner1_1"]="GridCard9",["GridPlate9Corner1_-1"]="GridCard9",["GridPlate9Corner-1_1"]="GridCard9",["GridPlate9Corner-1_-1"]="GridCard9",["GridPlate9Middle"]="GridCard9",["GridPlate9"]="GridCard9",["GridCard8"]="SelectScreen",["GridFace8"]="GridCard8",["GridRed8"]="GridCard8",["GridBlue8"]="GridCard8",["GridPlate8Corner1_1"]="GridCard8",["GridPlate8Corner1_-1"]="GridCard8",["GridPlate8Corner-1_1"]="GridCard8",["GridPlate8Corner-1_-1"]="GridCard8",["GridPlate8Middle"]="GridCard8",["GridPlate8"]="GridCard8",["GridCard7"]="SelectScreen",["GridFace7"]="GridCard7",["GridRed7"]="GridCard7",["GridBlue7"]="GridCard7",["GridPlate7Corner1_1"]="GridCard7",["GridPlate7Corner1_-1"]="GridCard7",["GridPlate7Corner-1_1"]="GridCard7",["GridPlate7Corner-1_-1"]="GridCard7",["GridPlate7Middle"]="GridCard7",["GridPlate7"]="GridCard7",["GridCard6"]="SelectScreen",["GridFace6"]="GridCard6",["GridRed6"]="GridCard6",["GridBlue6"]="GridCard6",["GridPlate6Corner1_1"]="GridCard6",["GridPlate6Corner1_-1"]="GridCard6",["GridPlate6Corner-1_1"]="GridCard6",["GridPlate6Corner-1_-1"]="GridCard6",["GridPlate6Middle"]="GridCard6",["GridPlate6"]="GridCard6",["GridCard5"]="SelectScreen",["GridFace5"]="GridCard5",["GridRed5"]="GridCard5",["GridBlue5"]="GridCard5",["GridPlate5Corner1_1"]="GridCard5",["GridPlate5Corner1_-1"]="GridCard5",["GridPlate5Corner-1_1"]="GridCard5",["GridPlate5Corner-1_-1"]="GridCard5",["GridPlate5Middle"]="GridCard5",["GridPlate5"]="GridCard5",["GridCard4"]="SelectScreen",["GridFace4"]="GridCard4",["GridRed4"]="GridCard4",["GridBlue4"]="GridCard4",["GridPlate4Corner1_1"]="GridCard4",["GridPlate4Corner1_-1"]="GridCard4",["GridPlate4Corner-1_1"]="GridCard4",["GridPlate4Corner-1_-1"]="GridCard4",["GridPlate4Middle"]="GridCard4",["GridPlate4"]="GridCard4",["GridCard3"]="SelectScreen",["GridFace3"]="GridCard3",["GridRed3"]="GridCard3",["GridBlue3"]="GridCard3",["GridPlate3Corner1_1"]="GridCard3",["GridPlate3Corner1_-1"]="GridCard3",["GridPlate3Corner-1_1"]="GridCard3",["GridPlate3Corner-1_-1"]="GridCard3",["GridPlate3Middle"]="GridCard3",["GridPlate3"]="GridCard3",["GridCard2"]="SelectScreen",["GridFace2"]="GridCard2",["GridRed2"]="GridCard2",["GridBlue2"]="GridCard2",["GridPlate2Corner1_1"]="GridCard2",["GridPlate2Corner1_-1"]="GridCard2",["GridPlate2Corner-1_1"]="GridCard2",["GridPlate2Corner-1_-1"]="GridCard2",["GridPlate2Middle"]="GridCard2",["GridPlate2"]="GridCard2",["GridCard1"]="SelectScreen",["GridFace1"]="GridCard1",["GridRed1"]="GridCard1",["GridBlue1"]="GridCard1",["GridPlate1Corner1_1"]="GridCard1",["GridPlate1Corner1_-1"]="GridCard1",["GridPlate1Corner-1_1"]="GridCard1",["GridPlate1Corner-1_-1"]="GridCard1",["GridPlate1Middle"]="GridCard1",["GridPlate1"]="GridCard1",["TeamSlot23"]="SelectScreen",["TeamName23"]="TeamSlot23",["TeamRound23"]="TeamSlot23",["TeamSlot23Caption"]="TeamSlot23",["TeamSlot23PlateCorner1_1"]="TeamSlot23",["TeamSlot23PlateCorner1_-1"]="TeamSlot23",["TeamSlot23PlateCorner-1_1"]="TeamSlot23",["TeamSlot23PlateCorner-1_-1"]="TeamSlot23",["TeamSlot23PlateMiddle"]="TeamSlot23",["TeamSlot23Plate"]="TeamSlot23",["TeamSlot23RimCorner1_1"]="TeamSlot23",["TeamSlot23RimCorner1_-1"]="TeamSlot23",["TeamSlot23RimCorner-1_1"]="TeamSlot23",["TeamSlot23RimCorner-1_-1"]="TeamSlot23",["TeamSlot23RimMiddle"]="TeamSlot23",["TeamSlot23Rim"]="TeamSlot23",["TeamSlot22"]="SelectScreen",["TeamName22"]="TeamSlot22",["TeamRound22"]="TeamSlot22",["TeamSlot22Caption"]="TeamSlot22",["TeamSlot22PlateCorner1_1"]="TeamSlot22",["TeamSlot22PlateCorner1_-1"]="TeamSlot22",["TeamSlot22PlateCorner-1_1"]="TeamSlot22",["TeamSlot22PlateCorner-1_-1"]="TeamSlot22",["TeamSlot22PlateMiddle"]="TeamSlot22",["TeamSlot22Plate"]="TeamSlot22",["TeamSlot22RimCorner1_1"]="TeamSlot22",["TeamSlot22RimCorner1_-1"]="TeamSlot22",["TeamSlot22RimCorner-1_1"]="TeamSlot22",["TeamSlot22RimCorner-1_-1"]="TeamSlot22",["TeamSlot22RimMiddle"]="TeamSlot22",["TeamSlot22Rim"]="TeamSlot22",["TeamSlot21"]="SelectScreen",["TeamName21"]="TeamSlot21",["TeamRound21"]="TeamSlot21",["TeamSlot21Caption"]="TeamSlot21",["TeamSlot21PlateCorner1_1"]="TeamSlot21",["TeamSlot21PlateCorner1_-1"]="TeamSlot21",["TeamSlot21PlateCorner-1_1"]="TeamSlot21",["TeamSlot21PlateCorner-1_-1"]="TeamSlot21",["TeamSlot21PlateMiddle"]="TeamSlot21",["TeamSlot21Plate"]="TeamSlot21",["TeamSlot21RimCorner1_1"]="TeamSlot21",["TeamSlot21RimCorner1_-1"]="TeamSlot21",["TeamSlot21RimCorner-1_1"]="TeamSlot21",["TeamSlot21RimCorner-1_-1"]="TeamSlot21",["TeamSlot21RimMiddle"]="TeamSlot21",["TeamSlot21Rim"]="TeamSlot21",["SelectReady2"]="SelectScreen",["SelectName2"]="SelectScreen",["TeamSlot13"]="SelectScreen",["TeamName13"]="TeamSlot13",["TeamRound13"]="TeamSlot13",["TeamSlot13Caption"]="TeamSlot13",["TeamSlot13PlateCorner1_1"]="TeamSlot13",["TeamSlot13PlateCorner1_-1"]="TeamSlot13",["TeamSlot13PlateCorner-1_1"]="TeamSlot13",["TeamSlot13PlateCorner-1_-1"]="TeamSlot13",["TeamSlot13PlateMiddle"]="TeamSlot13",["TeamSlot13Plate"]="TeamSlot13",["TeamSlot13RimCorner1_1"]="TeamSlot13",["TeamSlot13RimCorner1_-1"]="TeamSlot13",["TeamSlot13RimCorner-1_1"]="TeamSlot13",["TeamSlot13RimCorner-1_-1"]="TeamSlot13",["TeamSlot13RimMiddle"]="TeamSlot13",["TeamSlot13Rim"]="TeamSlot13",["TeamSlot12"]="SelectScreen",["TeamName12"]="TeamSlot12",["TeamRound12"]="TeamSlot12",["TeamSlot12Caption"]="TeamSlot12",["TeamSlot12PlateCorner1_1"]="TeamSlot12",["TeamSlot12PlateCorner1_-1"]="TeamSlot12",["TeamSlot12PlateCorner-1_1"]="TeamSlot12",["TeamSlot12PlateCorner-1_-1"]="TeamSlot12",["TeamSlot12PlateMiddle"]="TeamSlot12",["TeamSlot12Plate"]="TeamSlot12",["TeamSlot12RimCorner1_1"]="TeamSlot12",["TeamSlot12RimCorner1_-1"]="TeamSlot12",["TeamSlot12RimCorner-1_1"]="TeamSlot12",["TeamSlot12RimCorner-1_-1"]="TeamSlot12",["TeamSlot12RimMiddle"]="TeamSlot12",["TeamSlot12Rim"]="TeamSlot12",["TeamSlot11"]="SelectScreen",["TeamName11"]="TeamSlot11",["TeamRound11"]="TeamSlot11",["TeamSlot11Caption"]="TeamSlot11",["TeamSlot11PlateCorner1_1"]="TeamSlot11",["TeamSlot11PlateCorner1_-1"]="TeamSlot11",["TeamSlot11PlateCorner-1_1"]="TeamSlot11",["TeamSlot11PlateCorner-1_-1"]="TeamSlot11",["TeamSlot11PlateMiddle"]="TeamSlot11",["TeamSlot11Plate"]="TeamSlot11",["TeamSlot11RimCorner1_1"]="TeamSlot11",["TeamSlot11RimCorner1_-1"]="TeamSlot11",["TeamSlot11RimCorner-1_1"]="TeamSlot11",["TeamSlot11RimCorner-1_-1"]="TeamSlot11",["TeamSlot11RimMiddle"]="TeamSlot11",["TeamSlot11Rim"]="TeamSlot11",["SelectReady1"]="SelectScreen",["SelectName1"]="SelectScreen",["SelectionHint"]="SelectScreen",["RosterTitle"]="SelectScreen",CommandTitle='CommandScreen',CommandBody='CommandScreen',CommandClose='CommandScreen',ChooseRole1='SelectScreen',ChooseRole2='SelectScreen',ChooseRole3='SelectScreen',ChooseRole4='SelectScreen',ChooseRole5='SelectScreen',ChooseRole6='SelectScreen',ChooseRole7='SelectScreen',ChooseRole8='SelectScreen',ChooseRole9='SelectScreen',ChooseRole10='SelectScreen',ChooseRole11='SelectScreen',StartDuel='HomeScreen',ChooseKeqing='SelectScreen',ChooseDiluc='SelectScreen',ReadyConfirm='SelectScreen',ReadyConfirmText='ReadyConfirm',BackHome='SelectScreen',SelectName1='SelectScreen',SelectName2='SelectScreen',SelectReady1='SelectScreen',SelectReady2='SelectScreen',SelectionHint='SelectScreen',Rematch='ResultScreen',Reselect='ResultScreen',ResultHome='ResultScreen',ResultTitle='ResultScreen',ResultScore='ResultScreen'}
local function rootNode(name)
 local node=rootNodes[name];if not node then local parent=root;if uiParents[name]then parent=rootNode(uiParents[name])end;node=parent:FindChild(name);rootNodes[name]=node end;return node
end
local function actorNode(i,name)
 actorNodes[i]=actorNodes[i] or {};local node=actorNodes[i][name]
 if not node then node=actors[i]:FindChild(name);actorNodes[i][name]=node end;return node
end
local group1Motion={[3]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[4]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[5]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[6]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[7]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[8]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[9]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[10]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[11]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[12]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[13]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[14]={idle={{1,24},{2,24}},walk={{49,4},{50,4},{51,4},{52,4},{53,4},{54,4},{55,4},{56,4}}},[15]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[16]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}},[17]={idle={{1,24},{2,24}},walk={{3,8},{4,8},{5,8},{4,8}}}}
poseIds[3]["idle"]=1
poseIds[3]["idle2"]=2
poseIds[3]["walk1"]=3
poseIds[3]["walk2"]=5
poseIds[3]["crouch"]=6
poseIds[3]["guard"]=7
poseIds[3]["crouchGuard"]=8
poseIds[3]["jump"]=10
poseIds[3]["hurt"]=13
poseIds[3]["airHurt"]=14
poseIds[3]["down"]=15
poseIds[3]["getup"]=16
poseIds[3]["windup"]=17
poseIds[3]["slash"]=18
poseIds[3]["low"]=21
poseIds[3]["air"]=24
poseIds[3]["rising"]=24
poseIds[3]["special"]=26
poseIds[3]["eThrow"]=25
poseIds[3]["e1"]=26
poseIds[3]["e2"]=26
poseIds[3]["e3"]=26
poseIds[3]["e3Windup"]=25
poseIds[3]["teleport"]=26
poseIds[3]["qCharge"]=28
poseIds[3]["qRelease"]=29
poseIds[4]["idle"]=1
poseIds[4]["idle2"]=2
poseIds[4]["walk1"]=3
poseIds[4]["walk2"]=5
poseIds[4]["crouch"]=6
poseIds[4]["guard"]=7
poseIds[4]["crouchGuard"]=8
poseIds[4]["jump"]=10
poseIds[4]["hurt"]=13
poseIds[4]["airHurt"]=14
poseIds[4]["down"]=15
poseIds[4]["getup"]=16
poseIds[4]["windup"]=17
poseIds[4]["slash"]=18
poseIds[4]["low"]=21
poseIds[4]["air"]=24
poseIds[4]["rising"]=24
poseIds[4]["special"]=26
poseIds[4]["eThrow"]=25
poseIds[4]["e1"]=26
poseIds[4]["e2"]=26
poseIds[4]["e3"]=26
poseIds[4]["e3Windup"]=25
poseIds[4]["teleport"]=26
poseIds[4]["qCharge"]=28
poseIds[4]["qRelease"]=29
poseIds[5]["idle"]=1
poseIds[5]["idle2"]=2
poseIds[5]["walk1"]=3
poseIds[5]["walk2"]=5
poseIds[5]["crouch"]=6
poseIds[5]["guard"]=7
poseIds[5]["crouchGuard"]=8
poseIds[5]["jump"]=10
poseIds[5]["hurt"]=13
poseIds[5]["airHurt"]=14
poseIds[5]["down"]=15
poseIds[5]["getup"]=16
poseIds[5]["windup"]=17
poseIds[5]["slash"]=18
poseIds[5]["low"]=21
poseIds[5]["air"]=24
poseIds[5]["rising"]=24
poseIds[5]["special"]=26
poseIds[5]["eThrow"]=25
poseIds[5]["e1"]=26
poseIds[5]["e2"]=26
poseIds[5]["e3"]=26
poseIds[5]["e3Windup"]=25
poseIds[5]["teleport"]=26
poseIds[5]["qCharge"]=28
poseIds[5]["qRelease"]=29
poseIds[6]["idle"]=1
poseIds[6]["idle2"]=2
poseIds[6]["walk1"]=3
poseIds[6]["walk2"]=5
poseIds[6]["crouch"]=6
poseIds[6]["guard"]=7
poseIds[6]["crouchGuard"]=8
poseIds[6]["jump"]=10
poseIds[6]["hurt"]=13
poseIds[6]["airHurt"]=14
poseIds[6]["down"]=15
poseIds[6]["getup"]=16
poseIds[6]["windup"]=17
poseIds[6]["slash"]=18
poseIds[6]["low"]=21
poseIds[6]["air"]=24
poseIds[6]["rising"]=24
poseIds[6]["special"]=26
poseIds[6]["eThrow"]=25
poseIds[6]["e1"]=26
poseIds[6]["e2"]=26
poseIds[6]["e3"]=26
poseIds[6]["e3Windup"]=25
poseIds[6]["teleport"]=26
poseIds[6]["qCharge"]=28
poseIds[6]["qRelease"]=29
poseIds[7]["idle"]=1
poseIds[7]["idle2"]=2
poseIds[7]["walk1"]=3
poseIds[7]["walk2"]=5
poseIds[7]["crouch"]=6
poseIds[7]["guard"]=7
poseIds[7]["crouchGuard"]=8
poseIds[7]["jump"]=10
poseIds[7]["hurt"]=13
poseIds[7]["airHurt"]=14
poseIds[7]["down"]=15
poseIds[7]["getup"]=16
poseIds[7]["windup"]=17
poseIds[7]["slash"]=18
poseIds[7]["low"]=21
poseIds[7]["air"]=24
poseIds[7]["rising"]=24
poseIds[7]["special"]=26
poseIds[7]["eThrow"]=25
poseIds[7]["e1"]=26
poseIds[7]["e2"]=26
poseIds[7]["e3"]=26
poseIds[7]["e3Windup"]=25
poseIds[7]["teleport"]=26
poseIds[7]["qCharge"]=28
poseIds[7]["qRelease"]=29
poseIds[8]["idle"]=1
poseIds[8]["idle2"]=2
poseIds[8]["walk1"]=3
poseIds[8]["walk2"]=5
poseIds[8]["crouch"]=6
poseIds[8]["guard"]=7
poseIds[8]["crouchGuard"]=8
poseIds[8]["jump"]=10
poseIds[8]["hurt"]=13
poseIds[8]["airHurt"]=14
poseIds[8]["down"]=15
poseIds[8]["getup"]=16
poseIds[8]["windup"]=17
poseIds[8]["slash"]=18
poseIds[8]["low"]=21
poseIds[8]["air"]=24
poseIds[8]["rising"]=24
poseIds[8]["special"]=26
poseIds[8]["eThrow"]=25
poseIds[8]["e1"]=26
poseIds[8]["e2"]=26
poseIds[8]["e3"]=26
poseIds[8]["e3Windup"]=25
poseIds[8]["teleport"]=26
poseIds[8]["qCharge"]=28
poseIds[8]["qRelease"]=29
poseIds[9]["idle"]=1
poseIds[9]["idle2"]=2
poseIds[9]["walk1"]=3
poseIds[9]["walk2"]=5
poseIds[9]["crouch"]=6
poseIds[9]["guard"]=7
poseIds[9]["crouchGuard"]=8
poseIds[9]["jump"]=10
poseIds[9]["hurt"]=13
poseIds[9]["airHurt"]=14
poseIds[9]["down"]=15
poseIds[9]["getup"]=16
poseIds[9]["windup"]=17
poseIds[9]["slash"]=18
poseIds[9]["low"]=21
poseIds[9]["air"]=24
poseIds[9]["rising"]=24
poseIds[9]["special"]=26
poseIds[9]["eThrow"]=25
poseIds[9]["e1"]=26
poseIds[9]["e2"]=26
poseIds[9]["e3"]=26
poseIds[9]["e3Windup"]=25
poseIds[9]["teleport"]=26
poseIds[9]["qCharge"]=28
poseIds[9]["qRelease"]=29
-- Visual frame selection is derived from rollback simulation, never from image callbacks.
local function group1Sequence(seq,t)
 if not seq then return nil end
 for _,item in ipairs(seq)do if t<item[2]then return item[1]end;t=t-item[2]end
 return seq[#seq][1]
end
local function group1Pose(a,i)
 local m=group1Motion[a.role];if not m then return nil end
 local ids=poseIds[a.role]
 if phase~='fight' and phase~='intro' and phase~='roundLoad' and a.hp>0 and f[3-i].hp<=0 then return ids.attack14 end
 if a.down>0 then return ids.basic14
 elseif a.wake>0 then return ids.basic15
 elseif a.launched then return ids.basic13
 elseif a.stun>0 then return ids[a.guardStun and(a.crouch and'basic7'or'basic6')or'basic12']
 elseif a.attack then
  local atk=a.attack;local spec=specs[a.role][atk.kind];if not spec then return ids.basic0 end
  local kind=(atk.kind=='special'or atk.kind=='teleport'or atk.kind=='e2'or atk.kind=='e3')and'E'or atk.kind=='super'and'Q'or atk.kind=='low'and'lowA'or atk.kind=='rising'and'airA'or'A'
  if kind=='A'or kind=='E'then
   local offset=kind=='E'and 8 or 0;local t=atk.t;local phase,index
   if t<atk.startup then index=math.min(2,math.floor(t/math.max(1,atk.startup)*3))
   elseif t<atk.startup+spec.active then index=3+math.min(1,math.floor((t-atk.startup)/math.max(1,spec.active)*2))
   else index=5+math.min(2,math.floor((t-atk.startup-spec.active)/math.max(1,spec.recovery)*3))end
   return ids['connections'..(offset+index)]
  end
  local first=kind=='Q'and 11 or kind=='lowA'and 3 or 6
  local phase=atk.t<atk.startup and 0 or atk.t<atk.startup+spec.active and 1 or 2
  if kind=='airA'and phase==2 then return ids.basic10 end
  return ids['attack'..(first+phase)]or ids.basic10
 elseif a.y>0 then return ids[a.vy>0 and'basic9'or'basic10']
 elseif a.block then return ids[a.crouch and'basic7'or'basic6']
 elseif a.crouch then return ids.basic5
 elseif controls[i]and controls[i].input and(controls[i].input.left or controls[i].input.right)then return group1Sequence(m.walk,math.floor(a.walk*5)%32)
 end
 return group1Sequence(m.idle,tick%48)
end

local function updateSprite(i)
 local a=f[i];local art=actorNode(i,'Art');local ids=poseIds[a.role];local pose=ids.idle
 if a.down>0 then pose=ids.down
 elseif a.wake>0 then pose=ids.getup
 elseif a.launched then pose=ids.airHurt
 elseif a.stun>0 then pose=ids.hurt
 elseif a.attack then
  local atk=a.attack;local s=specs[a.role][atk.kind];local active=atk.t>=atk.startup
  if atk.kind=='low' then pose=active and ids.low or ids.crouch
  elseif atk.kind=='special' then pose=ids.eThrow or ids.e1 or ids.special or ids.slash
  elseif atk.kind=='teleport' then pose=active and ids.teleport or ids.eThrow
  elseif atk.kind=='e2' then pose=ids.e2
  elseif atk.kind=='e3' then pose=active and ids.e3 or ids.e3Windup
  elseif atk.kind=='super' then pose=active and ids.qRelease or(ids.qCharge or ids.guard)
  else pose=active and(atk.kind=='rising' and ids.rising or ids.slash)or ids.windup end
  if atk.t>atk.startup+s.active+s.recovery*.7 then pose=ids.idle end
 elseif a.y>0 then pose=ids.jump
 elseif a.block then pose=a.crouch and ids.crouchGuard or ids.guard
 elseif a.crouch then pose=ids.crouch
 else local c=controls[i] and controls[i].input
  if c and(c.left or c.right)then pose=math.floor(a.walk/1.6)%2==0 and ids.walk1 or ids.walk2
  elseif ids.idle2 and math.floor(tick/40)%2==1 then pose=ids.idle2 end
 end
 pose=group1Pose(a,i)or pose or ids.idle
 local key=a.role*100+pose
 if spriteCache[i]~=key then
  local data=spriteData[a.role][pose]
 if resourceGate.mode~='battle'or not data or not data.rows then return end;local pool=art:FindChild('Sprite')
  visualNodes[i]=visualNodes[i] or {};visualValues[i]=visualValues[i] or {}
  local nodes,values=visualNodes[i],visualValues[i]
  local count=data.count;local previous=visualCounts[i]or resourceGate.caps[i]
  for n=1,math.max(count,previous)do
   local node=nodes[n];if not node then node=loadingFind(pool,'P'..n);nodes[n]=node end
   local v=values[n];if not v then v={};values[n]=v end
   local visible=n<=count
   if v.visible~=visible then node:SetVisible(visible);v.visible=visible;visualWrites=visualWrites+1 end
   if visible then
    local px,py,pw,ph,color=framePixel(data,n)
    local x=(px+pw/2-data.anchor[1])*data.scale;local y=(data.anchor[2]-py-ph/2)*data.scale;local w,h=pw*data.scale,ph*data.scale
    if v.x~=x or v.y~=y then node:SetAnchoredPosition(x,y);v.x=x;v.y=y;visualWrites=visualWrites+1 end
    if v.w~=w or v.h~=h then node:SetSizeDelta(w,h);v.w=w;v.h=h;visualWrites=visualWrites+1 end
    if v.color~=color then node.imageColor=color;v.color=color;visualWrites=visualWrites+1 end
   end
  end
  visualCounts[i]=count;visualChanges=visualChanges+1
  spriteCache[i]=key
 end
 
 local lean=a.attack and (a.attack.t<a.attack.startup and 7 or -8) or (a.stun>0 and 12 or math.sin(a.walk)*1.3)
 art:SetLocalRotation(0,0,0)
 local roles=roleNames;rootNode(i==1 and 'Name1' or 'Name2').text=roles[a.role]..(i==1 and ' / \231\142\169\229\174\1821' or (aiEnabled and ' / \231\148\181\232\132\145' or ' / \231\142\169\229\174\1822'))
 local meter=rootNode(i==1 and 'Meter1' or 'Meter2');meter:SetSizeDelta(math.max(1,a.meter*4.8),8)
 meter:SetAnchoredPosition((i==1 and -565 or 565)+(i==1 and 1 or -1)*a.meter*2.4,245)
 rootNode(i==1 and 'Energy1' or 'Energy2').text='\232\131\189\233\135\143 '..math.floor(a.meter)..'/100'..(a.meter>=100 and ' \194\183 \232\182\133\229\191\133\230\157\128\229\176\177\231\187\170' or '')
end
local drawnStage=nil

local fxNodes,fxPose={},{}
local function drawPhoenix(i,pose)
 if fxPose[i]==pose then return end
 local data=phoenixData[pose];local pool=actorNode(i,'Phoenix');fxNodes[i]=fxNodes[i] or {}
 for n=1,338 do
  local node=fxNodes[i][n];if not node then node=loadingFind(pool,'F'..n);fxNodes[i][n]=node end
  local r=data.rows[n];node:SetVisible(r~=nil)
  if r then node:SetAnchoredPosition((r[1]+r[3]/2-data.anchor[1])*data.scale,(data.anchor[2]-r[2]-r[4]/2)*data.scale);node:SetSizeDelta(r[3]*data.scale,r[4]*data.scale);node.imageColor=r[5]end
 end
 fxPose[i]=pose
end

local function drawStage()
 if drawnStage==stage then return end
 drawnStage=stage

end

local function draw()
 for i=1,2 do
  local a,art=f[i],actorNode(i,'Art')
  actors[i]:SetAnchoredPosition(a.x,Collision.floorY()+a.y);rootNode('Shadow'..i):SetAnchoredPosition(a.x,Collision.floorY()-2);rootNode('Shadow'..i):SetSizeDelta(math.max(24,68-a.y*.14),5);art:SetLocalScale(a.face,1,1)
  art:SetAnchoredPosition(0,not a.attack and a.down<=0 and a.y==0 and not a.crouch and a.stun<=0 and math.sin(tick/20)*1.1 or 0)
  local swing=0
  if a.attack then local s=specs[f[i].role][a.attack.kind];swing=a.attack.t<a.attack.startup and -35 or (a.attack.t<a.attack.startup+s.active and 0 or 20);if a.attack.kind=='low' then swing=-12 end end
  updateSprite(i)
  actorNode(i,'Flash'):SetVisible(a.flash>0 and a.down<=0);actorNode(i,'GuardVisual'):SetVisible(a.block);actorNode(i,'GuardVisual'):SetAnchoredPosition(a.face*46,a.crouch and 62 or 115)
  actorNode(i,'Hitbox'):SetVisible(false);actorNode(i,'Hitbox'):SetAnchoredPosition(a.face*110,a.crouch and 45 or 120)
  local fx=actorNode(i,'SpecialFx');fx:SetVisible(false)
  local mark=actorNode(i,'Stiletto');mark:SetVisible(a.role==1 and(a.markLife or 0)>0)
  if (a.markLife or 0)>0 then mark:SetAnchoredPosition((a.markX or a.x)-a.x,92)end
  local bird=actorNode(i,'Phoenix');local atk=a.attack
  local birdOn=a.role==2 and atk and atk.kind=='super' and atk.t>=atk.startup and atk.t<atk.startup+specs[2].super.active
  bird:SetVisible(birdOn or false)
  if birdOn then
   local pose=math.floor((atk.t-atk.startup)/7)%2+1
   drawPhoenix(i,pose);bird:SetLocalScale(a.face,1,1);bird:SetAnchoredPosition(a.face*(90+(atk.t-atk.startup)*14),95)
  end
  for n=1,4 do
   local slash=actorNode(i,'BurstLine'..n)
   local on=a.role==1 and atk and atk.kind=='super' and atk.t>=atk.startup-5 and atk.t<atk.startup+specs[1].super.active
   slash:SetVisible(on or false)
  end
  local flame=actorNode(i,'FlameArc');local flaming=a.role==2 and atk and(atk.kind=='special' or atk.kind=='e2' or atk.kind=='e3')
  flame:SetVisible(flaming or false)
  if flaming then flame:SetLocalScale(a.face,1,1);flame:SetAnchoredPosition(a.face*95,atk.kind=='e3' and 70 or 105);flame:SetLocalRotation(0,0,atk.kind=='e2' and 30 or -25)end
  hpBars[i]:SetSizeDelta(math.max(1,480*a.hp/100),19);hpBars[i]:SetAnchoredPosition((i==1 and -565 or 565)+(i==1 and 1 or -1)*240*a.hp/100,264)
  rootNode(i==1 and 'Combo1' or 'Combo2').text=a.comboDisplay>0 and (a.comboHits..' \232\191\158\229\135\187 / '..a.comboDamage..' \228\188\164\229\174\179') or ''
  rootNode(i==1 and 'State1' or 'State2').text=a.launched and ('\230\181\174\231\169\186 / \232\191\189\229\135\187 '..a.airHits..'/5') or (a.down>0 and '\229\128\146\229\156\176' or (a.wake>0 and '\232\181\183\232\186\171\228\191\157\230\138\164' or ''))
 end
 drawStage()
 timerText.text=tostring(math.ceil(remaining));status.text=not onlineReady and '\231\173\137\229\190\133\229\143\140\228\186\186\230\168\161\229\188\143\239\188\154\231\142\169\229\174\1821\229\136\187\230\153\180 / \231\142\169\229\174\1822\232\191\170\229\141\162\229\133\139' or (phase=='fight' and ('\231\172\172 '..round..' \229\155\158\229\144\136 | '..wins[1]..' - '..wins[2]) or (phase=='DRAW ROUND' and '\230\156\172\229\155\158\229\144\136\229\185\179\229\177\128' or ((roleNames)[f[(wins[1]>=2 or phase=='KEQING WINS ROUND') and 1 or 2].role]..((wins[1]>=2 or wins[2]>=2) and '\232\181\162\229\190\151\230\175\148\232\181\155' or '\232\181\162\229\190\151\230\156\172\229\155\158\229\144\136'))))
 stats.text='\231\148\159\229\145\189 '..f[1].hp..' / '..f[2].hp..' | '..(f[1].attack and moveNames[f[1].role][f[1].attack.kind] or (f[1].block and (f[1].crouch and '\232\185\178\233\152\178' or '\231\171\153\233\152\178') or '\229\176\177\231\187\170'))..' | '..(f[2].attack and moveNames[f[2].role][f[2].attack.kind] or (f[2].block and '\233\152\178\229\190\161' or '\231\148\181\232\132\145\229\175\185\230\137\139'))..' | \229\191\133\230\157\128 236+J/K / \230\140\145\233\163\158 623+K / \232\182\133\229\191\133\230\157\128 236236+K'
 stats.text='\229\144\140\230\173\165\229\184\167 '..tick..' | '..string.gsub(stats.text,'\231\148\181\232\132\145\229\175\185\230\137\139','\229\176\177\231\187\170')
end
function OnInit()
 root=script.object;actors={root:FindChild('Keqing'),root:FindChild('Diluc')};hpBars={root:FindChild('Hp1'),root:FindChild('Hp2')};status=root:FindChild('Status');timerText=root:FindChild('Timer');stats=root:FindChild('Stats');restart();draw()
end
local function bind(name,callback)root:AddKeyEventListener(Enum.KeyEventType[name],function()callback();return true end)end
local fields={'guardStun','x','y','vy','hp','face','stun','down','wake','launched','airHits','block','crouch','chainCount','comboHits','comboDamage','comboOwner','comboDisplay','flash','walk','role','meter'}
local boolFields={guardStun=true,launched=true,block=true,crouch=true}
local function packState()
 local values={}
 local function add(v)values[#values+1]=type(v)=='number' and string.format('%.17g',v) or tostring(v)end
 add(tick);add(acc);add(phase);add(round);add(wins[1]);add(wins[2]);add(remaining);add(freeze);add(intermission);add(stage)
 for i=1,2 do local p=f[i]
  for _,key in ipairs(fields)do add(boolFields[key] and (p[key] and 1 or 0) or p[key])end
  local atk=p.attack;add(atk and atk.kind or 'none');add(atk and atk.t or 0);add(atk and atk.hit and 1 or 0);add(atk and atk.connected and 1 or 0);add(atk and atk.startup or 0)
 end
 return table.concat(values,'|')
end
local function unpackState(data)
 local values={};for v in string.gmatch(data,'[^|]+')do values[#values+1]=v end
 if #values~=10+2*(#fields+5) then print('NET_BAD_STATE '..#values);return false end
 local index=0;local function get()index=index+1;return values[index]end;local function num()return tonumber(get())or 0 end
 tick=num();acc=num();phase=get();round=num();wins={num(),num()};remaining=num();freeze=num();intermission=num();stage=num()
 for i=1,2 do local p=f[i]
  for _,key in ipairs(fields)do local value=num();if boolFields[key]then p[key]=value==1 else p[key]=value end end
  local kind=get();local t,hit,connected,startup=num(),num(),num(),num();p.attack=kind~='none' and {kind=kind,t=t,hit=hit==1,connected=connected==1,startup=startup}or nil
 end
 draw();return true
end
publishState=function()end
local function applyInput(player,event,value)
 if phase~='fight' or event=='restart' or event=='role' or event=='stage' then return end
 if event=='stage' then stage=clamp(value,1,210);return end
 if event=='role' then roleChoice[player]=clamp(value,1,2);restart();return end
 if event=='restart' then restart();return end
 withControl(player,function()
  if event=='stick' then input.left=(value==1 or value==4 or value==7);input.right=(value==3 or value==6 or value==9);input.down=value<=3;recordDirection();if value>=7 then input.jump=true end
  elseif event=='left' or event=='right' or event=='down' or event=='block' then setDirection(event,value==1)
  elseif event=='jump' then input.jump=true
  elseif event=='light' or event=='heavy' then
   if value==0 then heldButtons[event]=false elseif not heldButtons[event]then heldButtons[event]=true;pressAttack(event)end
  elseif event=='skill' then input.special=12;motionMove='special' elseif event=='ultimate' then input.special=12;motionMove='super' elseif event=='clickLight' then pressAttack('light')elseif event=='clickHeavy' then pressAttack('heavy')end
 end)
end

local function copy(value,seen)
 if type(value)~='table' then return value end
 seen=seen or {};if seen[value]then return seen[value]end
 local result={};seen[value]=result;for key,v in pairs(value)do result[key]=copy(v,seen)end;return result
end
local function capture()
 return copy({f=f,controls=controls,input=input,directions=directions,lastDirection=lastDirection,motionMove=motionMove,heldButtons=heldButtons,controlPlayer=controlPlayer,tick=tick,phase=phase,round=round,wins=wins,remaining=remaining,freeze=freeze,intermission=intermission,stage=stage,roleChoice=roleChoice,roundIntro=roundIntro,roundWinner=roundWinner,collisionResults=Collision.results})
end
local function restore(snapshot)
 local s=copy(snapshot);f=s.f;controls=s.controls;input=s.input;directions=s.directions;lastDirection=s.lastDirection;motionMove=s.motionMove;heldButtons=s.heldButtons;controlPlayer=s.controlPlayer;tick=s.tick;phase=s.phase;round=s.round;wins=s.wins;remaining=s.remaining;freeze=s.freeze;intermission=s.intermission;stage=s.stage;roleChoice=s.roleChoice;roundIntro=s.roundIntro;roundWinner=s.roundWinner or 0;Collision.results=s.collisionResults or{}
end

local function NewRollbackSession(callbacks,slot)
 local r={frame=0,confirmed=0,peerAck=0,localFrames={},remoteFrames={},used={},history={},pending={},dirty=nil,rollbacks=0,replayed=0,stalled=false,error=nil}
 local allowed={skill=true,ultimate=true,left=true,right=true,down=true,block=true,jump=true,light=true,heavy=true,clickLight=true,clickHeavy=true,stick=true,role=true,stage=true,restart=true}
 local function fail(message)r.error=message;return false end
 local function encode(events)
  local parts={};for _,e in ipairs(events)do parts[#parts+1]=e[1]..':'..e[2]end
  return #parts==0 and '-' or table.concat(parts,',')
 end
 local function decode(s)
  if s=='-' then return {}end
  local events={}
  for item in string.gmatch(s,'[^,]+')do
   local event,value=string.match(item,'^([%a]+):(%-?%d+)$');value=tonumber(value)
   if not allowed[event] or not value or value<0 or value>9 or #events>=32 then return nil end
   events[#events+1]={event,value}
  end
  if #events==0 or encode(events)~=s then return nil end
  return events
 end
 function r:queue(event,value)
  if self.error then return end
  if not allowed[event] or #self.pending>=32 then fail('INPUT_OVERFLOW');return end
  self.pending[#self.pending+1]={event,value==nil and 1 or value}
 end
 local function simulate(n)
  r.history[n]=callbacks.capture()
  local remote=r.remoteFrames[n] or '-';r.used[n]=remote
  local bySlot={};bySlot[slot]=decode(r.localFrames[n]);bySlot[3-slot]=decode(remote)
  
  for player=1,2 do for _,e in ipairs(bySlot[player])do callbacks.input(player,e[1],e[2])end end
  callbacks.step()
 end
 function r:repair()
  if self.error or not self.dirty then return end
  local from=self.dirty;self.dirty=nil
  if not self.history[from] then fail('HISTORY_EXPIRED');return end
  callbacks.restore(self.history[from]);self.rollbacks=self.rollbacks+1
  for n=from,self.frame do simulate(n);self.replayed=self.replayed+1 end
 end
 function r:advance()
  self:repair();if self.error then return false end
  if self.frame-self.confirmed>=12 then self.stalled=true;return false end
  self.stalled=false
  local n=self.frame+1;self.localFrames[n]=encode(self.pending);self.pending={}
  simulate(n);self.frame=n
  local obsolete=n-120
  if obsolete>0 then self.history[obsolete]=nil;self.used[obsolete]=nil;self.remoteFrames[obsolete]=nil end
  
  for old in pairs(self.localFrames)do if old<=self.peerAck-24 then self.localFrames[old]=nil end end
  return true
 end
 function r:packet()
  if self.frame==0 then return nil end
  local first=math.max(1,math.min(self.peerAck+1,self.frame-5))
  local last=math.min(self.frame,first+23);local parts={}
  for n=first,last do if not self.localFrames[n] then fail('SEND_HISTORY_EXPIRED');return nil end;parts[#parts+1]=self.localFrames[n]end
  return first,self.confirmed,table.concat(parts,'|')
 end
 function r:receive(first,ack,payload)
  if self.error then return false end
  if type(first)~='number' or first~=math.floor(first) or first<1 or first>self.frame+240 or type(ack)~='number' or ack~=math.floor(ack) or ack<0 or ack>self.frame or type(payload)~='string' or #payload>8192 then return fail('BAD_PACKET')end
  local entries={};for s in string.gmatch(payload,'[^|]+')do entries[#entries+1]=s end
  if #entries<1 or #entries>24 or table.concat(entries,'|')~=payload then return fail('BAD_BATCH')end
  for _,s in ipairs(entries)do if not decode(s)then return fail('BAD_INPUT')end end
  self.peerAck=math.max(self.peerAck,ack)
  for i,s in ipairs(entries)do
   local n=first+i-1
   if n>self.confirmed then
    if self.remoteFrames[n] and self.remoteFrames[n]~=s then return fail('CONFLICTING_INPUT')end
    self.remoteFrames[n]=s
    if n<=self.frame and self.used[n]~=s then self.dirty=math.min(self.dirty or n,n)end
   end
  end
  while self.remoteFrames[self.confirmed+1] do self.confirmed=self.confirmed+1 end
  return true
 end
 return r
end

local menuEpoch=1
local rb=nil
local debugNet={tx=0,bytes=0,last='\231\173\137\229\190\133\229\144\175\229\138\168',previous='',updates=0}
local function sendInput(event,value)
 if onlineReady and rb then rb:queue(event,value)end
end
local function flushFrames()
 if not rb or rb.error then return end
 local first,ack,payload=rb:packet();if not first then return end
 local sig=game.ServerSignal('GF10Frames');sig:AddInt(seat);sig:AddInt(first);sig:AddInt(ack);sig:AddString(payload);sig:AddInt(menuEpoch);sig:SendSignal();debugNet.tx=debugNet.tx+1;debugNet.bytes=#payload
end

local helloCount,joinCount,handshakeTime,receiveCount=0,0,0,0
local seatProbeCount=0
local seatProbe='\229\184\173\228\189\141\230\163\128\230\181\139\239\188\154\229\176\154\230\156\170\230\148\182\229\136\176\229\155\158\232\176\131'
local function helloRequest()
 helloCount=helloCount+1
 debugNet.last='\232\176\131\231\148\168 Hello \229\143\145\233\128\129'
 if helloCount<=3 or helloCount%10==0 then print('[NET CLIENT] Hello SEND '..helloCount)end
 game.ServerSignal('GF10Hello'):SendSignal()
end
local function joinRequest()
 joinCount=joinCount+1
 debugNet.last='\232\176\131\231\148\168 Join \229\143\145\233\128\129'
 if joinCount<=3 or joinCount%10==0 then print('[NET CLIENT] Join SEND '..joinCount)end
 local s=game.ServerSignal('GF10Join');s:AddInt(menuEpoch);s:SendSignal()
end
-- R1/R2/R3 are separate rounds, not in-round tag / relay.
uiParents.StartDuelHit='HomeScreen'
local menuMode='home'
-- [line 963 data omitted, len=1368841] resourceGate.homePortraitData={{textArt=true,palette={"33295
resourceGate.homePortraitNodes={{},{}}
resourceGate.showHome=function()return menuMode=='home'end
local menuReady,menuLoaded={false,false},{false,false}
local menuRevision,menuSeen,menuTime=0,{-1,-1},0
local debugPanel,commandOpen=false,false
local portraitNodes,portraitRole={},{}
local flowChoice,flowSeen,flowRevision={0,0},{-1,-1},0
local teamChoice={{0,0,0},{0,0,0}}
local previewChoice={0,0}
local rosterPage,menuDirty=1,true
local plannedRound,teamScores=1,{0,0}
local gridNodes,gridRoles={},{}
local function plateColor(name,color)
 rootNode(name).imageColor=color;rootNode(name..'Middle').imageColor=color
 for _,sx in ipairs({-1,1})do for _,sy in ipairs({-1,1})do rootNode(name..'Corner'..sx..'_'..sy).imageColor=color end end
end
local function selected(who,role)for n=1,3 do if teamChoice[who][n]==role then return n end end return nil end
local function complete(who)return teamChoice[who][1]>0 and teamChoice[who][2]>0 and teamChoice[who][3]>0 end
resourceGate.textArtCache={}
resourceGate.textGeometry={advance=20,glyphHeight=20,edgeFill=1.025,padX=2,padY=0}
resourceGate.textNodes=function(parent)
 local c=resourceGate.textArtCache[parent.name]
 if not c then c={nodes={}};for _,node in ipairs(parent:GetChildren())do local i=tonumber(string.match(node.name,'^TextArt(%d+)$'));if i then c.nodes[i]=node end end;resourceGate.textArtCache[parent.name]=c end
 return c
end
resourceGate.paintTextChunk=function(parent,data,scale,i)
 local c=resourceGate.textNodes(parent);local node=c.nodes[i];local chunk=data.chunks[i]
 if not node then error('Missing text row '..parent.name..':'..i)end
 if not chunk.text then
  local parts={'<b>'};for at=1,#chunk.runs,9 do local color=tonumber(string.sub(chunk.runs,at,at+5),16);local count=tonumber(string.sub(chunk.runs,at+6,at+8),16)
   parts[#parts+1]='<color=#'..data.palette[color]..'>'..string.rep('\226\150\136',count)..'</color>'
  end;parts[#parts+1]='</b>';chunk.text=table.concat(parts)
  if #chunk.text>1000 then error('Rich text chunk budget exceeded')end
 end
 node.text=chunk.text;node:SetVisible(true)
 local g=resourceGate.textGeometry;local width,height=chunk.w*g.advance+40,60
 -- Native block glyph has no line-leading here. Source coordinates set every row independently.
 local fillHeight=chunk.h+(g.edgeFill-1)
 node:SetSizeDelta(width,height);node:SetLocalScale(scale/g.advance,scale/g.glyphHeight*fillHeight,1)
 local inset=0
 node:SetAnchoredPosition((width/2-g.padX)*scale/g.advance+(chunk.x-data.anchor[1])*scale+inset,(data.anchor[2]-chunk.y)*scale-height/2*scale/g.glyphHeight*fillHeight+g.padY*scale/g.glyphHeight+inset)
end
resourceGate.paintTextArt=function(parent,data,scale)
 local c=resourceGate.textNodes(parent);if c.frame==data and c.scale==scale then return end
 for i,node in ipairs(c.nodes)do if data.chunks[i]then resourceGate.paintTextChunk(parent,data,scale,i)else node:SetVisible(false)end end
 c.frame=data;c.scale=scale
end
local function paintFrame(parent,prefix,data,scale,nodes)
 if data and data.textArt then resourceGate.paintTextArt(parent,data,scale);return end
 if not data or not data.rows then return end
 for n=1,data.count do
  local node=nodes[n];if not node then node=loadingFind(parent,prefix..n);nodes[n]=node end
  local x,y,w,h,color=framePixel(data,n);node:SetVisible(true);node:SetAnchoredPosition((x+w/2-data.anchor[1])*scale,(data.anchor[2]-y-h/2)*scale);node:SetSizeDelta(w*scale,h*scale);node.imageColor=color
 end
 for n=data.count+1,#nodes do nodes[n]:SetVisible(false)end
end
local function drawPortrait(i,role)
 if role<=0 then return end
 local key=role..':'..menuMode;if portraitRole[i]==key then return end
 local pool=rootNode('Portrait'..i);portraitNodes[i]=portraitNodes[i]or{}
 paintFrame(pool,'FacePx',portraitData[role],(menuMode=='battle'and 1.45 or 2.7)*48/portraitData[role].w,portraitNodes[i]);portraitRole[i]=key
end
local function sendSelection()
 if seat~=1 and seat~=2 then return end
 local s=game.ServerSignal('GF10Team');s:AddInt(seat)
 for n=1,3 do s:AddInt(teamChoice[seat][n])end
 s:AddInt(menuMode=='home'and 3 or(menuLoaded[seat]and 2 or(menuReady[seat]and 1 or 0)))
 s:AddInt(stage);s:AddInt(menuEpoch);s:AddInt(menuRevision);s:AddInt(plannedRound);s:AddInt(teamScores[1]);s:AddInt(teamScores[2]);s:SendSignal()
end
local function startNetworkRound()
 if plannedRound==1 then restart()else round=plannedRound;wins={teamScores[1],teamScores[2]};tick=0;resetRound()end
 menuDirty=true
end
local function leaveMatch(destination,targetEpoch)
 menuEpoch=targetEpoch and math.max(menuEpoch,targetEpoch)or(menuEpoch+1);menuRevision=menuRevision+1;menuSeen={-1,-1}
 menuReady={false,false};menuLoaded={false,false};onlineReady=false;joined=false;rb=nil;flowChoice={0,0};flowSeen={-1,-1}
 Collision.results={};plannedRound=1;teamScores={0,0};teamChoice={{0,0,0},{0,0,0}};previewChoice={0,0}
 menuMode=destination or'select';commandOpen=false;menuDirty=true
 resourceGate.request('menu',roleChoice);sendSelection()
end
local function chooseRole(role)
 if menuMode~='select' then return end
 if seat~=1 and seat~=2 then rootNode('SelectionHint').text='等待服务器分配席位：FighterHello → FighterSeat';print('[SELECT INPUT] blocked: no FighterSeat');helloRequest();return end
 if resourceGate.busy or menuReady[seat]then return end
 local at=selected(seat,role)
 if not at and complete(seat)then rootNode('SelectionHint').text='\233\152\181\229\174\185\229\183\178\230\187\161\239\188\154\231\130\185\229\135\187\229\183\178\233\128\137\229\164\180\229\131\143\230\136\150\229\155\158\229\144\136\230\160\143\228\189\141\230\146\164\229\155\158\229\144\142\229\134\141\233\128\137';return end
 if at then for n=at,2 do teamChoice[seat][n]=teamChoice[seat][n+1]end;teamChoice[seat][3]=0
 else for n=1,3 do if teamChoice[seat][n]==0 then teamChoice[seat][n]=role;break end end end
 previewChoice[seat]=at and(teamChoice[seat][3]>0 and teamChoice[seat][3]or(teamChoice[seat][2]>0 and teamChoice[seat][2]or teamChoice[seat][1]))or role;roleChoice[seat]=teamChoice[seat][1]>0 and teamChoice[seat][1]or role
 menuRevision=menuRevision+1;menuDirty=true;sendSelection();resourceGate.request('menu',roleChoice)
end
local function setReady()
 if menuMode~='select'or resourceGate.busy or(seat~=1 and seat~=2)then return end
 if not complete(seat)then rootNode('SelectionHint').text='\232\175\183\229\133\136\233\128\137\230\187\161\228\184\137\228\184\170\232\167\146\232\137\178\239\188\154ROUND 1 \226\134\146 ROUND 2 \226\134\146 ROUND 3';return end
 menuReady[seat]=not menuReady[seat];menuLoaded[seat]=false;menuRevision=menuRevision+1
 roleChoice[seat]=teamChoice[seat][1];menuDirty=true;sendSelection()
end
local function sendFlow(action)
 if seat<1 then return end
 flowRevision=flowRevision+1;flowChoice[seat]=action;menuDirty=true
 local s=game.ServerSignal('GF10Flow');s:AddInt(seat);s:AddInt(action);s:AddInt(menuEpoch);s:AddInt(flowRevision);s:SendSignal()
 if action==2 then leaveMatch('select')elseif action==3 then leaveMatch('home')end
end
local function retryFlow()
 if seat>0 and flowChoice[seat]==1 then local s=game.ServerSignal('GF10Flow');s:AddInt(seat);s:AddInt(1);s:AddInt(menuEpoch);s:AddInt(flowRevision);s:SendSignal()end
end
local function menuBind(name,callback)local control=rootNode(name);local hit=control:FindChild('InputHit')or control;hit:AddCursorEventListener(Enum.CursorEventType.CursorClick,callback)end
local function beginRoundLoad(number,score)
 plannedRound=number;teamScores={score[1],score[2]};round=number;wins={score[1],score[2]}
 roleChoice={teamChoice[1][math.min(number,3)],teamChoice[2][math.min(number,3)]}
 menuReady={true,true};menuLoaded={false,false};onlineReady=false;joined=false;rb=nil;menuMode='roundload';menuDirty=true
 resourceGate.request('battle',roleChoice)
end
local function menuStart()
 script:RegisterServerSignalHandler('GF10TeamOut',function(_,p)
  local who,flag,map,epoch,revision,number,w1,w2=tonumber(p[1]),tonumber(p[5]),tonumber(p[6]),tonumber(p[7]),tonumber(p[8]),tonumber(p[9]),tonumber(p[10]),tonumber(p[11])
  if(who~=1 and who~=2)or who==seat or not flag or flag<0 or flag>3 or not map or map<1 or map>210 or map~=math.floor(map)or not epoch or epoch<menuEpoch or not revision or revision<0 or not number or number<1 or number>3 or not w1 or not w2 or w1<0 or w2<0 or w1>2 or w2>2 then return end
  local team={tonumber(p[2]),tonumber(p[3]),tonumber(p[4])}
  for n=1,3 do if not team[n]or team[n]<0 or team[n]>9 or team[n]~=math.floor(team[n])then return end;for j=1,n-1 do if team[n]>0 and team[n]==team[j]then return end end end
  if(flag==1 or flag==2)and(team[1]==0 or team[2]==0 or team[3]==0)then return end
  local changed=epoch>menuEpoch
  if changed then
   local nextRound=who==1 and number>1 and(flag==1 or flag==2)and complete(seat)
   local rematching=number==1 and(flag==1 or flag==2)and flowChoice[seat]==1 and complete(seat)
   menuEpoch=epoch;menuSeen={-1,-1};menuRevision=menuRevision+1;onlineReady=false;joined=false;rb=nil;flowChoice={0,0};flowSeen={-1,-1}
   if nextRound then teamChoice[who]=team;stage=map;beginRoundLoad(number,{w1,w2})
   elseif rematching then plannedRound=1;teamScores={0,0};roleChoice={teamChoice[1][1],teamChoice[2][1]};menuMode='roundload';menuReady={true,true};menuLoaded={false,false};resourceGate.request('battle',roleChoice)
   else plannedRound=1;teamScores={0,0};teamChoice[seat]={0,0,0};previewChoice[seat]=0;menuMode=flag==3 and'home'or'select';menuReady={false,false};menuLoaded={false,false};resourceGate.request('menu',roleChoice)end
  end
  if revision<=menuSeen[who]then return end;menuSeen[who]=revision
  local oldPreview=previewChoice[who];teamChoice[who]=team;previewChoice[who]=team[3]>0 and team[3]or(team[2]>0 and team[2]or team[1])
  if who==1 then stage=map end
  roleChoice[who]=team[math.min(plannedRound,3)]>0 and team[math.min(plannedRound,3)]or roleChoice[who]
  menuReady[who]=(flag==1 or flag==2);menuLoaded[who]=flag==2;menuDirty=true
  if not changed and menuMode=='select'and oldPreview~=previewChoice[who]and resourceGate.mode=='menu'then resourceGate.request('menu',roleChoice)end
  if changed then sendSelection()end
 end)
 script:RegisterServerSignalHandler('GF10FlowOut',function(_,p)
  local who,action,epoch,revision=tonumber(p[1]),tonumber(p[2]),tonumber(p[3]),tonumber(p[4])
  if(who~=1 and who~=2)or who==seat or not epoch or(action==1 and epoch~=menuEpoch)or(action~=1 and(epoch<menuEpoch-1 or epoch>menuEpoch))or not revision or revision<=flowSeen[who]or(action~=1 and action~=2 and action~=3)then return end
  flowSeen[who]=revision;flowChoice[who]=action;menuDirty=true
  if action==2 or action==3 then leaveMatch(action==2 and'select'or'home',epoch+1)end
 end)
 menuBind('StartDuelHit',function()menuMode='select';resourceGate.request('menu',roleChoice);if seat==1 then stage=math.random(1,210)end;menuRevision=menuRevision+1;menuDirty=true;sendSelection()end)
 for n=1,10 do local cell=n;menuBind('GridCard'..cell,function()local role=(rosterPage-1)*10+cell;if role<=9 then chooseRole(role)end end)end
 for i=1,2 do for n=1,3 do local who,at=i,n;menuBind('TeamSlot'..who..at,function()if who==seat and teamChoice[who][at]>0 then chooseRole(teamChoice[who][at])end end)end end
 local function page(delta)if resourceGate.busy then return end;rosterPage=(rosterPage-1+delta)%math.ceil(9/10)+1;menuDirty=true;resourceGate.request('menu',roleChoice)end
 menuBind('PagePrev',function()page(-1)end);menuBind('PageNext',function()page(1)end)
 menuBind('ReadyConfirm',setReady);menuBind('BackHome',function()sendFlow(3)end)
 menuBind('Rematch',function()sendFlow(1)end);menuBind('Reselect',function()sendFlow(2)end);menuBind('ResultHome',function()sendFlow(3)end)
 menuBind('DebugToggle',function()debugPanel=not debugPanel;menuDirty=true end)
 menuBind('CommandToggle',function()commandOpen=not commandOpen;menuDirty=true end);menuBind('CommandClose',function()commandOpen=false;menuDirty=true end)
 menuBind('ExitMatch',function()sendFlow(3)end)
 resourceGate.menuRoles=function()return previewChoice,rosterPage end
 resourceGate.teamRoles=function()return teamChoice end
 resourceGate.stageFrame=function()return Collision.stageData[Collision.stageId(stage,plannedRound)]end
 resourceGate.prefetchRoles=function()return{menuMode=='select'and menuReady[1]and teamChoice[1][1]or 0,menuMode=='select'and menuReady[2]and teamChoice[2][1]or 0}end
 resourceGate.completed=function(mode)if mode~='battle'then Collision.stagePaintKey=nil;Collision.stageNodes={}end;Collision.hudNodes={};Collision.hudKeys={};
  spriteCache={};visualNodes={};visualValues={};visualCounts={};fxNodes={};fxPose={};portraitNodes={};portraitRole={};gridNodes={};gridRoles={};resourceGate.homePortraitNodes={{},{}};resourceGate.homePaintKeys={};menuDirty=true
  if mode=='battle'then menuLoaded[seat]=true;menuRevision=menuRevision+1;sendSelection()end
 end
end
function Collision.drawHUD(fighting)
 local host=rootNode('BattleTeamHUD');host:SetVisible(fighting)
 for p=1,2 do for n=1,3 do local name='BattleTeam'..p..n;local plate=host:FindChild(name..'Plate');local winner=Collision.results[n]
 local active=winner==nil and n==round;local loss=winner~=nil and winner~=0 and winner~=p
 local color=loss and 0xff555b65 or(p==1 and(active and 0xff8bcaff or 0xff438ce7)or(active and 0xffffa4a4 or 0xffe45565))
 for _,stripe in ipairs(plate:GetChildren())do stripe.imageColor=color end
 plate:SetLocalScale(active and 1.3 or 1,active and 1.3 or 1,1)
 host:FindChild(name..'Face'):SetVisible(false);host:FindChild(name..'Text'):SetVisible(false)
 end end
end
function Collision.drawBoxes()
 for p=1,2 do local a=f[p];local profile=Collision.profiles[a.role]
  local boxes={Push={a.x-profile.push,a.y,a.x+profile.push,a.y+profile.height},Hurt=Collision.hurt(a)}
  if a.attack then local s=specs[a.role][a.attack.kind];if a.attack.t>=a.attack.startup and a.attack.t<a.attack.startup+s.active then boxes.Attack=Collision.attack(a,s,s.range)end end
  for _,kind in ipairs({'Push','Hurt','Attack'})do local node=rootNode('Collision'..kind..p);local b=boxes[kind];node:SetVisible(menuMode=='battle'and debugPanel and b~=nil);if b then node:SetAnchoredPosition((b[1]+b[3])/2,Collision.floorY()+(b[2]+b[4])/2);node:SetSizeDelta(b[3]-b[1],b[4]-b[2])end end
 end
end
function Collision.floorY()
 local frame=Collision.stageData[Collision.stageId(stage,round)];local cw,ch=game.GetUICanvasSize()
 return -ch*.31
end
function Collision.drawStage(fighting)
 local parent=rootNode('CountryStage');parent:SetVisible(fighting)
 if not fighting then return end
 local id=Collision.stageId(stage,round);local cw,ch=game.GetUICanvasSize();local frame=Collision.stageData[id];local scale=math.max(cw/frame.w,ch/frame.h)
 local key=id..':'..cw..':'..ch
 if Collision.stagePaintKey~=key then Collision.stageNodes=Collision.stageNodes or{};paintFrame(parent,'StagePx',Collision.stageData[id],scale,Collision.stageNodes);Collision.stagePaintKey=key end
end
local function menuDraw()
 if resourceGate.busy then return end
 if onlineReady and phase=='roundLoad'then
  if seat==1 then menuEpoch=menuEpoch+1;menuRevision=menuRevision+1;menuSeen={-1,-1};beginRoundLoad(math.min(3,round+(roundWinner>0 and 1 or 0)),wins);sendSelection()
  else onlineReady=false;rb=nil;menuMode='waitingRound';menuDirty=true end
  return
 end
 if menuMode=='select'and menuReady[1]and menuReady[2]and not menuLoaded[seat]and resourceGate.mode~='battle'then
  plannedRound=1;teamScores={0,0};roleChoice={teamChoice[1][1],teamChoice[2][1]};menuMode='roundload';menuDirty=true;resourceGate.request('battle',roleChoice);return
 end
 if flowChoice[1]==1 and flowChoice[2]==1 then
  menuEpoch=menuEpoch+1;flowChoice={0,0};flowSeen={-1,-1};menuSeen={-1,-1};menuRevision=menuRevision+1;plannedRound=1;teamScores={0,0};roleChoice={teamChoice[1][1],teamChoice[2][1]}
  menuReady={true,true};menuLoaded={false,false};onlineReady=false;joined=false;rb=nil;menuMode='roundload';menuDirty=true;resourceGate.request('battle',roleChoice);sendSelection();return
 end
 local result=onlineReady and(wins[1]>=2 or wins[2]>=2)
 if not menuDirty then return end;menuDirty=false
 local selecting=menuMode=='select';local fighting=menuMode=='battle'
 local device=game.GetDevice();local touch=device==Enum.Device.Mobile or device==Enum.Device.MobileController
 Collision.drawStage(fighting);Collision.drawHUD(fighting);Collision.drawBoxes();rootNode('HomeScreen'):SetVisible(menuMode=='home');if menuMode=='home'then local cw,ch=game.GetUICanvasSize();local hs=math.min(1,cw/1600,ch/900);for i=1,2 do local bust=rootNode('HomeScreen'):FindChild('HomeBust'..i);bust:SetAnchoredPosition((i==1 and -490 or 490)*hs,-ch/2+300*hs);local key=cw..':'..ch;resourceGate.homePaintKeys=resourceGate.homePaintKeys or{};if resourceGate.homePaintKeys[i]~=key then paintFrame(bust,'HomePx',resourceGate.homePortraitData[i],resourceGate.homePortraitData[i].scale*hs,resourceGate.homePortraitNodes[i]);resourceGate.homePaintKeys[i]=key end end;for _,name in ipairs({'GameTitle','StartDuel','StartDuelHit'})do local node=rootNode('HomeScreen'):FindChild(name);node.localScaleX=hs;node.localScaleY=hs;node:SetAnchoredPosition(0,(name=='GameTitle'and 155 or -100)*hs)end end;rootNode('SelectScreen'):SetVisible(selecting);rootNode('ResultScreen'):SetVisible(fighting and result)
 for _,name in ipairs({'Stats','Timer','Status','TopPanel','Meter1','Meter2','MeterBack1','MeterBack2','Energy1','Energy2','Name1','Name2','Hp1','Hp2','HpBack1','HpBack2','Combo1','Combo2','State1','State2'})do rootNode(name):SetVisible(fighting)end
 for _,name in ipairs({'Light','Heavy','Jump','Block','Skill','Ultimate','StickBase'})do rootNode(name):SetVisible(fighting and not result and touch and not commandOpen)end
 for d=1,9 do rootNode('Stick'..d):SetVisible(fighting and not result and touch and not commandOpen)end
 rootNode('Help'):SetVisible(false);rootNode('MotionHelp'):SetVisible(false);rootNode('Restart'):SetVisible(false)
 rootNode('Stats'):SetVisible(fighting and debugPanel);rootNode('BootDiagnostic'):SetVisible(debugPanel);rootNode('DebugToggle'):SetVisible(fighting)
 rootNode('CommandToggle'):SetVisible(fighting);rootNode('ExitMatch'):SetVisible(fighting);rootNode('CommandScreen'):SetVisible(commandOpen)
 local r=roleChoice[seat>0 and seat or 1];local s=moveNames[r]
 rootNode('CommandTitle').text=roleNames[r]..' \194\183 \230\140\135\228\187\164\232\161\168'
 rootNode('CommandBody').text='A / D  \231\167\187\229\138\168     S  \232\185\178\228\188\143     \231\169\186\230\160\188  \232\183\179\232\183\131\nJ  \232\189\187\230\148\187\229\135\187     K  \233\135\141\230\148\187\229\135\187     L  \233\152\178\229\190\161\nS + J  \228\184\139\230\174\181     \229\137\141 + K  \228\184\138\230\174\181     S + K  \229\141\135\231\169\186\nE  '..s.special..'\nQ  '..s.super..' \194\183 100 \232\131\189\233\135\143\nH  \229\133\179\233\151\173\230\140\135\228\187\164\232\161\168 \194\183 \232\129\148\230\156\186\230\136\152\230\150\151\231\187\167\231\187\173\232\191\144\232\161\140'
 for n=1,3 do rootNode('SelectStage'..n):SetVisible(false);rootNode('Stage'..n):SetVisible(false)end
 rootNode('StageTitle'):SetVisible(fighting);rootNode('StageTitle').text=Collision.stageNames[Collision.stageId(stage,round)]
 rootNode('RoleKeqing'):SetVisible(false);rootNode('RoleDiluc'):SetVisible(false)
 for i=1,2 do
  actors[i]:SetVisible(fighting);rootNode('Shadow'..i):SetVisible(fighting)
  local role=selecting and previewChoice[i]or roleChoice[i];local portrait=rootNode('Portrait'..i);portrait:SetVisible((selecting and role>0)or fighting)
  portrait:SetAnchoredPosition(selecting and(i==1 and -165 or 165)or(i==1 and -608 or 608),selecting and 160 or 285);for _,part in ipairs(portrait:GetChildren())do if string.match(part.name,'^PortraitFrame')then part:SetVisible(fighting)end end;drawPortrait(i,role)
  rootNode('SelectName'..i).text=role>0 and roleNames[role]or'\233\128\137\229\174\154\232\167\146\232\137\178\229\144\142\229\177\149\231\164\186'
  rootNode('SelectReady'..i).text=menuReady[i]and'\233\152\181\229\174\185\229\183\178\233\148\129\229\174\154'or'\233\152\181\229\174\185\229\176\154\230\156\170\233\148\129\229\174\154'
  for n=1,3 do local chosen=teamChoice[i][n];rootNode('TeamName'..i..n).text=chosen>0 and roleNames[chosen]or'\229\190\133\233\128\137\232\167\146\232\137\178';plateColor('TeamSlot'..i..n..'Plate',chosen>0 and(i==1 and 0xff295a82 or 0xff8b3944)or 0xff2c3039)end
  for n=1,2 do rootNode('Win'..i..n):SetVisible(fighting and wins[i]>=n)end
 end
 for n=1,10 do local role=(rosterPage-1)*10+n;local valid=role<=9;rootNode('GridCard'..n):SetVisible(selecting and valid)
  if valid and selecting then
   local own=selected(1,role);local peer=selected(2,role)
   plateColor('GridPlate'..n,own and 0xff295a82 or(peer and 0xff8b3944 or 0xff40434b))
   rootNode('GridBlue'..n):SetVisible(own~=nil);rootNode('GridRed'..n):SetVisible(peer~=nil)
   gridNodes[n]=gridNodes[n]or{};if gridRoles[n]~=role then paintFrame(rootNode('GridFace'..n),'IconPx',thumbData[role],2.3*32/thumbData[role].w,gridNodes[n]);gridRoles[n]=role end
  end
 end
 rootNode('PageLabel').text=rosterPage..' / '..math.ceil(9/10)..'  \194\183  '..tostring(9)..' \228\189\141\232\167\146\232\137\178'
 local count=seat>0 and((teamChoice[seat][1]>0 and 1 or 0)+(teamChoice[seat][2]>0 and 1 or 0)+(teamChoice[seat][3]>0 and 1 or 0))or 0
 rootNode('SelectionHint').text=seat==0 and'\231\173\137\229\190\133\229\184\173\228\189\141\226\128\166'or('\228\189\160\230\152\175\231\142\169\229\174\182'..seat..' \194\183 \229\183\178\233\128\137 '..count..'/3 \194\183 \231\130\185\229\135\187\229\183\178\233\128\137\232\167\146\232\137\178\229\143\175\230\146\164\229\155\158')
 rootNode('ReadyConfirmText').text=seat>0 and menuReady[seat]and'\229\143\150\230\182\136\233\148\129\229\174\154'or(count==3 and'\233\148\129\229\174\154\228\184\137\228\186\186\233\152\181\229\174\185'or'\232\175\183\233\128\137\230\187\161\228\184\137\228\186\186')
 rootNode('ResultTitle').text=(wins[1]>=2 and'\231\142\169\229\174\1821'or'\231\142\169\229\174\1822')..'  \232\142\183\232\131\156';rootNode('ResultScore').text=wins[1]..' : '..wins[2]..' \194\183 \228\184\137\229\177\128\228\184\164\232\131\156'..((flowChoice[1]==1 or flowChoice[2]==1)and' \194\183 \231\173\137\229\190\133\229\143\140\230\150\185\229\134\141\230\136\152'or'')
end
local oldInit=OnInit
function OnInit()oldInit();menuDraw()end
function OnStart()
 menuStart()
 rootNode('Skill'):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()sendInput('skill')end)
 rootNode('Ultimate'):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()sendInput('ultimate')end)
 script:RegisterServerSignalHandler('GF10FramesOut',function(_,params)
  if not rb or tonumber(params[1])~=3-seat or tonumber(params[5])~=menuEpoch then return end
  receiveCount=receiveCount+1;debugNet.last='\230\148\182\229\136\176\232\190\147\229\133\165\230\137\185\230\172\161';if receiveCount==1 then print('[NET CLIENT] FramesOut RECEIVED')end;rb:receive(tonumber(params[2]),tonumber(params[3]),params[4])
 end)
 script:RegisterServerSignalHandler('GF10Joined',function(_,params)
  if not params or tonumber(params[1])~=menuEpoch then return end
  if onlineReady or (seat~=1 and seat~=2)or not menuReady[1] or not menuReady[2] or not menuLoaded[1] or not menuLoaded[2] or resourceGate.busy then return end
  debugNet.last='\230\148\182\229\136\176\229\188\128\230\136\152\233\128\154\231\159\165';print('[NET CLIENT] Joined RECEIVED');onlineReady=true;menuMode='battle';startNetworkRound();acc=0
  rb=NewRollbackSession({capture=capture,restore=restore,input=applyInput,step=step},seat)
 end)
 script:RegisterServerSignalHandler('GF10Seat',function(_,params)
  seatProbeCount=seatProbeCount+1
  local rawSlot=params and params[1]
  seatProbe='\229\184\173\228\189\141\229\155\158\232\176\131\230\172\161\230\149\176\239\188\154'..seatProbeCount..' | Slot='..tostring(rawSlot)
  print('[SEAT DEBUG] callback='..seatProbeCount..' Slot='..tostring(rawSlot))
  local assigned=tonumber(rawSlot);if assigned~=1 and assigned~=2 then
   seatProbe=seatProbe..' | \229\143\130\230\149\176\230\151\160\230\149\136';return
  end
  if onlineReady then return end
  seat=assigned;debugNet.last='\230\148\182\229\136\176\229\184\173\228\189\141 '..seat;print('[NET CLIENT] Seat RECEIVED '..seat)
  sendSelection()
 end)
 bind('KeyboardMoveLeftKeyDown',function()sendInput('left',1)end);bind('KeyboardMoveLeftKeyUp',function()sendInput('left',0)end)
 bind('KeyboardMoveRightKeyDown',function()sendInput('right',1)end);bind('KeyboardMoveRightKeyUp',function()sendInput('right',0)end)
 bind('KeyboardJumpKeyDown',function()sendInput('jump')end)
 bind('KeyboardMoveBackwardKeyDown',function()sendInput('down',1)end);bind('KeyboardMoveBackwardKeyUp',function()sendInput('down',0)end)
 bind('KeyboardCraftspersonKey19Down',function()sendInput('light',1)end);bind('KeyboardCraftspersonKey19Up',function()sendInput('light',0)end)
 bind('KeyboardCraftspersonKey20Down',function()sendInput('heavy',1)end);bind('KeyboardCraftspersonKey20Up',function()sendInput('heavy',0)end)
 bind('KeyboardCraftspersonKey21Down',function()sendInput('block',1)end);bind('KeyboardCraftspersonKey21Up',function()sendInput('block',0)end)
 bind('KeyboardCharacterSkill1KeyDown',function()sendInput('skill')end)
 bind('KeyboardCharacterSkill2KeyDown',function()sendInput('ultimate')end)
 bind('KeyboardCraftspersonKey15Down',function()commandOpen=not commandOpen;menuDirty=true end)
 bind('KeyboardCharacterSkill3KeyDown',function()sendInput('restart')end)
 for _,entry in ipairs({{'Left','left'},{'Right','right'},{'Down','down'},{'Block','block'}})do
  local c,k=root:FindChild(entry[1]),entry[2]
  c:AddCursorEventListener(Enum.CursorEventType.CursorDown,function()sendInput(k,1)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorUp,function()sendInput(k,0)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorExit,function()sendInput(k,0)end)
 end
 for _,entry in ipairs({{'Light',function()sendInput('clickLight')end},{'Heavy',function()sendInput('clickHeavy')end},{'Jump',function()sendInput('jump')end},{'Restart',function()sendInput('restart')end}})do root:FindChild(entry[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,entry[2])end

 for _,e in ipairs({{'RoleKeqing',1},{'RoleDiluc',2}})do root:FindChild(e[1]):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()chooseRole(e[2])end)end
 for n=1,3 do root:FindChild('SelectStage'..n):AddCursorEventListener(Enum.CursorEventType.CursorClick,function()chooseStage(n)end)end

 local stickHeld=false
 local function stick(d)
  local x=(d==1 or d==4 or d==7) and -1 or ((d==3 or d==6 or d==9) and 1 or 0)
  local down=d<=3
  sendInput('stick',d)
 end
 for d=1,9 do local c=root:FindChild('Stick'..d)
  c:AddCursorEventListener(Enum.CursorEventType.CursorDown,function()stickHeld=true;stick(d)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorEnter,function()if stickHeld then stick(d)end end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorUp,function()stickHeld=false;stick(5)end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorDrag,function(event)
   local x,y=event:GetUIPos();local px,py=event:GetPressUIPos()
   local dx=x-px+((d-1)%3-1)*48;local dy=y-py+(math.floor((d-1)/3)-1)*48
   local sx=dx>20 and 1 or (dx< -20 and -1 or 0);local sy=dy>20 and 1 or (dy< -20 and -1 or 0)
   stick(5+sx+sy*3)
  end)
  c:AddCursorEventListener(Enum.CursorEventType.CursorEndDrag,function()stickHeld=false;stick(5)end)
 end

 script:EnableUpdate(true)
 helloRequest()
end
local lastDrawPhase,lastDrawRound,lastDrawScore
local resendTime=0
function OnUpdate(dt)
 if resourceGate.busy then menuTime=menuTime+dt;return end
 menuTime=menuTime+dt
 visualUpdates=visualUpdates+1
 handshakeTime=handshakeTime+dt
 debugNet.updates=debugNet.updates+1
 if handshakeTime>=1 then
  retryFlow()
  visualRate=visualUpdates/handshakeTime;visualLastWrites=visualWrites;visualLastChanges=visualChanges
  visualUpdates=0;visualWrites=0;visualChanges=0
  handshakeTime=0
  if not onlineReady then
   if seat==0 then helloRequest()else sendSelection();if seat==2 and menuReady[1] and menuReady[2] and menuLoaded[1] and menuLoaded[2] and not resourceGate.busy then joinRequest()end end
  end
  local label=root:FindChild('BootDiagnostic')
  local state=not onlineReady and (seat==0 and '\231\173\137\229\190\133\229\184\173\228\189\141\229\155\158\229\140\133' or (seat==1 and '\229\183\178\231\153\187\232\174\176\239\188\140\231\173\137\229\190\133\229\143\166\228\184\128\228\186\186/\229\188\128\230\136\152' or '\231\173\137\229\190\133\229\188\128\230\136\152\229\155\158\229\140\133')) or (rb.error and ('\233\148\153\232\175\175 '..rb.error)or (rb.stalled and '\231\173\137\229\190\133\232\191\156\231\171\175\232\190\147\229\133\165' or '\230\136\152\230\150\151\232\191\144\232\161\140'))
  if label then label.text='DEBUG / Lua \229\183\178\229\144\175\229\138\168 \194\183 \230\155\180\230\150\176\230\172\161\230\149\176 '..debugNet.updates..'\n'..state..' | \229\184\173\228\189\141 '..seat..'\nHello \232\176\131\231\148\168 '..helloCount..' | Join \232\176\131\231\148\168 '..joinCount..'\n\232\190\147\229\133\165\229\143\145\233\128\129 '..debugNet.tx..' | \230\148\182\229\136\176 '..receiveCount..' | \230\137\185\230\172\161\229\173\151\232\138\130 '..debugNet.bytes..'\n\231\189\145\231\187\156\229\184\167 '..(rb and rb.frame or 0)..' | \232\191\156\231\171\175\231\161\174\232\174\164 '..(rb and rb.confirmed or 0)..' | \229\175\185\230\150\185\231\161\174\232\174\164 '..(rb and rb.peerAck or 0)..'\n\229\155\158\230\187\154 '..(rb and rb.rollbacks or 0)..' | \233\135\141\231\174\151\229\184\167 '..(rb and rb.replayed or 0)..'\n\230\156\128\232\191\145\239\188\154'..'LuaHz '..string.format('%.1f',visualRate)..' | Pose '..visualLastChanges..' | Writes '..visualLastWrites..'\n'..seatProbe end
  if debugNet.previous~=state then debugNet.previous=state;print('[NET CLIENT] STATE '..state)end
 end
 if not onlineReady or not rb then
  menuDraw()
  if menuMode=='select' and seat==0 then
   rootNode('SelectionHint').text='GF10-ORIGINAL-TEXT-V5 | Hello='..helloCount..' | SeatRx='..seatProbeCount..' | Slot='..seat..'\nTX=GF10Hello / RX=GF10Seat'
  end
  return
 end
 replaying=true;rb:repair();replaying=false
 acc=math.min(acc+math.min(dt,.1),.1);local n=0
 while acc>=1/60 and n<6 do
  if not rb:advance()then acc=0;break end
  acc=acc-1/60;n=n+1
 end
 resendTime=resendTime+dt
 if resendTime>=.05 then resendTime=0;flushFrames()end
 draw();Collision.drawBoxes()
 if lastDrawPhase~=phase or lastDrawRound~=round or lastDrawScore~=wins[1]*3+wins[2]then menuDirty=true;lastDrawPhase=phase;lastDrawRound=round;lastDrawScore=wins[1]*3+wins[2]end
 rootNode('RoundBanner'):SetVisible(phase=='intro');rootNode('RoundBanner').text=roundIntro<=25 and'FIGHT'or({'ROUND 1','ROUND 2','ROUND 3'})[math.min(round,3)]
 stats.text=stats.text..' | \229\155\158\230\187\154 '..rb.rollbacks..' / \231\189\145\231\187\156\229\184\167 '..rb.frame
 if rb.error then status.text='\232\129\148\230\156\186\233\148\153\232\175\175\239\188\154'..rb.error
 elseif rb.stalled then status.text='\231\173\137\229\190\133\232\191\156\231\171\175\232\190\147\229\133\165 \194\183 \230\154\130\229\129\156\233\162\132\230\181\139'end
 menuDraw()
end

function OnDisable()
 if rb then for _,key in ipairs({'left','right','down','block','light','heavy'})do rb:queue(key,0)end;rb:queue('stick',5);flushFrames()end
end

local bootOK=false
local originalInit,originalStart,originalUpdate=OnInit,OnStart,OnUpdate
local function bootText(message)
 local control=script.object:FindChild('BootDiagnostic')
 if control then control.text=message;control:SetVisible(true)end
end
function OnInit()
 local ok,message=pcall(originalInit)
 bootOK=ok
 if ok then bootText('Lua \229\183\178\229\136\157\229\167\139\229\140\150')else bootText('INIT ERROR: '..tostring(message));print('[fighter boot] INIT ERROR '..tostring(message))end
end
function OnStart()
 if not bootOK then return end
 local ok,message=pcall(originalStart)
 bootOK=ok
 if ok then bootText('Lua \229\183\178\229\144\175\229\138\168 \194\183 \230\160\188\230\150\151\231\149\140\233\157\162\232\191\144\232\161\140\228\184\173')else bootText('START ERROR: '..tostring(message));print('[fighter boot] START ERROR '..tostring(message))end
end
function OnUpdate(dt)
 if not bootOK then return end
 local ok,message=pcall(originalUpdate,dt)
 if not ok then bootOK=false;bootText('UPDATE ERROR: '..tostring(message));print('[fighter boot] UPDATE ERROR '..tostring(message))end
end

-- Compressed tables expand only for this menu page / these two current-round fighters.
local loadedInit,loadedStart,loadedUpdate=OnInit,OnStart,OnUpdate
local loadingRoot,loadingOverlay,loadingBar,loadingLabel,loadingTrack,loadingSeed
local loadingState='wait'


local loadingQueue,loadingUnload,loadingInstances,loadingActive={},{},{},{}
local loadingDecode={}
local loadingDone,loadingTotal,loadingTarget,loadingFirst=0,0,'menu',true
local PIXEL_TEMPLATE_INDEX=1073742822
local loadingPrefabIndex=nil
resourceGate.loader={view=nil,prefetchKeep={},prefetchQueue={},metrics={},displayClock=0}
function resourceGate.backgroundPrepare()
 local loader=resourceGate.loader;local roles=resourceGate.prefetchRoles and resourceGate.prefetchRoles()or{0,0}
 local key=roles[1]..':'..roles[2]
 if loader.prefetchKey~=key then
  local previous=loader.prefetchKeep
  loader.prefetchKey=key;loader.prefetchKeep={};loader.prefetchQueue={}
  for _,role in ipairs(roles)do if role>0 then for _,frame in ipairs(spriteData[role])do
   if not loader.prefetchKeep[frame]then loader.prefetchKeep[frame]=true;if not frame.rows then loader.prefetchQueue[#loader.prefetchQueue+1]=frame end end
  end end end
  if resourceGate.mode=='menu'then for frame in pairs(previous)do if not loader.prefetchKeep[frame]then frame.rows=nil;frame.raw=nil;frame.decoder=nil;frame.workDone=0 end end end
 end
 
 local began=loader.clock and loader.clock()or nil
 for n=1,12 do
  local now=loader.clock and loader.clock()or nil;if n>1 and began and now and now-began>=.001 then break end
  local frame=loader.prefetchQueue[#loader.prefetchQueue];if not frame then break end
  frame.workDone=(frame.workDone or 0)+1;if unpackWork(frame)then table.remove(loader.prefetchQueue)end
 end
end
local function loadingNow()local ok,t=pcall(function()return os.clock()end);return ok and type(t)=='number'and t or nil end
resourceGate.loader.clock=loadingNow
local function loadingDraw(dt)
 resourceGate.loader.displayClock=resourceGate.loader.displayClock+dt
 local cw,ch=game.GetUICanvasSize()
 local resized=cw~=resourceGate.loader.canvasW or ch~=resourceGate.loader.canvasH
 if not resized and resourceGate.loader.displayClock<.1 then return end
 resourceGate.loader.displayClock=0
 local width=math.min(760,cw*.7);local y=-ch/2+135
 if resized then
  resourceGate.loader.canvasW=cw;resourceGate.loader.canvasH=ch;resourceGate.loader.barWidth=nil
  if resourceGate.loader.stats then resourceGate.loader.stats.layoutWrites=resourceGate.loader.stats.layoutWrites+4 end
  loadingTrack:SetAnchoredPosition(0,y);loadingTrack:SetSizeDelta(width,8)
  loadingLabel:SetAnchoredPosition(0,y-35);loadingLabel:SetSizeDelta(cw*.9,56)
 end
 local ratio=loadingTotal>0 and math.min(1,loadingDone/loadingTotal)or 1
 local filled=math.max(1,math.floor(width*ratio+.5))
 if filled~=resourceGate.loader.barWidth then
  if resourceGate.loader.stats then resourceGate.loader.stats.progressWrites=resourceGate.loader.stats.progressWrites+2 end
  resourceGate.loader.barWidth=filled
  loadingBar:SetSizeDelta(filled,8);loadingBar:SetAnchoredPosition(-width/2+filled/2,y)
 end
end
resourceGate.waitingForBattle=function()return menuMode=='roundload' or menuMode=='waitingRound'end
resourceGate.loader.coverVisible=nil
resourceGate.loader.fail=function(message)
 loadingState='error'
 local panel=loadingRoot:FindChild('RuntimeError')
 for _,node in ipairs(loadingRoot:GetChildren())do node:SetVisible(node==panel)end
 local cw,ch=game.GetUICanvasSize();panel:SetSizeDelta(cw*.9,ch*.8);panel:SetAnchoredPosition(0,0)
 panel.text='ORIGINAL-TEXT-V5 / Lua error\n'..tostring(message)..'\nB index='..PIXEL_TEMPLATE_INDEX..' / target='..loadingTarget..' / tasks='..loadingDone..'/'..loadingTotal
 panel:SetVisible(true);print('[RESOURCE ERROR] '..tostring(message))
end
resourceGate.loader.syncCover=function()
 local backing=loadingRoot:FindChild('FullscreenBacking')
 if backing then backing:SetVisible(loadingState=='ready' and not resourceGate.waitingForBattle())end
 local waiting=loadingState=='ready' and resourceGate.waitingForBattle()
 local show=loadingState~='ready' or waiting
 if show~=resourceGate.loader.coverVisible then
  resourceGate.loader.coverVisible=show;loadingOverlay:SetVisible(show)
  if show then loadingOverlay:SetAsLastSibling()end
 end
 if waiting and not resourceGate.loader.wasWaiting then loadingOverlay:FindChild('LoadingBlack'):SetVisible(true);resourceGate.loader.displayClock=.1;loadingDraw(0)end
 resourceGate.loader.wasWaiting=waiting
end
local function loadingRequest(mode,choices)
 if resourceGate.busy and loadingState~='wait'then resourceGate.pending={mode,{choices[1],choices[2]}};return end
 resourceGate.loader.stats={created=0,destroyed=0,hidden=0,reused=0,decoded=0,updates=0,painted=0,phaseCpu={},phaseTasks={},wallSeconds=0,progressWrites=0,layoutWrites=0};resourceGate.loader.stagePaint=nil;loadingTarget=mode;resourceGate.busy=true;loadingState='paint';loadingDone=0;loadingTotal=0;loadingQueue={};loadingUnload={};loadingDecode={}
 local previews,page={0,0},1;if resourceGate.menuRoles then previews,page=resourceGate.menuRoles()end
 local desired,seen={},{}
 local showHome=mode=='menu'and resourceGate.showHome and resourceGate.showHome()
 local view=showHome and'home'or mode=='battle'and'battle'or'select';resourceGate.loader.targetView=view
 local function want(frame)if frame and not frame.textArt then desired[frame]=true end end
 if showHome then for _,frame in ipairs(resourceGate.homePortraitData)do want(frame)end end
 if mode=='battle'and resourceGate.stageFrame then want(resourceGate.stageFrame())end
 if mode=='battle'then
  for i=1,2 do for _,frame in ipairs(spriteData[choices[i]])do want(frame)end;want(portraitData[choices[i]])end
  local teams=resourceGate.teamRoles and resourceGate.teamRoles()or{{},{}};for i=1,2 do for n=1,3 do local role=teams[i][n];if role and role>0 then want(thumbData[role])end end end
 elseif not showHome then
  for n=1,10 do want(thumbData[(page-1)*10+n])end
  for i=1,2 do if previews[i]>0 then want(portraitData[previews[i]])end end
 end
 local function visit(frame)
  if frame.textArt then return end
  if seen[frame]then return end;seen[frame]=true
  if desired[frame]then if not frame.rows or frame.decoder then loadingDecode[#loadingDecode+1]=frame;loadingTotal=loadingTotal+math.max(1,unpackCost(frame)-(frame.workDone or 0))end
  elseif not resourceGate.loader.prefetchKeep[frame]then frame.rows=nil;frame.raw=nil;frame.decoder=nil;frame.workDone=0 end
 end
 for _,frames in ipairs(spriteData)do for _,frame in ipairs(frames)do visit(frame)end end
 for _,frame in ipairs(resourceGate.homePortraitData)do visit(frame)end
 for _,frame in ipairs(Collision.stageData)do visit(frame)end
 for _,frames in ipairs({portraitData,thumbData})do for _,frame in ipairs(frames)do visit(frame)end end
 local caps={mode=='battle'and poolCaps[choices[1]]or 0,mode=='battle'and poolCaps[choices[2]]or 0};resourceGate.caps=caps
 for j,job in ipairs(loadingJobs)do
  local parent=loadingRoot;for _,name in ipairs(job.path)do parent=parent:FindChild(name)end
  local name=parent.name;local who=job.path[1]=='Keqing'and 1 or 2;local wanted=0
  if name=='CountryStage'then wanted=mode=='battle'and resourceGate.stageFrame().count or 0
  elseif string.match(name,'^BattleTeam%d%dFace$')then local p,n=string.match(name,'^BattleTeam(%d)(%d)Face$');local teams=resourceGate.teamRoles and resourceGate.teamRoles()or{{},{}};local role=teams[tonumber(p)][tonumber(n)]or 0;wanted=mode=='battle'and role>0 and thumbData[role].count or 0
  elseif name=='HomeBust1'or name=='HomeBust2'then wanted=showHome and job.count or 0
  elseif name=='Sprite'then wanted=caps[who]
  elseif name=='Phoenix'then wanted=mode=='battle'and choices[who]==2 and job.count or 0
  elseif name=='Portrait1'or name=='Portrait2'then local i=name=='Portrait1'and 1 or 2;local role=mode=='battle'and choices[i]or previews[i];wanted=role>0 and portraitData[role].count or 0
  elseif string.match(name,'^GridFace%d+$')then local n=tonumber(string.match(name,'%d+'));local role=(page-1)*10+n;wanted=mode=='menu'and not showHome and thumbData[role]and thumbData[role].count or 0
  end
  local old=loadingActive[j]or 0;loadingInstances[j]=loadingInstances[j]or{}
  for n=old+1,wanted do loadingQueue[#loadingQueue+1]={j,n,parent}end
  local retain=(mode=='battle'and(name=='Sprite'or name=='Phoenix'or name=='CountryStage'))or(mode=='menu'and not showHome and(string.match(name,'^GridFace')or name=='Portrait1'or name=='Portrait2'))
  for n=wanted+1,old do loadingUnload[#loadingUnload+1]={j,n,parent,retain}end
  resourceGate.loader.stats.reused=resourceGate.loader.stats.reused+math.min(old,wanted)
  loadingActive[j]=retain and math.max(old,wanted)or wanted
 end
 if mode=='battle'then local frame=resourceGate.stageFrame();local cw,ch=game.GetUICanvasSize();local scale=math.max(cw/frame.w,ch/frame.h);local c=resourceGate.textNodes(rootNode('CountryStage'));if c.frame~=frame or c.scale~=scale then resourceGate.loader.stagePaint={frame=frame,n=1,scale=scale,key='1:'..cw..':'..ch};Collision.stageNodes={};loadingTotal=loadingTotal+math.ceil(#frame.chunks/16)end end
 loadingTotal=loadingTotal+#loadingQueue+#loadingUnload
 local full=loadingFirst or view~=resourceGate.loader.view or mode=='battle'
 if full then for _,node in ipairs(loadingRoot:GetChildren())do if node.name~='LoadingScreen'and node.name~='LoadingPixelTemplate'and node.name~='FullscreenBacking'then node:SetVisible(false)end end end
 resourceGate.loader.displayClock=.1;resourceGate.loader.barWidth=nil;loadingLabel:SetVisible(false);resourceGate.loader.coverVisible=true;loadingRoot:FindChild('FullscreenBacking'):SetVisible(false);loadingOverlay:SetActive(true);loadingOverlay:SetVisible(true);loadingOverlay:FindChild('LoadingBlack'):SetVisible(full);loadingOverlay:SetAsLastSibling();loadingDraw(0)
 print('[RESOURCE] '..mode..' compressed tasks='..loadingTotal..' current sprite caps='..caps[1]..','..caps[2])
end
local function loadingWorkRaw()
 if #loadingDecode>0 then local frame=loadingDecode[#loadingDecode];local done=unpackWork(frame);frame.workDone=(frame.workDone or 0)+1;resourceGate.loader.stats.decoded=resourceGate.loader.stats.decoded+1;loadingDone=loadingDone+1;if done then table.remove(loadingDecode)end;return true end
 local item=table.remove(loadingUnload)
 if item then local j,n,parent=item[1],item[2],item[3];local name=loadingJobs[j].prefix..n;if item[4]then loadingRegistry[loadingKey(parent)][name]:SetVisible(false);resourceGate.loader.stats.hidden=resourceGate.loader.stats.hidden+1
  else loadingRegistry[loadingKey(parent)][name]=nil;game.DestroyClientUIControl(loadingInstances[j][n]);loadingInstances[j][n]=nil;resourceGate.loader.stats.destroyed=resourceGate.loader.stats.destroyed+1 end
 else
  item=table.remove(loadingQueue);if not item then
   local paint=resourceGate.loader.stagePaint
   if paint and paint.n<=#paint.frame.chunks then
    local parent=rootNode('CountryStage')
    for n=paint.n,math.min(#paint.frame.chunks,paint.n+15)do resourceGate.paintTextChunk(parent,paint.frame,paint.scale,n);resourceGate.loader.stats.painted=resourceGate.loader.stats.painted+1 end
    paint.n=paint.n+16;loadingDone=loadingDone+1;return true
   end
   if paint then Collision.stagePaintKey=paint.key;local c=resourceGate.textNodes(rootNode('CountryStage'));c.frame=paint.frame;c.scale=paint.scale end
   return false end
  local j,n,parent=item[1],item[2],item[3];local name=loadingJobs[j].prefix..n
  if not loadingPrefabIndex then loadingPrefabIndex=PIXEL_TEMPLATE_INDEX>0 and PIXEL_TEMPLATE_INDEX or loadingSeed.referencedPrefabIndex end
  local box=game.InstantiateClientUIControl(loadingPrefabIndex,parent);if not box then error('\230\151\160\230\179\149\229\136\155\229\187\186\229\155\190\229\133\131\239\188\154\232\175\183\230\163\128\230\159\165 B \230\168\161\230\157\191\231\180\162\229\188\149 '..tostring(loadingPrefabIndex))end
  if parent.name=='Portrait1'or parent.name=='Portrait2'then box:SetAsLastSibling()end
  local pixel=box:FindChild('Pixel');if not pixel then error('B \230\168\161\230\157\191\231\188\186\229\176\145 Pixel')end;pixel.name=name;pixel:SetVisible(false)
  local key=loadingKey(parent);loadingRegistry[key]=loadingRegistry[key]or{};loadingRegistry[key][name]=pixel;loadingInstances[j][n]=box;resourceGate.loader.stats.created=resourceGate.loader.stats.created+1
 end
 loadingDone=loadingDone+1;return true
end
local function loadingWork()
 local stats=resourceGate.loader.stats
 local phase=#loadingDecode>0 and 'decode' or(#loadingUnload>0 and 'recycle' or(#loadingQueue>0 and 'create' or 'paint'))
 local began=loadingNow();local worked=loadingWorkRaw();local ended=loadingNow()
 if worked then stats.phaseTasks[phase]=(stats.phaseTasks[phase]or 0)+1 end
 if began and ended then stats.phaseCpu[phase]=(stats.phaseCpu[phase]or 0)+math.max(0,ended-began)end
 return worked
end
function OnInit()
 loadingRoot=script.object;loadingRoot:FindChild('FullscreenBacking'):SetAsFirstSibling();loadingOverlay=loadingRoot:FindChild('LoadingScreen');loadingBar=loadingOverlay:FindChild('LoadingBar');loadingLabel=loadingOverlay:FindChild('LoadingText');loadingLabel:SetVisible(false);loadingTrack=loadingOverlay:FindChild('LoadingTrack');loadingSeed=loadingRoot:FindChild('LoadingPixelTemplate')
 resourceGate.request=loadingRequest;loadingRequest('menu',{1,2})
end
function OnStart()script:EnableUpdate(true)end
function OnUpdate(dt)
 local ok,message=pcall(function()
  if loadingState=='error' then return end
  if loadingState=='ready'then
   loadedUpdate(dt)
   if loadingState=='ready'then resourceGate.backgroundPrepare()end
   resourceGate.loader.syncCover();return
  end
  resourceGate.loader.stats.updates=resourceGate.loader.stats.updates+1
  resourceGate.loader.stats.wallSeconds=resourceGate.loader.stats.wallSeconds+math.max(0,dt)
  local updateBegan=loadingNow();loadingDraw(dt);if loadingState=='error'then return end
  if loadingState=='paint'then loadingState='create';return end
  local began=updateBegan;local device=game.GetDevice();local mobile=device==Enum.Device.Mobile or device==Enum.Device.MobileController
  local ceiling=#loadingDecode>0 and 128 or(#loadingUnload>0 and 128 or(mobile and 48 or 96))
  local loader=resourceGate.loader;loader.batchFactor=loader.batchFactor or 1
  -- Frame interval is a scheduling signal, not CPU/GPU time or measured power.
  if dt>.04 then loader.batchFactor=math.max(.125,loader.batchFactor*.75)
  elseif dt>0 and dt<.022 then loader.batchFactor=math.min(1,loader.batchFactor+.02)end
  local batch=math.max(1,math.floor(ceiling*loader.batchFactor));local budget=mobile and .002 or .004
  for n=1,batch do
   local now=loadingNow();if n>1 and began and now and now-began>=budget then break end
   if not loadingWork()then loadingState='complete';break end
  end
  resourceGate.loader.stats.lastBatch=batch;resourceGate.loader.stats.luaSoftBudget=budget
  if loadingState=='complete'then
   resourceGate.mode=loadingTarget;resourceGate.busy=false
   if loadingFirst then loadingFirst=false;loadedInit();loadedStart();local diagnostic=loadingRoot:FindChild('BootDiagnostic');if diagnostic and string.find(diagnostic.text,'ERROR')then error(diagnostic.text)end end
   if resourceGate.pending then local p=resourceGate.pending;resourceGate.pending=nil;loadingState='wait';loadingRequest(p[1],p[2]);return end
   if resourceGate.completed then resourceGate.completed(loadingTarget)end
   resourceGate.loader.view=resourceGate.loader.targetView;resourceGate.loader.metrics[#resourceGate.loader.metrics+1]=resourceGate.loader.stats
   local s=resourceGate.loader.stats;print('[LOAD METRIC] '..loadingTarget..' create='..s.created..' destroy='..s.destroyed..' reuse='..s.reused..' decode='..s.decoded..' updates='..s.updates)
   if #resourceGate.loader.metrics>32 then table.remove(resourceGate.loader.metrics,1)end
   loadingState='ready';resourceGate.loader.displayClock=.1;loadingDraw(0);menuDraw();resourceGate.loader.syncCover()
   local s=resourceGate.loader.stats
   for _,phase in ipairs({'decode','recycle','create','paint'})do print('[LOAD PHASE] '..phase..' tasks='..(s.phaseTasks[phase]or 0)..' cpu='..(s.phaseCpu[phase]or 0))end
   print('[LOAD SCHEDULE] wall='..s.wallSeconds..' progressWrites='..s.progressWrites..' layoutWrites='..s.layoutWrites..' batch='..(s.lastBatch or 0))
  end
 end)
 if not ok then resourceGate.loader.fail(message)end
end
