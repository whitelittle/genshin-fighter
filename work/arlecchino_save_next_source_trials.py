from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';s=json.loads((o/'current-status.json').read_text(encoding='utf-8'));trials=[]
for name,note in [('light3-hook-v2','镰刃前向上钩六姿；待完整提取、杆轴/握点与尺度复核'),('heavy-hook-v2','镰刃前向重钩六姿；右侧刀尖贴近画布，需复核完整轮廓与脚底（不得按刀尖底部定脚底）'),('crouchlight-v1','低位枪尾短击四姿；待提取、低姿接触与杆轴保护')]:
 p=o/'source'/f'{name}.png';im=Image.open(p).convert('RGBA');a=np.array(im)[:,:,3];trials.append({'source':p.relative_to(o).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':list(im.size),'outerEdgeAlpha128Pixels':int((a[:,[0,-1]]>=128).sum()),'status':note,'active':False})
s['sourceCandidatesReadyForExtraction']=trials;s['nextStep']='按已保存light3-hook-v2、heavy-hook-v2、crouchlight-v1逐对象提取，不重复生成；保留低alpha杆轴原RGBA与独立靴底支撑。之后补剩余动作/特效/Q/双方投技及共享落地起身链。';(o/'current-status.json').write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
(o/'next-source-trials.json').write_text(json.dumps(trials,ensure_ascii=False,indent=2),encoding='utf-8')
with (o/'制作与交付.md').open('a',encoding='utf-8') as f:f.write('\n### 已保存下一批源候选\n\n`light3-hook-v2.png`、`heavy-hook-v2.png`、`crouchlight-v1.png`与完整提示词已返回并目视检查；前两组明确改为镰刃在前的上钩/重钩，蹲轻为有意枪尾短击。三组尚未加入九组动作表，不计额外可播放完成。右侧重攻刀尖接近画布边缘，当前外边缘alpha128像素为0，不能仅凭这个数字宣布轮廓通过；继续复核。持武器支撑必须按实际鞋底，不按可能更低的刀尖确定。源哈希和待提取状态见`next-source-trials.json`。\n')
manifest={'candidate':True,'sourceTool':'built-in image_gen','actions':9,'poses':42,'files':[]}
for p in sorted(o.rglob('*')):
 if p.is_file() and p.name!='manifest.json':manifest['files'].append({'path':p.relative_to(o).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(o/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved 3 next source sets without inflating active action count')
