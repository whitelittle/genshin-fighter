__loaders['gf_training_courses']=function()
return {
 main={
  {id='movement',label='基础移动',available=true,desc='前走、后退、跳跃落地、前冲、后撤。',status='可练习 · 5个目标'},
  {id='attack',label='普通攻击',available=true,desc='距离、轻击、三段普攻、重击、打空收招。命中后再按下一段，长按不会自动连段。',status='可练习 · 5个目标 · 三段与重击'},
  {id='low',label='下段攻击',available=true,desc='蹲轻、蹲重分别练，检查攻击高度和收招。',status='可练习 · 蹲轻与蹲重'},
  {id='air',label='空中攻击',available=true,desc='起跳后练空轻、空重，再观察落地恢复。',status='可练习 · 空轻与空重'},
  {id='launcher',label='挑空与追跳',available=true,desc='命中确认、蹲重挑空、向前跳跃取消、空轻接空重；最后练完整五击路线。',status='可练习 · 4个目标 · 自己输入追跳'},
  {id='guard',label='防御与反击',available=true,desc='站防、蹲防、退开躲招、趁收招轻击反击。先看丘丘王的举拳或压低蓄力，受击可重试。',status='可练习 · 4个目标 · 蓄力预警'},
  {id='skill',label='元素战技 E',available=true,desc='普通E、上E、下E各自练习，再认识共享冷却。',status='可练习 · 上中下E与共享冷却'},
  {id='burst',label='元素爆发',available=true,desc='先看能量，再练释放及命中、打空、被防的区别。',status='可练习 · 能量、命中、打空、被防'},
  {id='assist',label='支援协击',available=true,desc='空入场协击并退场，练呼叫、命中、冷却和打空。',status='可练习 · 空的专属支援动作'},
  {id='side',label='换边与自动转身',available=true,desc='向右跳过、向左跳回，最后在右侧使用新的后方向防御。',status='可练习 · 3个目标'},
  {id='elements',label='七元素与反应',desc='分别选择风、岩、雷、草、水、火、冰课程。',status='进入七元素课程目录'},
  {id='throw',label='投技与拆投',available=true,desc='先练近身投，再练抓住后的拆投，最后认识投空风险。',status='可练习 · 投技、12拍拆投、投空'},
 },
 elements={
  {id='anemo',available=true,status='可练习 · 预挂元素与指定战技',label='风元素',desc='认识扩散：先有可扩散附着，再用风攻击触发。'},
  {id='geo',available=true,status='可练习 · 预挂元素与指定战技',label='岩元素',desc='认识结晶与护盾，观察触发条件及护盾消耗。'},
  {id='electro',available=true,status='可练习 · 预挂元素与指定战技',label='雷元素',desc='分别练感电、超载、超导及与草的配合。'},
  {id='dendro',available=true,status='可练习 · 预挂元素与指定战技',label='草元素',desc='分别练绽放、激化、燃烧，控制场上持续对象数量。'},
  {id='hydro',available=true,status='可练习 · 预挂元素与指定战技',label='水元素',desc='分别练蒸发、冻结、感电和绽放的配合。'},
  {id='pyro',available=true,status='可练习 · 预挂元素与指定战技',label='火元素',desc='分别练蒸发、融化、超载和燃烧。'},
  {id='cryo',available=true,status='可练习 · 预挂元素与指定战技',label='冰元素',desc='分别练冻结、融化、超导。'},
 },
}
end
