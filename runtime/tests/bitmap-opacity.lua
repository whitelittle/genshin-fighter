-- Native colour caching must preserve each source palette's alpha exactly.
local G=GF_REQUIRE('gf_gfx')
local b=G.bitmap({});local img={n=3,ax=0,ay=0,pal={{10,20,30,255},{10,20,30,128}},bytes={0,0,1,1,0,1,0,1,1,1,2,0,1,1,0}}
b:draw(img,'opacity-test')
local function expected(c,alpha)local a=math.floor(c[4]*alpha+.5);return ((c[1]*256+c[2])*256+c[3])*256+a end
for _,alpha in ipairs({0,.1,.45,1}) do
 b:opacity(img,alpha)
 for i=1,3 do assert(b.kids[i].ck==expected(img.pal[img.bytes[(i-1)*5+5]+1],alpha)) end
 local n=G.N.col;b:opacity(img,alpha);assert(G.N.col==n,'stable alpha rewrites colours')
end
b:tintRGBA(170,235,255,140);local n=G.N.col;b:tintRGBA(170,235,255,140);assert(G.N.col==n)
b:draw(img,'opacity-new-frame');b:opacity(img,1)
for i=1,3 do assert(b.kids[i].ck==expected(img.pal[img.bytes[(i-1)*5+5]+1],1)) end
b:free()
