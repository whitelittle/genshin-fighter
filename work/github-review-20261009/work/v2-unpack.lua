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
