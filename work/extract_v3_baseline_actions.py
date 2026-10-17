"""Export actual Raiden/Nahida source poses and inherited effective move tables."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageDraw
from v3_runtime_harness import ROOT,BASE,load_runtime,plain
OUT=ROOT/'outputs/v4-one-character-20261010/baseline-actions'
OUT.mkdir(parents=True,exist_ok=True)
rt=load_runtime();require=rt.globals().GF_REQUIRE
K=require('gf_kits');R=require('gf_roster');U=require('gf_util')
anim=require('gf_animation_data');between=require('gf_inbetween_data')
result={'baseline':'V3 accepted E','simulation_hz':60,'internal_units_per_design_unit':100,
        'scope':'Source extraction and code parameters, not new gameplay/device acceptance','characters':{}}
for char in [R[1],R[2]]:
    key=char.key;name='raiden' if key=='raidenshogun' else 'nahida'
    folder=OUT/key;folder.mkdir(exist_ok=True)
    bank=anim[name].lo;palette=plain(bank.pal)
    # Palette here already consists of numeric channels, not a string.
    poses=[];sheets={}
    for origin,b in [('keyframes',bank),('inbetweens',between.poses[name].lo)]:
        for pose,src in sorted(b.items(),key=lambda p:str(p[0])):
            if not hasattr(src,'items') or src.n is None:continue
            if src.d is not None:
                decoded=U.decodeAll(src.d)
                vals=[int(decoded[i*2-1])+int(decoded[i*2])*256 for i in range(1,int(src.n)*5+1)]
            else:
                vals=[src.bytes[i] for i in range(1,int(src.n)*5+1)]
            im=Image.new('RGBA',(math.ceil(src.w),math.ceil(src.h)))
            draw=ImageDraw.Draw(im)
            for i in range(0,len(vals),5):
                x,y,w,h,c=vals[i:i+5];col=palette[c]
                draw.rectangle((x,y,x+w-1,y+h-1),fill=tuple(col[:4] if len(col)>3 else col+[255]))
            path=folder/(str(pose)+'.png');im.save(path)
            record={'pose':pose,'origin':origin,'rects':int(src.n),'w':src.w,'h':src.h,
                    'ax':src.ax,'ay':src.ay,'u':src.u,'baked':bool(src.baked),'file':path.relative_to(OUT).as_posix(),
                    'png_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
            poses.append(record)
            if origin=='keyframes':sheets.setdefault(str(pose).rsplit('_',1)[0],[]).append((str(pose),im))
    for sheet,images in sheets.items():
        poster=Image.new('RGB',(280*4,330*math.ceil(len(images)/4)),'#202733');d=ImageDraw.Draw(poster)
        for i,(label,im) in enumerate(images):
            scale=min(250/im.width,290/im.height);thumb=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
            x=i%4*280;y=i//4*330;poster.paste(thumb,(x+(280-thumb.width)//2,y+5),thumb)
            d.text((x+8,y+307),label,fill='#eef2f9')
        poster.save(folder/(sheet+'-contact.png'))
    result['characters'][key]={'roster':plain(char),'body':plain(K.body[key] or K.body.default),
        'weapon':plain(K.weapons[char.weapon]),'skill':plain(K.skills[key]),'burst_table':plain(K.bursts[key]),
        'throw_table':plain(K.throw),'poses':poses,'body_pool_peak':max(p['rects'] for p in poses),
        'notes':['Q and throw effective timing must use gf_sim branches, not only K table',
                 'PNG is decoded source-pixel drawing; runtime applies u, anchors, view transforms and seam',
                 'Raiden qburst runtime additionally applies 0.77 to original u; idle_1 boot-aligned copy',
                 'Logic y up; image y down; screen animation does not define collision']}
result['source_sha256']={name:hashlib.sha256((BASE/'source/modules'/name).read_bytes()).hexdigest() for name in ['gf_kits.lua','gf_sim.lua','gf_fview.lua','gf_animation_data.lua','gf_inbetween_data.lua']}
(OUT/'parameters.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:{'poses':len(v['poses']),'keyframes':sum(p['origin']=='keyframes' for p in v['poses']),'pool_peak':v['body_pool_peak']} for k,v in result['characters'].items()}))
