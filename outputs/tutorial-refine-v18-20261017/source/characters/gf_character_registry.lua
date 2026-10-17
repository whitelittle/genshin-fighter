__loaders['gf_character_registry']=function()
-- Stable roster indices are also protocol IDs. Append; never sort by display name.
local R={definitions={
 {key='raidenshogun',name='雷电将军',element='electro',weapon='polearm',attack='源流',skill='神变·恶曜开眼',burst='奥义·梦想真说',h=336},
 {key='nahida',name='纳西妲',element='dendro',weapon='catalyst',attack='行相',skill='所闻遍计',burst='心景幻成',h=261},
 {key='furina',name='芙宁娜',element='hydro',weapon='sword',attack='独舞之邀',skill='孤心沙龙',burst='万众狂欢',h=335,candidate=true,provider='gf_character_furina'},
 {key='kamisatoayaka',name='神里绫华',element='cryo',weapon='sword',attack='神里流·倾',skill='神里流·冰华',burst='神里流·霜灭',h=335,candidate=true,provider='gf_character_ayaka'},
 {key='clorinde',name='克洛琳德',element='electro',weapon='sword',attack='逐影之誓',skill='狩夜之巡',burst='残光将终',h=335,candidate=true,provider='gf_character_clorinde'},
 {key='arlecchino',name='阿蕾奇诺',element='pyro',weapon='polearm',attack='斩首之邀',skill='万相化灰',burst='厄月将升',h=335,candidate=true,provider='gf_character_arlecchino'},
 {key='lumine',name='荧',element='anemo',weapon='sword',attack='轻击试作',skill='暂未开放',burst='暂未开放',h=335,provider='gf_character_lumine_training'},
 {key='lawachurl',name='岩盔丘丘王',element='geo',weapon='claymore',attack='教学陪练',skill='暂未开放',burst='暂未开放',h=440,provider='gf_character_lawachurl_training'},
},byKey={},providers={}}
for i,c in ipairs(R.definitions) do
 assert(not R.byKey[c.key],'duplicate character key')
 c.index=i;R.byKey[c.key]=c
end
function R.provider(key)
 local c=R.byKey[key]
 if not c or not c.provider then return nil end
 if not R.providers[key] then R.providers[key]=require(c.provider) end
 return R.providers[key]
end
return R
end
