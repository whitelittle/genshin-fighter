"""Extract new held-weapon poses and reuse the V3 action-page HTML."""
from pathlib import Path
from collections import deque
import json
import shutil
from PIL import Image
from build_ayaka_full_animation_candidate import SOURCES, FIT_ROOT

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/v4-one-character-20261010/ayaka-armed-v2'
SRC=OUT/'standguard-source-v2.png' if (OUT/'standguard-source-v2.png').exists() else OUT/'standguard-source-v1.png'
im=Image.open(SRC).convert('RGBA')
w,h=im.size
alpha=im.getchannel('A').tobytes()
seen=bytearray(w*h)
components=[]
for start in range(w*h):
    if seen[start] or alpha[start]<64: continue
    queue=deque([start]);seen[start]=1;pts=[]
    while queue:
        p=queue.popleft();pts.append(p);x=p%w;y=p//w
        for q in (p-1 if x else -1,p+1 if x<w-1 else -1,p-w if y else -1,p+w if y<h-1 else -1):
            if q>=0 and not seen[q] and alpha[q]>=64:
                seen[q]=1;queue.append(q)
    if len(pts)>1000:components.append(pts)
components=sorted(sorted(components,key=len,reverse=True)[:4],key=lambda p:min(q%w for q in p))
if len(components)!=4:raise RuntimeError('Expected four separate pose objects')
frames=[]
for i,pts in enumerate(components):
    box=(min(p%w for p in pts),min(p//w for p in pts),max(p%w for p in pts)+1,max(p//w for p in pts)+1)
    mask=Image.new('L',im.size);mp=mask.load()
    for p in pts:mp[p%w,p//w]=alpha[p]
    frame=im.copy();frame.putalpha(mask);frame=frame.crop(box)
    frame.save(OUT/f'guard-{i}.png')
    foot_x=[320,800,1290,1750][i]
    frames.append({'file':f'guard-{i}.png','roi':list(box),'anchor':[foot_x-box[0],754-box[1]],'scale':0.50,'source':SRC.name})
(OUT/'frames.json').write_text(json.dumps({'frames':frames,'scale_policy':'same 0.5 source-pixel scale for all frames','status':'source candidate; rough support anchors'},ensure_ascii=False,indent=2),encoding='utf-8')
actions={'站立格挡':{'frames':frames,'durations':[12,24,12,24],'phases':['进入格挡','保持','受力','恢复'],'status':'新作v2，胸前架刀；关键姿势待验'}}
candidate_root=ROOT/'outputs/v4-one-character-20261010/ayaka-full-animation-candidate/actions'
for label,key in {'待机':'idle','前走':'walk','后退':'backwalk','跳跃':'jump','前冲':'forwarddash','后撤':'backdash','蹲下':'crouch','蹲防':'crouchguard','轻攻一':'light1','受击与倒地':'hurt_knockdown','起身':'wakeup','E · 冰华':'E','败北':'defeat'}.items():
    items=[]
    for i,p in enumerate(sorted((candidate_root/key).glob('body-*.png'))):
        image=Image.open(p)
        filename=f'{key}-candidate-{i}.png';shutil.copy2(p,OUT/filename)
        items.append({'file':filename,'anchor':[image.width/2,image.height-2],'scale':4.5})
    source_dir=FIT_ROOT/SOURCES[key] if key in SOURCES else ROOT/'outputs/v4-one-character-20261010/ayaka-light1-candidate/frames'
    source_paths=sorted(source_dir.glob('source-cell-*.png')) or sorted(source_dir.glob('source-[0-9]*.png'))
    originals=[]
    for i,p in enumerate(source_paths[:len(items)]):
        source=Image.open(p);fit=Image.open(OUT/items[i]['file'])
        ratio=source.height/fit.height
        filename=f'{key}-source-{i}.png';shutil.copy2(p,OUT/filename)
        originals.append({'file':filename,'anchor':[items[i]['anchor'][0]*ratio,items[i]['anchor'][1]*ratio],'scale':items[i]['scale']/ratio})
    if items:actions[label]={'frames':items,'sourceFrames':originals if len(originals)==len(items) else items,'durations':[10]*len(items),'phases':[f'姿势 {i+1}' for i in range(len(items))],'status':'已有候选，开放供筛选；粗锚点'}
victory=Image.open(ROOT/'work/v4-handoff-20261009-partial/V4/assets/codex-batch-20261009/kamisatoayaka-victory-body-v1.png')
win_frames=[]
for i in range(4):
    cell= victory.crop((i*victory.width//4,0,(i+1)*victory.width//4,victory.height))
    name=f'victory-source-{i}.png';cell.save(OUT/name)
    win_frames.append({'file':name,'anchor':[cell.width*.60,960],'scale':.34})
actions['胜利']={'frames':win_frames,'sourceFrames':win_frames,'durations':[18,18,24,36],'phases':['站定','整理衣装','致意','收势'],'status':'保留既有胜利源图；背景与切帧待处理，旧拟合不展示'}
# Group calibration uses a reference pose, never each frame's changing bbox.
# Heights below are measured reference-pose display extents in the prior viewer.
# They are a first-pass display correction; weapon/limb proportions need review.
reference_heights={'站立格挡':318.5 if SRC.name.endswith('v2.png') else 330.0,'待机':305.3,'前走':324.0,'后退':305.1,
    '跳跃':304.8,'前冲':304.8,'后撤':305.2,'蹲下':305.3,'蹲防':304.9,
    '轻攻一':281.5,'受击与倒地':305.1,'起身':305.0,'E · 冰华':324.0,
    '败北':305.1,'胜利':316.2}
for name,action in actions.items():
    factor=305.3/reference_heights[name]
    lists=[action['frames']]
    if action.get('sourceFrames') is not action['frames'] and action.get('sourceFrames'):
        lists.append(action['sourceFrames'])
    for group in lists:
        base_scale=group[0]['scale']*factor
        for frame in group:frame['scale']=base_scale
    action['displayCalibration']={'factor':round(factor,5),'targetStandingHeight':305.3,'policy':'one fixed scale per action, provisional reference-pose calibration'}
    action['status']+='；显示尺度已初校'
if (OUT/'new-actions.json').exists():
    actions.update(json.loads((OUT/'new-actions.json').read_text(encoding='utf-8')))
if '被投' in actions:
    victim=actions['被投']
    current=victim['frames']
    down_action=actions['受击与倒地']
    down_sources=(down_action.get('sourceFrames') or down_action['frames'])[-2:]
    down_fits=down_action['frames'][-2:]
    # Remove a disconnected fragment from the original landing ROI, without
    # changing its canvas or source-coordinate anchor.
    landing=dict(down_sources[0])
    landing_image=Image.open(OUT/landing['file']).convert('RGBA')
    lw,lh=landing_image.size;la=landing_image.getchannel('A').tobytes();ls=bytearray(lw*lh);main=[]
    for lp in range(lw*lh):
        if ls[lp] or la[lp]<64:continue
        lq=deque([lp]);ls[lp]=1;part=[]
        while lq:
            v=lq.popleft();part.append(v);xx=v%lw;yy=v//lw
            for z in (v-1 if xx else -1,v+1 if xx<lw-1 else -1,v-lw if yy else -1,v+lw if yy<lh-1 else -1):
                if z>=0 and not ls[z] and la[z]>=64:ls[z]=1;lq.append(z)
        if len(part)>len(main):main=part
    lm=Image.new('L',landing_image.size);lmp=lm.load()
    for v in main:lmp[v%lw,v//lw]=la[v]
    landing_image.putalpha(lm);landing['file']='original-landing-clean.png';landing_image.save(OUT/landing['file'])
    # Keep one airborne reaction, then reuse the established knockdown ending.
    indices=[0,1,1,3]
    victim['frames']=[dict(current[i]) for i in indices]+[dict(f) for f in down_fits]
    victim['sourceFrames']=[dict(current[i]) for i in indices]+[landing,dict(down_sources[1])]
    victim['phases']=['被抓','上升','腾空','下落','落地','倒地']
    victim['status']='被投连续段接原倒地；落地单段结算'
    victim['continuation']={'action':'受击与倒地','frame':'last','atTick':44}
(OUT/'actions.json').write_text(json.dumps(actions,ensure_ascii=False,indent=2),encoding='utf-8')
template=ROOT/'work/github-review-20261009/V3/assets/action-reference/raiden/index.html'
html=template.read_text(encoding='utf-8')
html=html.replace('雷电将军 · 动作预览','神里绫华 · 持械动作重制')
html=html.replace('雷电将军 · 动作补帧 r28 · r31 · 雷眼与前景修复','神里绫华 · 动作展示')
html=html.replace('../action-wrap.css?v=wrap1','action-wrap.css?v=wrap2')
html=html.replace('app.js?v=r31','app.js?v=attacks2')
html=html.replace('<label><input id="body"', '<label>素材<select id="material"><option value="source" selected>源图</option><option value="fit">拟合图</option></select></label><a id="sourceLink" target="_blank">查看原始图</a><label><input id="body"',1)
html=html.replace('<label><input id="loop"', '<label><input id="stageMove" type="checkbox" checked>舞台位移</label><label><input id="opponent" type="checkbox" checked>对手</label><label><input id="loop"',1)
html=html.replace('<label><input id="loop"', '<label><input id="boxes" type="checkbox">判定框</label><label><input id="loop"',1)
html=html.replace('<label><input id="loop"', '<label>背景<select id="background"><option value="#171625">深色</option><option value="#ffffff">白色</option></select></label><label><input id="loop"',1)
html=html.replace('轻攻击第一段','站立格挡 · 新制作')
html=html.replace('动作试稿，尚未接入正式游戏。预览时序用于检查衔接，不代表最终战斗帧表。','新持械格挡：进入→保持→受力→恢复。共用源像素倍率；脚底锚点为粗校准。其余动作等待重制。')
start=html.index('<span><a href=');end=html.index('</span>',start)+len('</span>')
html=html[:start]+'<span><a href="http://127.0.0.1:8767/actions/nahida/">草神展示</a> · <a href="http://127.0.0.1:8767/actions/raiden/">雷神展示</a></span>'+html[end:]
html=html.replace('</style>','#note,#pair{display:none}.action:disabled{opacity:.35}</style>')
(OUT/'index.html').write_text(html,encoding='utf-8')
shutil.copy2(template.parent.parent/'action-wrap.css',OUT/'action-wrap.css')
served=template.parent.parent/'ayaka'
served.mkdir(exist_ok=True)
for p in OUT.iterdir():
    if p.suffix in ('.html','.js','.css','.json','.png'):shutil.copy2(p,served/p.name)
old=ROOT/'outputs/v4-one-character-20261010/ayaka-full-animation-candidate/viewer.html'
old.write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=http://127.0.0.1:8767/actions/ayaka/"><a href="http://127.0.0.1:8767/actions/ayaka/">绫华持械动作重制：原展示模板</a>',encoding='utf-8')
print(json.dumps({'components':[len(p) for p in components],'frames':frames},ensure_ascii=False))
