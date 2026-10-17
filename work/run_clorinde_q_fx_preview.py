from pathlib import Path
import sys,json
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'runtime/tools'))
import preview
preview.RuntimeClient.source=R/'outputs/clorinde-q-fx-20261014/release/genshin_fighter.lua'
# A project-local wrapper reuses the actual client and existing mock server.
preview.preview.HERE=R/'outputs/clorinde-q-fx-20261014/simulator'
preview.preview.HERE.mkdir(exist_ok=True)
html=(R/'runtime/tools/index.html').read_text(encoding='utf8')
html=html.replace('整理版 · 四角色全流程模拟器','V9 · 克洛琳德大招电光恢复检查').replace('整理版 · 四角色','V9 · 克洛琳德大招电光恢复')
html=html.replace('<option value="KeyboardAndMouse">','<option value="KeyboardAndMouse" selected>').replace('value="MobileWide" selected','value="MobileWide"')
html=html.replace('点击画面开始；战斗使用触屏方向与技能按钮','A/D移动 · J普攻 · K重攻 · E战技 · W跳跃 · P菜单；训练陪练站立')
# Two immediate distance presets and a J2 diagnostic let the user inspect the gun
# without having to land J1 first. These are local preview controls, not game bindings.
html=html.replace('<button id="restart">重启</button>', '<button id="restart">重启</button><button data-test="near">近距离</button><button data-test="mid">中距离</button><button data-test="far">远距离</button><button data-test="j1">J1剑击</button><button data-test="j2">J2射击</button><button data-test="j3">J3剑击</button>')
html=html.replace('</style>','#bar{box-sizing:border-box;height:auto;min-height:88px;flex-wrap:wrap;gap:6px;align-content:center;padding:8px}#bar b{width:100%;font-size:12px}#bar button,#bar select{flex:0 0 auto;white-space:nowrap}#keys,#stats{display:none}#wrap{bottom:145px}</style>')
html=html.replace('const cv =', "document.querySelectorAll('[data-test]').forEach(b=>b.onclick=()=>fetch('/probe?mode='+b.dataset.test).then(()=>document.getElementById('cv').focus()));\nconst cv =")
(preview.preview.HERE/'index.html').write_text(html,encoding='utf8')
original=preview.preview.Handler.do_GET
def get(self):
 if self.path.startswith('/probe?mode='):
  mode=self.path.split('=',1)[1]
  with preview.preview.RUNNER.lock:
   c=preview.preview.RUNNER.client
   if mode in ['near','mid','far']:
    distance={'near':140,'mid':450,'far':850}[mode]
    c.lua(f"(function()local sc=GF_APP().scene;if not sc.sim then return false end;local s=sc.sim;local p,d=s.f[1],s.f[2];s.freeze=0;s.phase='fight';s:setState(p,'idle');s:setState(d,'idle');p.x={-distance*50};d.x={distance*50};p.y=0;d.y=0;p.face=1;d.face=-1;p.skillCd=0;p.energy=100;d.hp=d.maxhp;d.invul=0;return true end)()")
   elif mode in ['shot','j1','j2','j3']:
    move={'shot':'light2','j1':'light1','j2':'light2','j3':'light3'}[mode]
    c.lua(f"(function()local s=GF_APP().scene.sim;if not s then return false end;local p=s.f[1];p.airMove=nil;p.airMoveId=nil;s:setState(p,'idle');s:startMove(p,'{move}');return true end)()")
  return self.send(200,'ok')
 return original(self)
preview.preview.Handler.do_GET=get
sys.argv=['preview','--port','8791','--scene','fight','--device','KeyboardAndMouse','--canvas','1600x900','--args',json.dumps({'chars':['clorinde','clorinde'],'mode':'training','infinite':False,'stage':'mondstadt','cpu':[False,False],'seed':21})]
preview.preview.main()
