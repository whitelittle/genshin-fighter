"""Fit the selected Traveler walk with the established canonical method.

Writes an isolated teaching candidate; never rebuilds or overwrites v13.
"""
from pathlib import Path
import base64,hashlib,json,shutil,struct,sys
from PIL import Image,ImageDraw
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'outputs/lumine-teaching-walk-20261016'
BASE=ROOT/'outputs/tutorial-polish-v13-20261016'
OUT=ROOT/'outputs/tutorial-walk-v14-20261016'
sys.path.insert(0,str(ROOT/'work'))
sys.path.insert(0,str(ROOT/'runtime/tools'))
sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
import clorinde_assets as ca
from compact_assets import LuaRuntime,python_table
from export_furina import lua

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    reference=ROOT/'outputs/lumine-rebuild-20261016/canonical-v4'
    calibration=json.loads((reference/'report.json').read_text(encoding='utf-8'))
    # Preserve the confirmed color-index mapping as well as canonical geometry.
    palette=json.loads((reference/'fit/master-contrast.json').read_text(encoding='utf-8'))['palette']
    scale=calibration['sourceUnit']
    roots=json.loads((ART/'roots.json').read_text(encoding='utf-8'))
    ca.O=ART
    fits={};encoded={}
    for key,anchor in roots.items():
        path=ART/'source'/f'{key}.png';im=Image.open(path).convert('RGBA')
        assert im.size==(1024,1536),(key,im.size)
        bb=im.getchannel('A').point(lambda a:255 if a>=128 else 0).getbbox()
        assert bb and bb[0]>1 and bb[1]>1 and bb[2]<im.width-1 and bb[3]<im.height-1,(key,bb)
        fit,meta=ca.canonical_fit(im,anchor,scale,calibration['palette'],key)
        # Apply the already confirmed color table AFTER quantization. Feeding
        # the contrast palette back into quantization would change pixel ownership.
        shape=Image.open(ART/fit['file']).size
        ca.artlib.render(meta['rects'],palette,*shape).save(ART/fit['file'])
        meta['palette']=palette
        (ART/'fit'/f'{key}.json').write_text(json.dumps(meta,ensure_ascii=False),encoding='utf-8')
        target=Image.open(ART/fit['file']).convert('RGBA')
        raw=struct.pack('<'+'H'*(len(meta['rects'])*5),*(v for rect in meta['rects'] for v in rect))
        raw+=b'\0'*((-len(raw))%3)
        encoded[key]={'n':len(meta['rects']),'d':base64.b64encode(raw).decode(),
                      'pal':[c+[255] for c in palette],'ax':fit['anchor'][0],
                      'ay':fit['anchor'][1],'u':fit['scale'],'w':target.width,'h':target.height}
        fits[key]={**fit,'source':f'source/{key}.png','sourceAnchor':anchor,
                   'sourceSha256':digest(path),'sourceBounds':bb,'sameSourceScale':scale,
                   'sourceGroundedBySupportSole':True,'pixelRoundtrip':True}
    assert digest(ART/'source/master.png')==calibration['frames']['master']['sourceSha256']
    original=json.loads((reference/'fit/master-contrast.json').read_text(encoding='utf-8'))
    actual=json.loads((ART/'fit/master.json').read_text(encoding='utf-8'))
    assert actual['rects']==original['rects'] and actual['palette']==original['palette']
    assert np.array_equal(np.asarray(Image.open(ART/'fit/master.png')),np.asarray(Image.open(reference/'fit/master-contrast.png')))
    keys=['walk-00','walk-02','walk-04','walk-06']
    phases=['近侧腿落脚','近侧腿承重／远侧腿经过','远侧腿落脚','远侧腿承重／近侧腿经过']
    rt=LuaRuntime();rt.execute('__loaders={};'+(BASE/'source/teaching/gf_lumine_training_data.lua').read_text(encoding='utf-8'))
    old=python_table(rt.globals().__loaders['gf_lumine_training_data']())
    data=python_table(rt.globals().__loaders['gf_lumine_training_data']())
    # Old walk_* keys are still consumed by the legacy backward placeholder.
    # Keep those records untouched rather than silently claiming a new backwalk.
    data['frames']['teaching_master']=encoded['master']
    for key in keys:data['frames'][key.replace('-','_')]=encoded[key]
    data['groups']['idle']={'frames':['teaching_master'],'durations':[60]}
    data['groups']['walk']={'frames':[k.replace('-','_') for k in keys],'durations':[12,11,12,11]}
    data['aliases'].update(walk1='walk_00',walk2='walk_04')
    preserved=[k for k in old['frames'] if data['frames'][k]==old['frames'][k]]
    assert len(preserved)==len(old['frames'])
    assert all(data['groups'][k]==v for k,v in old['groups'].items() if k not in ['idle','walk'])
    data['bodyPeak']=max(v['n'] for v in data['frames'].values())
    unique={json.dumps(v,sort_keys=True):v for v in data['frames'].values()}
    mean=sum(v['n'] for v in unique.values())/len(unique)
    assert mean<1000,mean
    shutil.copytree(BASE/'source',OUT/'source',dirs_exist_ok=True)
    module=OUT/'source/teaching/gf_lumine_training_data.lua'
    module.write_text("__loaders['gf_lumine_training_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
    order=json.loads((BASE/'source/order.json').read_text(encoding='utf-8'))
    changed=[p for p in order if digest(BASE/p)!=digest(OUT/p)]
    assert changed==['source/teaching/gf_lumine_training_data.lua'],changed
    code='\n'.join((OUT/p).read_text(encoding='utf-8') for p in order)
    (OUT/'genshin_fighter.lua').write_text(code,encoding='utf-8')
    (OUT/'verification').mkdir(exist_ok=True)
    report={'scope':'荧教学关前进行走候选；既有拟合方式与效果沿用确认；新动作美术及真机待验',
            'sourceUnit':scale,'logicalCell':4.5,'bodyUniqueFrames':len(unique),'bodyUniqueMean':mean,
            'bodyPeak':data['bodyPeak'],'newPeak':max(v['n'] for v in encoded.values()),
            'preservedOldFrames':len(preserved),'onlyChangedSourceFiles':changed,
            'clientSha256':digest(OUT/'genshin_fighter.lua'),'baselineSha256':digest(BASE/'genshin_fighter.lua'),
            'frames':fits,'walk':data['groups']['walk'],'phases':phases,
            'backward':'旧后退暂代，未倒放新前走冒充完成','otherActions':'跳跃、冲撤、攻防等沿用旧暂代，未宣称本批完成',
            'userScopeConfirmed':'继续完成教学关；旅行者荧；母版、拟合方式与效果已初步确认'}
    (ART/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'build-manifest.json').write_text(json.dumps({'clientSha256':report['clientSha256'],
      'sourceFiles':{p:digest(OUT/p) for p in order},'baselineSha256':report['baselineSha256'],
      'onlyChangedSourceFiles':changed},indent=2),encoding='utf-8')
    public={'frames':fits,'keys':keys,'phases':phases,'durations':[12,11,12,11],
            'sourceUnit':scale,'palette':palette,'newPeak':report['newPeak']}
    (ART/'walk-data.js').write_text('window.WALK='+json.dumps(public,ensure_ascii=False)+';',encoding='utf-8')
    # Export one shared indexed GIF palette to avoid animation palette flicker.
    pal=[0,0,0]+[v for c in palette for v in c];pal+= [0]*(768-len(pal))
    gif=[];board=Image.new('RGB',(1200,430),'#263454');draw=ImageDraw.Draw(board)
    for i,key in enumerate(keys):
        meta=json.loads((ART/'fit'/f'{key}.json').read_text(encoding='utf-8'))
        frame=Image.new('P',(104,104),0);frame.putpalette(pal)
        paint=ImageDraw.Draw(frame);ox=48-meta['anchor'][0];oy=91-meta['anchor'][1]
        for x,y,w,h,c in meta['rects']:paint.rectangle((ox+x,oy+y,ox+x+w-1,oy+y+h-1),fill=c+1)
        gif.append(frame.resize((416,416),Image.Resampling.NEAREST))
        rgb=frame.convert('RGBA');rgb.putalpha(Image.fromarray((np.asarray(frame)>0).astype('uint8')*255))
        rgb=rgb.resize((300,300),Image.Resampling.NEAREST);board.paste(rgb,(i*300,50),rgb)
        draw.text((i*300+12,14),key+' / '+str(fits[key]['rectangles'])+' rects',fill='white')
    gif[0].save(ART/'walk.gif',save_all=True,append_images=gif[1:],duration=[200,180,200,180],loop=0,transparency=0,disposal=2,optimize=False)
    board.save(ART/'contact-sheet.png')
    print(json.dumps({k:v for k,v in report.items() if k not in ['frames','phases']},ensure_ascii=False))

if __name__=='__main__':main()
