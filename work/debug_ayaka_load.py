import sys
sys.path.insert(0,'runtime/tests')
from mock_flow import *
c=RuntimeClient();wait(c,"GF_APP() and GF_APP().sceneName=='intro' and not GF_APP().poolNext")
c.lua("(function()GF_APP():go('select',{mode='versus',cpu=true});return true end)()")
wait(c,"GF_APP().sceneName=='select' and GF_APP().scene.built==4 and not GF_APP().poolNext")
c.lua("(function()local s=GF_APP().scene;s.cur={4,3};s:confirm(1);s:confirm(2);return true end)()")
for i in range(2400):
 c.step()
 if i%400==0:print(i,c.lua('GF_APP().sceneName'),c.lua('GF_APP().scene.state'),c.lua('GF_APP().scene.loadStep'),c.lua('GF_APP().scene.warm'),flush=True)
print(c.logs[-10:] if hasattr(c,'logs') else c.lua('GF_APP().scene.state'))
