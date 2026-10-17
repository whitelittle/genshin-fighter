__loaders['gf_element_rules']=function()
return function(K)
K.reactionName = {
    vaporize = '蒸发', melt = '融化', overload = '超载', frozen = '冻结', electro = '感电', superconduct = '超导',
    swirl = '扩散', crystal = '结晶', bloom = '绽放', aggravate = '激化', burning = '燃烧',
}
local R = {}
local function pair(a, b, r) R[a] = R[a] or {}; R[b] = R[b] or {}; R[a][b] = r; R[b][a] = r end
pair('hydro', 'pyro', 'vaporize')
pair('cryo', 'pyro', 'melt')
pair('electro', 'pyro', 'overload')
pair('hydro', 'cryo', 'frozen')
pair('electro', 'hydro', 'electro')
pair('electro', 'cryo', 'superconduct')
pair('dendro', 'hydro', 'bloom')
pair('dendro', 'electro', 'aggravate')
pair('dendro', 'pyro', 'burning')
for _, e in ipairs({'hydro', 'pyro', 'electro', 'cryo'}) do
    R.anemo = R.anemo or {}; R.anemo[e] = 'swirl'; R[e].anemo = 'swirl'
    R.geo = R.geo or {}; R.geo[e] = 'crystal'; R[e].geo = 'crystal'
end
K.reaction = R

K.elementColor = {
    anemo = {116, 255, 214}, geo = {255, 200, 64}, electro = {196, 120, 255}, dendro = {150, 230, 60},
    hydro = {60, 170, 255}, pyro = {255, 110, 50}, cryo = {160, 230, 255},
}
K.elementName = {anemo = '风', geo = '岩', electro = '雷', dendro = '草', hydro = '水', pyro = '火', cryo = '冰'}
K.weaponName = {sword = '单手剑', claymore = '双手剑', polearm = '长柄武器', catalyst = '法器', bow = '弓'}


end
end
