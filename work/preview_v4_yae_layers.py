"""Offline layered study: source-coordinate provenance, V3 fitting, proposed timing only."""
from pathlib import Path
import sys,json,hashlib,ast
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'work/github-review-20261009/game/tools'))
sys.path.insert(0,str(ROOT/'work'))
import artlib
from fit_v4_prototype import scan_rects,bounded_rects
tree=ast.parse((ROOT/'work/fit_v4_free_atlas.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['components','box']],type_ignores=[]),'free_atlas_helpers','exec'))
V=ROOT/'work/v4-handoff-20261009-partial/V4'
BASE=V/'evidence/codex-batch-20261009'
OUT=BASE/'yaemiko-crouchheavy-layered-study-v1';OUT.mkdir(parents=True,exist_ok=True)
source=V/'assets/codex-batch-20261009/yaemiko-crouchheavy-hitfx-v1.png'
im=Image.open(source).convert('RGBA');raw=np.asarray(im);groups=components(raw[:,:,3]>=128)
major=groups[:4];major.sort(key=lambda g:box(g)[0]);allgroups=[[g] for g in major]
assert len(major)==4
areas=[sum(x1-x0 for y,x0,x1 in g) for g in major]
for g in groups[4:]:
    x0,y0,x1,y1=box(g);cx=(x0+x1)/2;cy=(y0+y1)/2
    def distance(k):
        a,b,c,d=box(major[k]);return max(a-cx,0,cx-c)**2+max(b-cy,0,cy-d)**2
    allgroups[min(range(4),key=distance)].append(g)
fx=[];fxrecords=[];scale=24/max(box(g)[3]-box(g)[1] for g in major)
for n,gg in enumerate(allgroups):
    support=np.zeros(raw.shape[:2],dtype='uint8');joined=[]
    for g in gg:
        joined.extend(g)
        for y,x0,x1 in g:support[y,x0:x1]=255
    keep=np.asarray(Image.fromarray(support).filter(ImageFilter.MaxFilter(7)))>0
    bounds=box(joined);x0,y0,x1,y1=bounds;bounds=[max(0,x0-3),max(0,y0-3),min(im.width,x1+3),min(im.height,y1+3)]
    isolated=raw.copy();isolated[~keep,3]=0
    crop=Image.fromarray(isolated).crop(bounds);crop.save(OUT/f'fx-source-{n}.png')
    fx.append(artlib.downscale(crop,scale));fxrecords.append({'frame':n,'crop_box':bounds,'main_box':box(major[n]),'scale':scale,'particle_groups':len(gg)})
palette=artlib.build_palette(fx,5,seed=22)
fitted=[]
for n,c in enumerate(fx):
    idx=artlib.apply_palette(c,palette);rr=artlib.painter(idx);scan=scan_rects(idx);bounded=bounded_rects(idx,rr)
    fitted.append(artlib.render(bounded,palette,idx.shape[1],idx.shape[0]));control=artlib.render(scan,palette,idx.shape[1],idx.shape[0])
    assert np.array_equal(np.asarray(fitted[-1]),np.asarray(control))
    fitted[-1].save(OUT/f'fx-fit-{n}.png');fxrecords[n].update(rect_count=len(rr),bounded_rect_count=len(bounded),rects=bounded,exact_reconstruction=True)
bodyfolder=BASE/'yaemiko-crouchheavy-body-v3';foxfolder=BASE/'yaemiko-crouchheavy-fox-pink-v1'
body=[Image.open(bodyfolder/f'fit-bounded-{n}.png').convert('RGBA') for n in range(4)]
foxreport=json.loads((foxfolder/'fit.json').read_text(encoding='utf-8'))
fox=[artlib.render(f['bounded_rects'],foxreport['palette'],*f['fit_size']) for f in foxreport['frames']]
breport=json.loads((bodyfolder/'fit.json').read_text(encoding='utf-8'))
# Proposed heel roots observed from source images. Must be reviewed, not declared exact.
bodyroots=[(49,58),(49,58),(49,55),(49,55)]
feet=[(40,fox[0].height-1),(45,fox[1].height-1),(48,fox[2].height-1),(39,fox[3].height-1)]
frames=[];timeline=[]
for tick in range(48):
    phase=0 if tick<12 else 1 if tick<18 else 2 if tick<24 else 3
    image=Image.new('RGBA',(440,150),'#202733');d=ImageDraw.Draw(image)
    ground=118;d.line((12,ground,428,ground),fill='#465461',width=1)
    bx,by=bodyroots[phase];image.alpha_composite(body[phase],(70-bx,ground-by))
    # One helper moves out then returns, never duplicates simultaneously.
    travel=0 if tick<18 else round((tick-18)/6*68) if tick<24 else round((48-tick)/24*68)
    fxfoot,fyfoot=feet[phase];fox_x=125+travel
    image.alpha_composite(fox[phase],(fox_x-fxfoot,ground-fyfoot))
    effect_visible=False  # User flagged the crescent as an unrelated blade; removed.
    if effect_visible:
        effect_phase=2 if tick<24 else 3
        sprite=fitted[effect_phase]
        image.alpha_composite(sprite,(fox_x+4,ground-25))
    d.text((8,6),f'STUDY ONLY  tick {tick:02d}/48  phase {phase}  NOT GAME',fill='#aeb9cb')
    d.text((8,136),'body / one pink fox / NO blade effect | anchors proposed',fill='#aeb9cb')
    frames.append(image.convert('RGB'))
    timeline.append({'tick':tick,'body_phase':phase,'helper_phase':phase,'helper_x':fox_x,
                     'fx_visible':effect_visible,'proposed_release_event':tick==18})
frames[0].save(OUT/'layered-playback.gif',save_all=True,append_images=frames[1:],duration=17,loop=0)
poster=Image.new('RGB',(880,300))
for i,t in enumerate([0,12,20,34]):poster.paste(frames[t],((i%2)*440,(i//2)*150))
poster.save(OUT/'layered-keyframes.png')
body_peak=max(f['bounded_rect_count'] for f in breport['frames'])
helper_peak=max(f['bounded_rect_count'] for f in foxreport['frames']);fxpeak=max(f['bounded_rect_count'] for f in fxrecords)
report={'method':'Offline pixel compositor and restored V3 painter, no game logic implemented',
        'fx_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'fx_palette':palette,'fx_frames':fxrecords,
        'body_roots_proposed':bodyroots,'helper_foot_roots_proposed':feet,'anchor_status':'rough visual marks; needs precise review',
        'timeline_candidate':timeline,'logic_tick_and_damage_implemented':False,
        'blade_effect_removed':True,'unused_fx_status':'historical experiment, excluded from current composition',
        'visible_layer_image_peak_upper_bound':body_peak+helper_peak,
        'two_actor_all_layer_double_buffer_upper_bound':4*(body_peak+helper_peak),
        'native_controls':'not measured; image templates may have container wrappers',
        'accepted':False,'device':False,'review':['FX particle grouping nearest main component is heuristic and requires visual check',
        'GIF nominal17ms is approximate; not measured60FPS','Helper return currently provisional, collision and interrupt not implemented']}
(OUT/'study.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'fx_bounded_rects':[f['bounded_rect_count'] for f in fxrecords],
                  'visible_layer_image_peak_upper_bound':report['visible_layer_image_peak_upper_bound'],
                  'two_actor_all_layer_double_buffer_upper_bound':report['two_actor_all_layer_double_buffer_upper_bound']}))
