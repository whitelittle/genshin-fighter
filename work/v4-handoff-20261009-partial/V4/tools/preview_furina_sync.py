"""Preview an authored timing candidate, without collision or game integration."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
V=Path(__file__).resolve().parents[1]
job=next(j for j in json.loads((V/'design/ROSTER_JOBS.json').read_text())['jobs'] if j['character']=='furina')
out=V/'evidence'/job.get('E_assistant_evidence_batch','furina-salon-refinement-v2')
t=json.loads((V/'design/furina-E-sync-candidate.json').read_text())
def phase(tick,starts):return max(n for n,start in enumerate(starts) if tick>=start)
def source(folder,n):return Image.open(folder/f'optimized-{n}.png').convert('RGBA')
frames=[]
for tick in range(t['total_ticks']):
    p=phase(tick,t['body_phase_starts']);mp=phase(tick,t['member_phase_starts'])
    canvas=Image.new('RGBA',(380,190),'#232936')
    canvas.alpha_composite(source(V/'evidence/furina-E-review',p),tuple(t['illustrative_scene_root_positions']['body']))
    for member in ('usher','chevalmarin','crabaletta'):
        canvas.alpha_composite(source(out/member,mp),tuple(t['illustrative_scene_root_positions'][member]))
    if t['effect_visible_ticks'][0]<=tick<t['effect_visible_ticks'][1]:
        ep=phase(tick,t['effect_phase_starts'])
        canvas.alpha_composite(source(V/'evidence/furina-E-fx-review',ep),tuple(t['illustrative_scene_root_positions']['water_effect']))
    d=ImageDraw.Draw(canvas);stage='STARTUP' if tick<18 else 'ACTIVE' if tick<24 else 'RECOVERY'
    d.text((10,10),f'OFFLINE CANDIDATE  tick {tick:02d}/47  {stage}',fill='#d9e4fa')
    frames.append(canvas.convert('RGB').resize((1140,570),Image.Resampling.NEAREST))
# GIF time quantization is only a preview; JSON remains authoritative at 60Hz.
frames[0].save(out/'timed-scene-playback.gif',save_all=True,append_images=frames[1:],duration=[20 if n%3==0 else 10 if n%3==1 else 20 for n in range(48)],loop=0)
frames[18].save(out/'timed-scene-active.png')
(out/'timing-evidence.json').write_text(json.dumps({'schedule':t,'gif_timing':'GIF centiseconds approximating 60Hz; no gameplay simulation','frames_written':48,'status':'offline_authored_preview_only'},ensure_ascii=False,indent=2))
print('48 authored display ticks, one shared release marker; no game damage executed')
