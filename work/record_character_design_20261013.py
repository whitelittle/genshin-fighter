from pathlib import Path
import re,json,hashlib
R=Path(__file__).resolve().parents[1]
entries={
'AI_START.md':'> 2026-10-13 设计备选：用户认可加强角色区分度，允许特殊闪避与双攻击模组，并加入那维莱特、钟离、玛薇卡。已记录[九角色个人特色v0.1](docs/current/九角色个人特色技能设计备选_20261013.md)，仅设计，未改稳定版。用户明确动作核验交另一对话，本对话[只记录尺度跳变及分工](docs/current/动作尺度跳变反馈与跨对话分工_20261013.md)；站立/移动/受击大小仍不一致，不能标为已修复。',
'docs/current/README.md':'> 2026-10-13 最新设计：[九角色个人特色技能备选](九角色个人特色技能设计备选_20261013.md)，含无敌阶段、双模组、伙伴、标记、岩脊与骑乘方案，数值后调。当前仍六人稳定版，未实现九人。动作核验与尺寸修复由另一对话负责，本对话[仅记录反馈](动作尺度跳变反馈与跨对话分工_20261013.md)。',
'docs/current/问题台账.md':'> 2026-10-13 P1未修复：匿名玩家确认人物站立、移动、受击之间仍有身体大小跳变，明确不是镜头问题。动作核验与修复由另一对话负责，本对话仅登记，[交接记录](动作尺度跳变反馈与跨对话分工_20261013.md)。此前统一渲染倍率不代表统一人体实际尺度。',
'docs/current/V4_执行与验收台账_20261009.md':'> 2026-10-13 设计：记录九角色个人特色技能v0.1，现六人加那维莱特/钟离/玛薇卡，参考原作、允许特殊闪避和双模组，数值后调；未改代码/素材/稳定归档。动作尺寸跳变仍待修，用户指定另一对话核验，本对话只记录。详见[设计备选](九角色个人特色技能设计备选_20261013.md)与[分工](动作尺度跳变反馈与跨对话分工_20261013.md)。',
'docs/current/稳定版资料_20261013/README.md':'> 稳定归档后的新增备选（2026-10-13）：[九角色个人特色设计v0.1](../九角色个人特色技能设计备选_20261013.md)。未纳入冻结稳定版；[动作尺度跳变](../动作尺度跳变反馈与跨对话分工_20261013.md)由另一对话核验，本对话仅记录。',
'docs/current/后续模式与轮换角色需求_20261013.md':'> 2026-10-13 新增设计备选：[九角色个人特色技能](九角色个人特色技能设计备选_20261013.md)，用户要求将那维莱特、钟离、玛薇卡也纳入特色设计，仓库动作更新交另一对话核验。当前未接入三人，未扩稳定版名单；其余未来模式仍仅记录。'
}
for rel,entry in entries.items():
 p=R/rel
 p.write_text(entry+'\n\n'+p.read_text(encoding='utf-8-sig'),encoding='utf-8')
paths=[R/'docs/current/九角色个人特色技能设计备选_20261013.md',R/'docs/current/动作尺度跳变反馈与跨对话分工_20261013.md']
for p in paths:
 s=p.read_text(encoding='utf-8')
 assert not re.search(r'[A-Z]:[\\/]Users[\\/]|UID\s*[:：]\s*\d+',s)
 for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',s):
  if '://' not in link:assert (p.parent/link).exists(),link
archive=R/'outputs/archive/20261013_stable_gfv2_p6'
m=json.loads((archive/'manifest.json').read_text(encoding='utf-8'))
for f in m['files']:
 p=archive/f['path']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==f['sha256'],p
for p in (R/'runtime/source').rglob('*'):
 if p.is_file():assert p.read_bytes()==(archive/'runtime/source'/p.relative_to(R/'runtime/source')).read_bytes(),p
print('Design links/privacy passed; stable archive and runtime source unchanged; no action inspection or modification.')
