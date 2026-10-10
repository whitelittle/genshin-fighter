"""Explicit latest user decisions, separate from rejected head-only calibration."""
from copy import deepcopy
import json
import numpy as np
from PIL import Image

AIR_SOLES={'空轻':[[211,451],[171,473],[143,404],[173,401],[143,498],[166,415]],
           '空重':[[246,496],[189,493],[144,502],[180,494],[161,493],[195,458]]}

def apply(data,folder,fit,palette):
    # One scale adjustment for the whole defeat action, referenced to its first
    # upright pose, NOT equal silhouette heights for kneeling/lying poses.
    idle=data['待机']['frames'][0];ref=json.loads((folder/idle['file']).with_suffix('.rects.json').read_text(encoding='utf-8'))['bodyBoundingBox']
    target=(ref[3]-ref[1])*idle['scale']
    first=data['败北']['frames'][0];b=json.loads((folder/first['file']).with_suffix('.rects.json').read_text(encoding='utf-8'))['bodyBoundingBox']
    before=(b[3]-b[1])*first['scale'];factor=target/before
    for i,f in enumerate(data['败北']['sourceFrames']):
        f['scale']*=factor
        for key in ['headWorld','torsoWorld']:
            if key in f.get('anatomy',{}):f['anatomy'][key]*=factor
        data['败北']['frames'][i],_=fit(f,list(palette),f'latest-defeat-{i}.png')
    data['败北']['displayCalibration']={'method':'uniform action multiplier referenced to upright first pose and idle model','wholeActionMultiplier':factor,'firstUprightHeightBefore':before,'targetIdleHeight':target,'perPoseBboxNormalization':False,'visualAcceptance':False}
    data['败北']['status']='按待机整体体型缩小整组败北；各姿源图比例仍需复核'
    for label,soles in AIR_SOLES.items():
        for i,(f,sole) in enumerate(zip(data[label]['sourceFrames'],soles)):
            f['anchor'][1]=sole[1]
            f['supportPoint']=sole
            data[label]['frames'][i],_=fit(f,list(palette),f'latest-air-{0 if label=="空轻" else 1}-{i}.png')
        data[label]['airHoverWorld']=100
        data[label]['flightPreview']={'peakWorld':160,'jumpTicks':38,'standaloneEntryTick':12,'inheritJump':True,'horizontalMovement':'input-only'}
        data[label]['status']='空攻接续跳跃高度与移动输入；海马上半身嘴位同步喷水，源图比例/残片仍待修'
    hurt=data['受击与倒地'];wake=data['起身']
    for key in ['sourceFrames','frames']:hurt[key][-1]=deepcopy(wake[key][0])
    hurt['phases'][-1]='侧撑 · 复用起身第1帧'
    hurt['status']='倒地终态直接复用起身第1帧；同文件、倍率、锚点，保留原第4帧历史'
    # Victory uses one drawing scale for its new raised-hat and bow poses.
    # Start/end reuse exact canonical idle: no separate small standing model.
    extraction=json.loads((folder/'victory-v2-extraction.json').read_text(encoding='utf-8'))
    victory_scale=target/extraction['calibrationUprightSourceHeight']
    victory_sources=[deepcopy(data['待机']['sourceFrames'][0])]
    victory_fits=[deepcopy(data['待机']['frames'][0])]
    for index,hip in [(1,[211,356]),(2,[251,277])]:
        name=f'victory-v2-source-{index}.png';im=Image.open(folder/name)
        f={'file':name,'source':'victory-curtaincall-source-v2.png','scale':victory_scale,
           'anchor':[hip[0]-33.66/victory_scale,im.height-1],
           'previewOnly':True,'displayRegistration':'shared source drawing scale, calibrated by upright reference; not per-pose bbox height'}
        fitted,_=fit(f,list(palette),f'latest-victory-{index}.png')
        victory_sources.append(f);victory_fits.append(fitted)
    victory_sources.append(deepcopy(data['待机']['sourceFrames'][0]));victory_fits.append(deepcopy(data['待机']['frames'][0]))
    data['胜利'].update(sourceFrames=victory_sources,frames=victory_fits,
        phases=['站定 · 原待机','提帽','谢幕','恢复 · 原待机'],
        status='胜利首尾直接复用待机，中间提帽/鞠躬同绘图倍率；源图与连接待播放复核',
        displayCalibration={'method':'exact idle first/last, shared upright-reference scale for both intermediate poses','sourceScale':victory_scale,'visualAcceptance':False})
    # Only light3 preparation was abnormally large. Its hat-to-boots upright
    # body fits inside the silhouette (the sword does not exceed its height).
    light=data['轻攻三'];first=light['frames'][0]
    box=json.loads((folder/first['file']).with_suffix('.rects.json').read_text(encoding='utf-8'))['bodyBoundingBox']
    light_before=(box[3]-box[1])*first['scale'];light_factor=target/light_before
    light['sourceFrames'][0]['scale']*=light_factor
    light['frames'][0],_=fit(light['sourceFrames'][0],list(palette),'latest-light3-preparation.png')
    light['status']='轻攻三准备帧整体大小对齐待机；其余攻击姿势/人体比例仍待复核'
    from furina_light3_consistency import apply as apply_consistency
    consistency=apply_consistency(data,folder,fit,palette)
    return {'defeatUniformMultiplier':factor,'defeatUprightBefore':before,'defeatTargetIdleHeight':target,
            'airHoverWorld':100,'airRoot':'manual boot sole point; not pelvis virtual floor',
            'hurtLastEqualsWakeupFirst':True,'independentSourceProportionAcceptance':False,
            'victoryFirstLastExactIdle':True,'victoryIntermediateSharedScale':victory_scale,
            'light3FirstHeightBefore':light_before,'light3FirstMultiplier':light_factor,
            'outlineColor':[25,31,79],'outlineWidthLogical':1,'light3ConsistencyTrial':consistency}
