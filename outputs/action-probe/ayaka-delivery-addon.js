(() => {
  'use strict';
  const role = window.PROBE_DATA?.roles?.find((item) => item.key === 'kamisatoayaka');
  if (!role) return;
  const root = '../v4-one-character-20261010/ayaka-full-animation-candidate/actions/';
  const latest = {
    idle: ['idle', '00'], walk1: ['walk', '00'], walk2: ['walk', '01'],
    crouch: ['crouch', '00'], guard: ['guard', '00'], crouchGuard: ['crouchguard', '00'],
    hurt: ['hurt_knockdown', '00'], airHurt: ['victim', '00'], down: ['defeat', '02'],
    jump: ['jump', '01'], slash: ['light1', '00'], special: ['E', '00'],
    qRelease: ['Q', '02'], qCharge: ['Q', '00'],
  };
  for (const pose of role.poses || []) {
    const ref = latest[pose.name];
    if (!ref) continue;
    pose.url = `${root}${ref[0]}/body-${ref[1]}.png`;
    pose.review = '20261010-ayaka-full-animation-candidate';
    pose.alias = false;
  }
  role.delivery = {
    status: 'visual_candidate_review_only', actionGroups: 25, frames: 110,
    fullViewer: '../v4-one-character-20261010/ayaka-full-animation-candidate/viewer.html',
    note: '全动作候选已挂入本角色入口；关键姿势显示使用原始拟合帧，不使用统一放大。完整帧序、特效和待验项在全动作候选包。',
  };
})();
