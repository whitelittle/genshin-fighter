-- Offline evidence export only; never loaded by the production client.
local A=GF_REQUIRE('gf_art');local View=GF_REQUIRE('gf_fview')
local function json(v)
 local t=type(v)
 if t=='number' then return tostring(v) elseif t=='string' then return string.format('%q',v) elseif t=='boolean' then return tostring(v) elseif t=='nil' then return 'null' end
 local out={};local array=#v>0
 if array then for _,x in ipairs(v)do out[#out+1]=json(x)end;return '['..table.concat(out,',')..']' end
 for k,x in pairs(v)do out[#out+1]=json(tostring(k))..':'..json(x)end;table.sort(out);return '{'..table.concat(out,',')..'}'
end
local data={}
for _,key in ipairs({'raidenshogun','nahida'})do
 data[key]={}
 local names=key=='raidenshogun' and {'idle_0','idle_1','basic_2','basic_3','basic_4','basic_5','basic_6','basic_7'} or {'basic_0','basic_1','basic_2','basic_3','basic_4','basic_5','basic_6','basic_7'}
 for _,pose in ipairs(names)do local img=View.image({key=key,tier='lo'},pose);assert(img,'missing '..pose)
 if not img.bytes then local j=A.prepare(key,'lo');while not j:step(9000)do end;img=A.pose(key,'lo',pose)end
 assert(img.bytes,'not decoded '..pose);data[key][pose]={w=img.w,h=img.h,ax=img.ax,ay=img.ay,u=img.u,n=img.n,ox=img.ox or 0,pal=img.pal,bytes=img.bytes}
 end
end
data.effects=GF_REQUIRE('gf_animation_effects')
local f=assert(io.open('V4/evidence/v3-accepted-sd.json','w'));f:write(json(data));f:close();print('Exported accepted V3 SD poses without changing client')
