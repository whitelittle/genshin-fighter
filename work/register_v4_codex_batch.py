"""Persist this session's generated sources and receipt classifications for review."""
from pathlib import Path
import json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent.parent
V=ROOT/'work/v4-handoff-20261009-partial/V4'
ASSETS=V/'assets/codex-batch-20261009';PROMPTS=V/'prompts/codex-batch-20261009'
OUT=V/'evidence/codex-batch-20261009';OUT.mkdir(parents=True,exist_ok=True)
special={'zhongli-airlight-body-v2':'needs_grip_and_composition_review',
         'zhongli-standguard-body-v1':'requires_pose_overlap_fix',
         'zhongli-airlight-contact-study-v1':'historical_contact_study_not_layered',
         'zhongli-airlight-contact-study-v2':'deferred_contact_study_not_layered',
         'yaemiko-crouchheavy-body-v2':'historical_layout_candidate',
         'yaemiko-crouchheavy-hitfx-v1':'removed_from_current_yae_composition_unrelated_blade',
         'yaemiko-crouchheavy-fox-v1':'historical_purple',
         'yaemiko-crouchheavy-fox-v2':'historical_purple'}
records=[]
overrides=json.loads((OUT/'SOURCE_REVIEW_OVERRIDES.json').read_text(encoding='utf-8')) if (OUT/'SOURCE_REVIEW_OVERRIDES.json').exists() else {}
for path in sorted(ASSETS.glob('*.png')):
    prompt=PROMPTS/(path.stem+'.txt')
    assert prompt.exists(),f'missing prompt for {path.stem}'
    with Image.open(path) as im:
        rgba=im.convert('RGBA');size=list(im.size);alpha=list(rgba.getchannel('A').getextrema())
    status=special.get(path.stem,'historical_purple_single_pose' if path.stem.startswith('yaemiko-fox-single-') else 'source_candidate_requires_review')
    status=overrides.get(path.stem,{}).get('status',status)
    records.append({'id':path.stem,'source':path.relative_to(V.parent).as_posix(),
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'size':size,'alpha_extrema':alpha,
                    'prompt':prompt.relative_to(V.parent).as_posix(),'prompt_sha256':hashlib.sha256(prompt.read_bytes()).hexdigest(),
                    'tool':'built-in image_gen','status':status,'visual_review':overrides.get(path.stem),'user_accepted':False,'game_integrated':False,
                    'evidence_folder':(OUT/path.stem).relative_to(V.parent).as_posix() if (OUT/path.stem).exists() else None})
report={'date':'2026-10-09','generated_source_count':len(records),'records':records,
        'tool_errors':[{'job':'yaemiko-fox-single-2','type':'connection_failed','message':'image generation failed: connection failed: error sending request','retry':'same prompt retry succeeded','quota_exhaustion':False}],
        'quota_exhausted':False,'accepted':0,'game_integrated':0,
        'latest_decisions':['no fixed grid boundaries','fox pink','remove unrelated blade effect from Yae preview']}
if (OUT/'REQUEST_ERRORS.json').exists():
    errors=json.loads((OUT/'REQUEST_ERRORS.json').read_text(encoding='utf-8'))
    report['tool_errors']=errors['errors'];report['quota_exhausted']=errors.get('quota_exhausted',False)
(OUT/'BATCH_MANIFEST.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
cols=3;cellw,cellh=420,310;rows=(len(records)+cols-1)//cols
gallery=Image.new('RGB',(cols*cellw,rows*cellh),'#202733');draw=ImageDraw.Draw(gallery)
for n,r in enumerate(records):
    im=Image.open(V.parent/r['source']).convert('RGBA');scale=min((cellw-20)/im.width,(cellh-55)/im.height)
    thumb=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
    x=(n%cols)*cellw;y=(n//cols)*cellh
    gallery.paste(thumb,(x+(cellw-thumb.width)//2,y+5),thumb)
    draw.text((x+8,y+cellh-40),r['id'],fill='#eef2f9')
    draw.text((x+8,y+cellh-22),'CANDIDATE / NOT ACCEPTED',fill='#aeb9cb')
gallery.save(OUT/'batch-overview.png')
lines=['# 本轮生成成果索引','','全部为候选或历史；正式验收0，游戏接入0。源图与提示词均保存哈希。','',
       '|候选|状态|源图|证据|','|---|---|---|---|']
for r in records:
    src='../../'+r['source'].removeprefix('V4/')
    evidence='[查看]('+r['id']+'/fit.json)' if r['evidence_folder'] and (OUT/r['id']/'fit.json').exists() else '待检查'
    lines.append('|'+r['id']+'|'+r['status']+'|[原图]('+src+')|'+evidence+'|')
(OUT/'成果索引.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print('Registered',len(records),'generated images; full prompts and hashes preserved')
