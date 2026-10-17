local Art=require('gf_art');local V=require('gf_fview')
local view=setmetatable({key='raidenshogun',tier='lo'},{__index=V})
local function array(t)local q={} for i=1,#t do if type(t[i])=='table' then q[i]=array(t[i]) else q[i]=tostring(t[i]) end end return '['..table.concat(q,',')..']' end
local out={}
for _,pose in ipairs({'idle_0','guard_2','guard_6','hurt_0'}) do
 local im=view:image(pose)
 out[#out+1]='"'..pose..'":{"w":'..im.w..',"h":'..im.h..',"ax":'..im.ax..',"ay":'..im.ay..',"ox":'..(im.ox or 0)..',"rectangles":'..im.n..',"palette":'..array(im.pal)..',"bytes":'..array(im.bytes)..'}'
end
local file=assert(io.open('dist/assets/v3-target-data.json','w'));file:write('{"character":"raidenshogun","poses":{'..table.concat(out,',')..'}}');file:close();print('Exported V3 loaded opponent data; CPU reconstruction only')
