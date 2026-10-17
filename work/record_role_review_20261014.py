from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013'
entry='> 2026-10-14 三角色美术续作：用户明确继续未完成角色、允许重画、严格审查并找回历史提示词。已恢复48份提示词/方向资料；那维前冲返修、后撤新增，玛薇卡跳跃新增进入独立预览。钟离蹲伏重画仍偏离母版，已退回，主预览保留原候选及最新岩脊/喝茶。20拟合对象精确重建、45组637引用及本批76浏览器阶段检查通过；美术未全通过，正式战斗/真机未验。先读[严格审查与续作](docs/current/三角色动作严格审查与续作_20261014.md)，预览`outputs/three-role-basic-20261013/index.html`，提示词入口`outputs/role-design-reference-20261014/index.html`。仅恢复这三位的美术续作，不推断发布授权。\n\n'
f=R/'AI_START.md';s=f.read_text(encoding='utf8')
if not s.startswith('> 2026-10-14 三角色美术续作：'):f.write_text(entry+s,encoding='utf8')
f=R/'docs/current/V9_执行与验收台账_20261013.md';s=f.read_text(encoding='utf8')
entry='> 2026-10-14 用户恢复三角色美术续作：48份历史提示词与方向恢复；那维前冲4身体姿返修、后撤4姿新增，玛薇卡跳跃6姿新增；钟离蹲伏新稿头身未通过，退回并保留原主候选。当前13组67姿/7组34姿/25组145姿，20拟合对象重建、637引用及76浏览器阶段检查通过；人体/发尾惯性/接缝与用户美术验收仍待，正式战斗/真机未验。详见[严格审查与续作](三角色动作严格审查与续作_20261014.md)。\n\n'
if not s.startswith('> 2026-10-14 用户恢复三角色美术续作：'):f.write_text(entry+s,encoding='utf8')
for role,issues in [('neuvillette',['后撤发尾惯性方向需返修','前冲/后撤杖长、握点、体型和首尾接缝待用户美术验收']),('mavuika',['跳跃人体尺度、发尾跟随与落地回待机接缝待美术验收']),('zhongli',['蹲伏新稿头身偏离母版，未采用','旧源图按姿尺度和枪杆连续性仍需审查'])]:
 f=O/role/'current-status.json';d=json.loads(f.read_text(encoding='utf8'));d['unresolvedArtIssues']=issues;d['artAccepted']=False;f.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
f=O/'strict-review-20261014.json';d=json.loads(f.read_text(encoding='utf8'));d['adoptedPreviewBodies']=14;d['rejectedZhongliBodies']=6;d['activePreviewActions']=45;d['artReview']={'neuvillette':'candidate; backdash hair inertia and cane continuity unresolved','mavuika':'candidate; landing and anatomy still require review','zhongli':'redraw rejected, previous actions restored exactly'};f.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
