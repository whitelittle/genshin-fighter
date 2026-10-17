from pathlib import Path
import json,re,hashlib,shutil
R=Path(__file__).resolve().parents[1];O=R/'outputs/three-role-basic-20261013';P=R/'outputs/role-design-reference-20261014';P.mkdir(exist_ok=True)
# Grounded anticipation and landing no longer float with the whole jump cycle.
f=O/'mavuika/player.js';s=f.read_text(encoding='utf8')
s=s.replace('if(active.motion.kind==="jump")root[1]-=active.motion.height*Math.sin(Math.PI*u);','if(active.motion.kind==="jump"){const air=active.motion.airPhases;if(air){const begin=active.durations.slice(0,air[0]).reduce((a,b)=>a+b,0),end=active.durations.slice(0,air[air.length-1]+1).reduce((a,b)=>a+b,0);if(time>=begin&&time<end)root[1]-=active.motion.height*Math.sin(Math.PI*(time-begin)/(end-begin));}else root[1]-=active.motion.height*Math.sin(Math.PI*u);}')
f.write_text(s,encoding='utf8')
for role in ['neuvillette','mavuika']:
 f=O/role/'player.js';s=f.read_text(encoding='utf8')
 wait='await load(bank.idle[material==="source"?"sourceFrames":"frames"][0].file)'
 if 'idleImage:'+wait in s:
  s=s.replace('if(v!==version)return;active=',f'const idleImage={wait};if(v!==version)return;active=')
  s=s.replace('idleImage:'+wait,'idleImage')
 s=re.sub(r"\$\('source'\)\.href=.*?;document.querySelectorAll",lambda m:"$('source').href=d.sourceFrames.find(f=>f.file.includes('strict-20261014'))?.source||d.sourceFrames.find(f=>f.source.includes('heavy'))?.source||d.sourceFrames[0].source;document.querySelectorAll",s)
 f.write_text(s,encoding='utf8')
 f=O/role/'player.html';s=f.read_text(encoding='utf8').replace('href="verification.json"','href="../strict-review-20261014.json"');
 if role=='mavuika':s=s.replace('href="制作与交付.md"','href="../../../docs/current/三角色动作严格审查与续作_20261014.md"')
 s=re.sub(r'src="(player|action-data|effect-data)\.js(?:\?[^\"]*)?"',r'src="\1.js?v=strict-20261014"',s)
 f.write_text(s,encoding='utf8')
f=O/'index.html';s=f.read_text(encoding='utf8').replace('那维莱特 · 12组 / 61姿','那维莱特 · 13组 / 67姿').replace('玛薇卡 · 6组 / 27姿','玛薇卡 · 7组 / 34姿')
s=s.replace('本批为美术与预览候选，正式战斗与真机另验。补间已纳入后续方案。','10月14日：那维前冲返修／后撤新增，玛薇卡跳跃新增；钟离蹲伏重画未通过，原候选保留。正式战斗与真机另验。')
s=s.replace('那维莱特并排图','那维莱特上批历史图').replace('玛薇卡并排图','玛薇卡上批历史图').replace('钟离并排图','钟离上批历史图')
s=s.replace('<a href="本批记录.md"','<a href="neuvillette/evidence/forwarddash-strict-20261014.png" target="_blank">本批前冲并排</a><a href="neuvillette/evidence/backdash-strict-20261014.png" target="_blank">本批后撤并排</a><a href="mavuika/evidence/jump-strict-20261014.png" target="_blank">本批跳跃并排</a><a href="本批记录.md"')
s=s.replace('<a href="本批记录.md"','<a href="../../docs/current/三角色动作严格审查与续作_20261014.md" target="_blank">本批审查与未完成项</a><a href="../role-design-reference-20261014/index.html" target="_blank">找回的提示词与方向</a><a href="本批记录.md"')
seen=set()
def unique_link(m):
 href=m[1]
 if href in seen:return ''
 seen.add(href);return m[0]
s=re.sub(r'<a href="([^\"]+)"[^>]*>.*?</a>',unique_link,s)
f.write_text(s,encoding='utf8')
sources=[]
for folder in [O/'neuvillette/prompts',O/'upstream/zhongli/prompts',O/'zhongli/prompts-review-20261014',O/'neuvillette/prompts-review-20261014',O/'mavuika/prompts-review-20261014']:
 sources.extend(p for p in folder.rglob('*') if p.is_file())
sources.extend([O/'zhongli/prompts.json',O/'upstream/zhongli/full-actions/prompts.json',O/'upstream/zhongli/batches/20261011-resume/prompts.json',O/'upstream/zhongli/batches/20261011-refinement/prompts.json',O/'zhongli/sources/victory-tea-v9-20261014.prompt.txt'])
mf=O/'upstream/mavuika-v10/production'
sources.extend(mf/name for name in ['neutral-prompts-v5.json','prompts-v6.json','light1-correction-prompt-v6.txt','light1-fx-prompt-v7.txt','image-prompts.md','RESUME_20261012_ORIGIN_V10.md','RESUME_20261012_LAYER_V9.md'])
sources.append(O/'neuvillette/动作设计卡.md')
manifest=[]
for p in sorted(set(sources)):
 if not p.exists():continue
 rel=p.relative_to(O);dst=P/'recovered'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 text=p.read_text(encoding='utf8');text=re.sub(r'C:[/\\]Users[/\\][^/\\\s"\']+',r'%USERPROFILE%',text)
 dst.write_text(text,encoding='utf8')
 manifest.append({'source':rel.as_posix(),'recovered':dst.relative_to(P).as_posix(),'originalSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'privacySanitized':True})
(P/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
links=''.join(f'<li><a href="{m["recovered"]}">{m["source"]}</a></li>' for m in manifest)
(P/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>三角色提示词与方向恢复</title><style>body{font:16px system-ui;max-width:1100px;margin:30px auto;line-height:1.7;background:#171c29;color:#eee}a{color:#adcafa}li{overflow-wrap:anywhere}</style><h1>三角色提示词与设计方向恢复</h1><p>2026-10-14 · 共'+str(len(manifest))+'份本地原始提示词、批次记录与方向资料。先读<a href="../../docs/current/三角色动作严格审查与续作_20261014.md">最新审查记录</a>。旧提示词含失败稿和旧决定，不能直接当作当前标准。玛薇卡以V10近距离确认、出刀原位落地为准；钟离保留已修岩脊和喝茶；那维莱特保留庄重持杖、单掌洪流方向。</p><p>本批使用内置imagegen。所有原稿、返修提示词均保留；恢复清单含原文件SHA256。</p><ul>'+links+'</ul>',encoding='utf8')
print('Recovered',len(manifest),'reference files')
