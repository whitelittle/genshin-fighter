__loaders['gf_kits'] = function()
local K = {}

K.en = {
    raidenshogun = 'RAIDEN SHOGUN', furina = 'FURINA', zhongli = 'ZHONGLI', mavuika = 'MAVUIKA', nahida = 'NAHIDA',
    venti = 'VENTI', kamisatoayaka = 'KAMISATO AYAKA', tartaglia = 'TARTAGLIA', aratakiitto = 'ARATAKI ITTO',
    yaemiko = 'YAE MIKO', arlecchino = 'ARLECCHINO', wanderer = 'WANDERER', neuvillette = 'NEUVILLETTE',
    clorinde = 'CLORINDE', navia = 'NAVIA', skirk = 'SKIRK',
}
K.title = {
    raidenshogun = '永恒的雷光', furina = '不休的独舞', zhongli = '尘世闲游', mavuika = '燃烧的太阳', nahida = '白草净华',
    venti = '风色诗人', kamisatoayaka = '白鹭霜华', tartaglia = '公子', aratakiitto = '花坂豪快', yaemiko = '浮世笑百姿',
    arlecchino = '「仆人」', wanderer = '久世浮倾', neuvillette = '谕告的潮音', clorinde = '秉烛狝影', navia = '明花蔓舵',
    skirk = '深渊的剑客',
}

require('gf_weapon_rules')(K)
require('gf_character_rules')(K)
require('gf_character_furina_rules')(K)
require('gf_character_ayaka_rules')(K)
require('gf_character_clorinde_rules')(K)
require('gf_character_arlecchino_rules')(K)
require('gf_element_rules')(K)
K.en.lumine='LUMINE';K.en.lawachurl='STONEHIDE LAWACHURL'
K.characterWeapons=K.characterWeapons or {}
require('gf_lumine_training_rules')(K)
K.characterWeapons.lawachurl={reach=1,light1={pose='slash',startup=54,active=5,recovery=110,damage=24,hitstun=18,blockstun=12,push=1,level='high',box={x=10,y=100,w=350,h=220},cancel={}},crouchHeavy={pose='slash',startup=60,active=5,recovery=74,damage=24,hitstun=18,blockstun=12,push=1,level='low',box={x=10,y=20,w=350,h=100},cancel={}}}
K.body.lawachurl={walk=3,back=2.5,dash=10,health=1500,weight=1.3}
return K
end
