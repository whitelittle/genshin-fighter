from pathlib import Path
import json
p=Path('outputs/motion-production')
m=json.loads((p/'manifest.json').read_text(encoding='utf-8'))
plan=json.loads((p/'batch-plan.json').read_text(encoding='utf-8'))
plan.update(sample_status='playback_workflow_verified_art_revision_pending',normal_proportion='nahida_idle_comparison_only',weaponResearch='cancelled_by_latest_user')
for b in plan['batches']: b['status']='pending_after_sample_art_revision'
(p/'batch-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
for r in m['roles']:
    report={'role':[r['key'],r['name']],'states':{a:{'status':'playback_candidate','frames':s,'review':'visual_candidate_not_final'} for a,s in r['sequences'].items()},'intro':'discussion_pending','productionCombatChanged':False,'deviceVerified':False,'fullAnimationApproved':False}
    (p/(r['key']+'-checklist.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
page=p/'index.html'; s=page.read_text(encoding='utf-8')
if 'href="proportions.html"' not in s: s=s.replace('<a href="../action-probe/index.html">','<a href="proportions.html">正常比例对照</a><a href="../action-probe/index.html">')
page.write_text(s,encoding='utf-8')
for page in [Path('work/action-probe/index.html'),Path('outputs/action-probe/index.html')]:
    s=page.read_text(encoding='utf-8')
    if '../motion-production/index.html' not in s: s=s.replace('<span class="badge">','<a href="../motion-production/index.html">五角色动作制作与播放</a><span class="badge">')
    page.write_text(s,encoding='utf-8')
print('motion progress recorded')
