__loaders['gf_training_courses']=function()
return {
 main={
  {id='movement',label='基础移动',available=true,desc='前走、后退、跳跃落地、前冲、后撤。',status='可练习 · 5个目标'},
  {id='attack',label='普通攻击',available=true,desc='先练距离与一次真实轻击；三段和重击随后补齐。',status='轻击入门可练 · 三段/重击待接'},
  {id='low',label='下段攻击',desc='蹲轻、蹲重分别练，检查攻击高度和收招。',status='待接入动作与命中规则'},
  {id='air',label='空中攻击',desc='起跳后练空轻、空重，再观察落地恢复。',status='待接入动作与落地规则'},
  {id='guard',label='防御与反击',available=true,desc='站防、蹲防、退开躲招、趁收招轻击反击。丘丘王按固定节奏出招，受击可重试。',status='可练习 · 4个目标 · 攻击动画暂代'},
  {id='skill',label='元素战技 E',desc='普通E、上E、下E各自练习，再认识共享冷却。',status='待接荧的三个战技分支'},
  {id='burst',label='元素爆发',desc='先看能量，再练释放及命中、打空、被防的区别。',status='待接入大招动作与规则'},
  {id='assist',label='支援协击',desc='认识独立协同位，练呼叫、真实协击和冷却。',status='已有协同原型 · 本关待接'},
  {id='elements',label='七元素与反应',desc='分别选择风、岩、雷、草、水、火、冰课程。',status='进入七元素课程目录'},
  {id='throw',label='投技与拆投',desc='先练近身投，再练抓住后的拆投，最后认识投空风险。',status='待接通用投、拆投及动作'},
 },
 elements={
  {id='anemo',label='风元素',desc='认识扩散：先有可扩散附着，再用风攻击触发。'},
  {id='geo',label='岩元素',desc='认识结晶与护盾，观察触发条件及护盾消耗。'},
  {id='electro',label='雷元素',desc='分别练感电、超载、超导及与草的配合。'},
  {id='dendro',label='草元素',desc='分别练绽放、激化、燃烧，控制场上持续对象数量。'},
  {id='hydro',label='水元素',desc='分别练蒸发、冻结、感电和绽放的配合。'},
  {id='pyro',label='火元素',desc='分别练蒸发、融化、超载和燃烧。'},
  {id='cryo',label='冰元素',desc='分别练冻结、融化、超导。'},
 },
}
end
