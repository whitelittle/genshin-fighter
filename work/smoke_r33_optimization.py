"""PC/touch mock-client walkthrough and measured pool growth for r33 candidates."""
from test_r33_optimization import ROOT, OUT
import json
from harness import Client

class ArchiveClient(Client):
    def _build_tree(self):
        super()._build_tree()
        self.rt.execute('''
local H=...
H.game.InstantiateClientUIControl=function(index,parent)
 return H.newControl('image','dynamic',parent,nil)
end
''', self.H)

def run(label, device):
    c=ArchiveClient(script=OUT/f'GF_r33_opt_{label}.lua',build=False,
                    device=device,pools={'img':256,'txt':160,'btn':24})
    for _ in range(1400):
        c.step()
        if c.lua("GF_APP() and GF_APP().sceneName=='intro' and not GF_APP().poolNext"):
            break
    c.lua("(function() GF_APP():go('fight',{chars={'raidenshogun','nahida'},mode='versus',rounds=2,time=99,seed=73});return true end)()")
    for _ in range(1800):
        c.step()
        if c.lua("GF_APP().sceneName=='fight' and GF_APP().scene.state=='run'"): break
    assert c.lua("GF_APP().sceneName=='fight' and GF_APP().scene.state=='run'")
    load_frames=c.frame
    c.run(3)
    x0=c.lua('GF_APP().scene.sim.f[1].x')
    if device=='Mobile':
        from test_touch import to_canvas, button
        assert c.lua('GF_APP().scene.touch~=nil')
        sx,sy=to_canvas(c,-c.lua('GF_APP().W')/2+260,-c.lua('GF_APP().H')/2+200)
        c.touch('down',sx,sy,1);c.touch('drag',sx+90,sy,1);c.run(0.6)
        assert c.lua('GF_APP().scene.sim.f[1].x')>x0
        lx,ly=to_canvas(c,*button(c,'LP'))
        c.touch('down',lx,ly,2);c.step();c.step()
        assert c.lua('GF_APP().scene.sim.f[1].state')=='attack'
        c.touch('up',lx,ly,2);c.touch('up',sx+90,sy,1)
    else:
        c.key('D',True);c.run(0.6);c.key('D',False)
        assert c.lua('GF_APP().scene.sim.f[1].x')>x0
        c.press('J');c.run(1)
    # Measure manager growth independently of draw allocation/emergency fallback.
    growth=c.lua("""(function()
 local G=GF_REQUIRE('gf_gfx');local before=G.counts.img
 G.requestImages(before+100);G.manageImagePool('fight',false)
 return G.counts.img-before
end)()""")
    assert growth==(2 if label=='B' else 64), growth
    return {'device':device,'load_and_boot_updates':load_frames,'max_host_instructions':c.max_instr,
            'pool_manager_growth':growth,'scene':c.lua('GF_APP().sceneName'),
            'touch_present':bool(c.lua('GF_APP().scene.touch~=nil')),'stats':c.stats()}

if __name__=='__main__':
    result={}
    for label,device in [('A','KeyboardAndMouse'),('B','Mobile')]:
        result[label]=run(label,device)
        print(label,json.dumps(result[label]),flush=True)
    (OUT/'smoke-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
