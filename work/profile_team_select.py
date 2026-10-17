import sys
sys.path.insert(0,'runtime/tests')
from mock_flow import RuntimeClient
c=RuntimeClient();c.env.GF_FIRST_SCENE='select';c.env.GF_FIRST_ARGS=c.rt.eval('{teamPreview=true,demo=true}')
while c.frame<459:c.step()
c.env.PROFILE=lambda tag: print(tag,c.H.instr)
c.lua('''(function()
local app=GF_APP();local old=app.backdrop
app.backdrop=function(...) PROFILE('bd before');local r=old(...);PROFILE('bd after');return r end
local B=GF_REQUIRE('gf_scene_select');local bind=B.bindAreas
B.bindAreas=function(...) PROFILE('areas before');local r=bind(...);PROFILE('areas after');return r end
local G=GF_REQUIRE('gf_gfx');for _,k in ipairs({'layer','group'}) do local fn=G[k];G[k]=function(...) PROFILE(k..' before');local r=fn(...);PROFILE(k..' after');return r end end
return true end)()''')
for _ in range(12):
 c.step();print(c.frame,c.lua("GF_APP().scene and tostring(GF_APP().scene.initialized)..':'..tostring(GF_APP().scene.frameN)..':'..tostring(GF_APP().scene.initFrames) or 'none'"))
print(c.heavy)
