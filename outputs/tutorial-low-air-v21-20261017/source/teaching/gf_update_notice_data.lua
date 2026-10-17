__loaders['gf_update_notice_data']=function()
-- Entries and grouping explicitly confirmed by the user for this combined update.
return {
 stage='游戏目前处于早期开发阶段，角色动作、玩法与表现仍会持续调整。',
 nextGoal='下一步目标：完成教学关设计，并推进角色重做。',
 updates={
  {date='2026-10-15',origin='V15',title='克洛琳德报错修复',detail='修复空中攻击落地后再射击可能报错、近距离射击漏伤害的问题。',confirmed=true,candidate=false,source='outputs/clorinde-shot-crash-fix-20261015/修复与复现说明.md'},
  {date='2026-10-15',origin='V15',title='报错后返回与退出',detail='报错页可重启返回标题或退出游戏；已用原始错误复现检查返回流程。',confirmed=true,candidate=false,source='outputs/clorinde-real-crash-recovery-20261015/原始错误与恢复测试.md'},
  {date='2026-10-14',origin='已确认',title='克洛琳德技能调整',detail='恢复大招电光与近身剑击范围，调整射击表现及接触判定，补充大招反馈与操作说明。',confirmed=true,candidate=false,source='docs/current/V9_反馈修复与待定设计分流_20261014.md'},
 },
}
end
