__loaders['gf_character_assets']=function()
local U=require('gf_util')
local M={}
-- Provider boundary: encoded storage can change without changing Art/FView callers.
function M.new(data)
 local P={data=data,bodyPeak=data.bodyPeak}
 local function commit(img,raw)
  local values=U.rectangleValues(img,raw)
  for i=1,img.n*5 do
   local v=values[i]
   local axis=i%5;values[i]=axis==0 and v or v*((axis==1 or axis==3) and (img.ux or img.u) or (img.uy or img.u))
  end
  img.bytes=values;img.ax=img.ax*(img.ux or img.u);img.ay=img.ay*(img.uy or img.u)
  img.w=img.w*(img.ux or img.u);img.h=img.h*(img.uy or img.u);img.seam=.08*img.u;img.u=1;img.baked=true
 end
 function P.image(pose)
  local id=data.aliases[pose] or pose
  local img=assert(data.frames[id],'missing character image: '..tostring(pose))
  if not img.bytes then commit(img,U.decodeImage(img)) end
  return img
 end
 function P.prepare()
  if GF_RAW_ASSET_TABLES and require('gf_gfx').mobileLightEffects then return {total=0,completed=0,step=function()return true end} end
  local names={}
  for id,img in pairs(data.frames) do if not img.bytes then names[#names+1]=id end end
  table.sort(names)
  local job={i=1,total=#names,completed=0}
  function job:step(budget)
   local id=names[self.i];if not id then return true end
   local img=data.frames[id]
   if img.raw then
    P.image(id);self.completed=self.i;self.i=self.i+1
    return self.i>self.total
   end
   -- Menu preview or another preparation job may have committed this image.
   if not img.bytes then
    self.decoder=self.decoder or U.imageDecoder(img)
    if not self.decoder:step(math.max(4,math.min(9000,budget or 9000))) then return false end
    commit(img,self.decoder.bytes)
   end
   self.decoder=nil;self.completed=self.i;self.i=self.i+1
   return self.i>self.total
  end
  return job
 end
 return P
end
return M
end
