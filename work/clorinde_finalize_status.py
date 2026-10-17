from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];O=R/'outputs/clorinde-actions-20261011'
p=O/'actions.json';d=json.loads(p.read_text(encoding='utf-8'))
for k,v in d.items():
 if k!='throw':v['status']='本轮新图与拟合候选；本地文件/播放检查通过，最终美术及正式战斗待验收'
p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
p=O/'player.js';s=p.read_text(encoding='utf-8')
s=s.replace("$('source').href=d.sourceFrames[indices[0]].source||d.sourceFrames[indices[0]].file;", "const sourceLink=d.sourceFrames.find(f=>!f.file.startsWith('frames/idle-'))||d.sourceFrames[indices[0]];$('source').href=sourceLink.source||sourceLink.file;")
p.write_text(s,encoding='utf-8')
