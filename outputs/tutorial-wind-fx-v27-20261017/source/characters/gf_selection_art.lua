__loaders['gf_selection_art']=function()
local Art=require('gf_art')
local D=require('gf_selection_candidates')
local A={roster={},byKey={}}
for i,c in ipairs(Art.roster) do A.roster[i]=c;A.byKey[c.key]=c end
for _,c in ipairs({
 {key='clorinde',name='克洛琳德',element='electro',weapon='sword',skill='狩夜之巡',burst='残光将终',selectionOnly=true},
 {key='arlecchino',name='阿蕾奇诺',element='pyro',weapon='polearm',skill='万相化灰',burst='厄月将升',selectionOnly=true},
}) do if not A.byKey[c.key] then c.index=#A.roster+1;A.roster[c.index]=c;A.byKey[c.key]=c end end
function A.face(key) return D[key] and D[key].face or Art.face(key) end
function A.pose(key,tier,pose) return D[key] and D[key].idle or Art.pose(key,tier,pose) end
return A
end
