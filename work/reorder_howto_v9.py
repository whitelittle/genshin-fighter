from pathlib import Path
import re
R=Path(__file__).resolve().parents[1];p=R/'runtime/source/menu/gf_scene_howto.lua';s=p.read_text(encoding='utf8');O=R/'outputs/arlecchino-scale-layer-20261014/history';(O/'gf_scene_howto.lua').write_text(s,encoding='utf8')
block='''local function pagesFor(app)
 local dev=app.input:device()
 local mobile=dev=='touch';local pad=dev=='pad'
 local light=mobile and '轻按钮' or pad and '普攻键' or 'J'
 local heavy=mobile and '重按钮' or pad and '交互键' or 'K'
 local skill=mobile and 'E按钮' or pad and '技能1' or 'E'
 local burst=mobile and 'Q按钮' or pad and '技能2' or 'Q'
 return {
  {title='基础操作',lines={
   {'移动 / 跳跃',mobile and '摇杆移动；点跳按钮起跳' or pad and '左摇杆移动；跳跃键起跳' or 'A / D 左右；W或空格跳跃；S蹲下'},
   {'防御','按住远离对手的方向；后下为蹲防'},
   {'轻攻击',light..' · 可接后续轻攻；蹲下可出蹲轻'},
   {'重攻击',heavy..' · 角色重攻；蹲下可出蹲重'},
   {'元素战技',skill..' · 冷却结束后发动'},
   {'元素爆发',burst..' · 能量满时发动'},
   {'冲刺',mobile and '冲按钮；按住后方向可后撤' or pad and '冲刺键；按住后方向可后撤' or 'U；后方向＋U为后撤'},
   {'投技',mobile and '近身前方向＋重按钮' or pad and '近身前方向＋交互键' or 'L；需近身且目标可投'},
  }},
  {title='连段规则',lines={
   {'轻攻连段','连续轻攻可接下一段，招式随角色不同'},
   {'取消窗口','命中或被防后，在允许窗口接后续招式'},
   {'技能衔接','战技 / 爆发需满足资源与当前动作条件'},
   {'空中招式','起跳后可出空轻 / 空重，动作随角色不同'},
   {'伤害递减','同一连段越长，后续伤害越低'},
   {'练习入口','主菜单进入训练，分别选择自己与陪练'},
  }},
  {title='元素技能',lines={
   {'元素战技',skill..' · 有冷却，效果与范围随角色不同'},
   {'元素爆发',burst..' · 需要满能量；发动时消耗能量'},
   {'命中确认','满足首击命中条件后，进入完整爆发演出'},
   {'未命中','取消后续演出并收招，已消耗能量不退回'},
   {'被防住','按对应角色的防御分支处理'},
   {'命中限制','距离、朝向、有效时间与对手无敌状态都会影响命中'},
   {'状态限制','受击 / 倒地 / 不允许取消时，按键不代表成功发动'},
  }},
  {title='进阶操作',lines={
   {'战技备用',mobile and '使用E按钮；方向指令放在后续招式教学' or pad and '使用技能1；方向指令为进阶输入' or 'I也可发动战技；默认主键为E'},
   {'爆发备用',mobile and '使用Q按钮' or pad and '使用技能2' or 'O也可发动爆发；默认主键为Q'},
   {'方向指令','↓↘→＋攻击为进阶战技输入'},
   {'近身投技','前方向＋重攻；对手状态不允许时会落空'},
   {'打开菜单',mobile and '点画面上方菜单按钮' or pad and '平台技能3键打开战斗菜单' or 'P打开战斗菜单'},
   {'连段示例','实际能否衔接取决于角色、距离和取消窗口'},
  }},
 }
end
'''
s=re.sub(r'local PAGES = \{.*?\n\}\n',lambda m:block,s,count=1,flags=re.S)
s=s.replace('self.L = G.layer(app.layers.ui)','self.L = G.layer(app.layers.ui)\n    self.pages=pagesFor(app);self.device=app.input:device()')
s=s.replace('self.pt = self.pt + 1 / 60','self.pt = self.pt + 1 / 60\n    if self.device~=app.input:device() then self.device=app.input:device();self.pages=pagesFor(app) end')
s=s.replace('#PAGES','#self.pages').replace('ipairs(PAGES)','ipairs(self.pages)').replace('PAGES[self.page]','self.pages[self.page]')
s=s.replace("local EN = {'CONTROLS', 'COMBOS', 'BURSTS'}","local EN = {'CONTROLS', 'COMBOS', 'SKILLS', 'ADVANCED'}")
s=s.replace("-W / 2 + 820 + (i - 1) * 230","-W / 2 + 480 + (i - 1) * 280")
p.write_text(s,encoding='utf8');print('howto four device-specific pages')
