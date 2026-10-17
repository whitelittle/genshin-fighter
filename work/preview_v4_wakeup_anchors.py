"""Explicit draft source-coordinate roots, not independently centered crops."""
from pathlib import Path
import json
from PIL import Image,ImageDraw
V=Path(__file__).resolve().parent/'v4-handoff-20261009-partial/V4'
BASE=V/'evidence/codex-batch-20261009'
NAME='kamisatoayaka-wakeup-body-v1'
F=BASE/NAME
report=json.loads((F/'fit.json').read_text(encoding='utf-8'))
OUT=BASE/'kamisatoayaka-wakeup-anchor-study-v1'
OUT.mkdir(parents=True,exist_ok=True)
# Approximate marks from inspected full source. Explicit draft, not engine roots.
# Lying/seated root is projected pelvis/support plane; final root is between feet.
source_roots=[(382,346),(1110,382),(640,928),(1140,992)]
records=[];panels=[]
zoom=3;world=(240,220);size=(520,290)
for n,f in enumerate(report['frames']):
    sprite=Image.open(F/f'fit-{n}.png').convert('RGBA')
    crop=f['crop_box'];cw,ch=crop[2]-crop[0],crop[3]-crop[1]
    x,y=source_roots[n]
    local=((x-crop[0])*sprite.width/cw,(y-crop[1])*sprite.height/ch)
    records.append({'frame':n,'source_point':list(source_roots[n]),'fit_root':list(local),
                    'status':'rough_visual_draft_unaccepted','world':[0,0],
                    'support':'projected pelvis/ground' if n<2 else 'planted foot/ground'})
    sheet=Image.new('RGB',(size[0]*2,size[1]))
    for col,bg in enumerate(['#202733','#e5e8ec']):
        panel=Image.new('RGBA',size,bg);d=ImageDraw.Draw(panel)
        d.line((8,world[1],size[0]-8,world[1]),fill='#728197')
        scaled=sprite.resize((sprite.width*zoom,sprite.height*zoom),Image.Resampling.NEAREST)
        panel.alpha_composite(scaled,(round(world[0]-local[0]*zoom),round(world[1]-local[1]*zoom)))
        d.line((world[0]-5,world[1],world[0]+5,world[1]),fill='#ff3865',width=2)
        d.line((world[0],world[1]-5,world[0],world[1]+5),fill='#ff3865',width=2)
        d.text((8,8),f'DRAFT ROOT / PHASE {n} / NOT GAME',fill='#8899aa')
        d.text((8,267),'Fixed world root; no per-frame centering',fill='#8899aa')
        sheet.paste(panel.convert('RGB'),(col*size[0],0))
    panels.append(sheet)
panels[0].save(OUT/'grounded-draft.gif',save_all=True,append_images=panels[1:],duration=[400,400,400,700],loop=0)
poster=Image.new('RGB',(size[0]*2,size[1]*4))
for n,p in enumerate(panels):poster.paste(p,(0,n*size[1]))
poster.save(OUT/'grounded-draft.png')
metadata={'source_sha256':report['source_sha256'],'frames':records,
          'method':'manual rough marks on inspected source mapped through actual crop and fit dimensions',
          'exact_support_measurement':False,'biomechanics_accepted':False,'runtime_ready':False,
          'purpose':'Expose ground/root/height discontinuity at fixed world position; not runtime calibration',
          'not_validated':['anatomy','head scale continuity','lying facing transition','neutral hand/scabbard layer','true device performance']}
(OUT/'anchors-draft.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved explicit draft-root comparison and slow playback; not runtime-ready')
