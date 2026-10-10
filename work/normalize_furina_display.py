"""Deterministic scale candidate and independent source-proportion rejection audit.

Does not repaint anatomy, replace active actions, or certify visual acceptance.
"""
from pathlib import Path
import json, math, sys, shutil, hashlib, base64
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
R=Path(__file__).resolve().parents[1]
O=R/'outputs/furina-design-20261010'
sys.path.insert(0,str(R/'game/tools'))
import artlib
CELL=4.5
FONT=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',14)

def canonical_fit(f,palette,name):
    im=Image.open(O/f['file']).convert('RGBA')
    q=f['scale']/CELL
    ax,ay=f['anchor']
    left=math.floor(-ax*q)-1;top=math.floor(-ay*q)-1
    right=math.ceil((im.width-ax)*q)+1;bottom=math.ceil((im.height-ay)*q)+1
    w,h=right-left,bottom-top
    # Uniform affine sampling around the world pivot, not independently rounded
    # X/Y image sizes. Premultiplied alpha avoids dark transparent fringes.
    rgba=np.asarray(im,dtype=float)
    rgba[:,:,:3]*=rgba[:,:,3:4]/255
    pm=Image.fromarray(np.clip(rgba,0,255).astype('uint8'),'RGBA')
    k=4
    sample=pm.transform((w*k,h*k),Image.Transform.AFFINE,
        (1/(q*k),0,ax+left/q,0,1/(q*k),ay+top/q),
        resample=Image.Resampling.BILINEAR).resize((w,h),Image.Resampling.BOX)
    a=np.asarray(sample,dtype=float);alpha=a[:,:,3:4]
    a[:,:,:3]=np.where(alpha>0,a[:,:,:3]*255/np.maximum(1,alpha),0)
    small=Image.fromarray(np.clip(a+.5,0,255).astype('uint8'),'RGBA')
    idx=artlib.apply_palette(small,palette)
    # Restore the established one-cell EXTERNAL contour. Hair/skin are protected
    # by leaving every interior pixel unchanged, not by omitting their perimeter.
    mask=idx>=0
    interior=np.zeros((h,w,4),dtype='uint8')
    for c,color in enumerate(palette):interior[idx==c]=color[:3]+[255]
    body_bbox=Image.fromarray(mask.astype('uint8')*255).getbbox()
    expanded=np.asarray(Image.fromarray(mask.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
    border=expanded&~mask
    dark=[25,31,79]
    if dark not in palette:palette=palette+[dark]
    idx[border]=palette.index(dark)
    rects=artlib.painter(idx)
    target=np.zeros((h,w,4),dtype='uint8');rebuilt=np.zeros_like(target)
    for c,color in enumerate(palette):target[idx==c]=color[:3]+[255]
    for x,y,rw,rh,c in rects:rebuilt[y:y+rh,x:x+rw]=palette[c][:3]+[255]
    assert np.array_equal(target,rebuilt)
    Image.fromarray(rebuilt).save(O/name)
    result={key:value for key,value in f.items() if key not in ['scaleX','scaleY']}
    result.update(file=name,anchor=[-left,-top],scale=CELL)
    (O/Path(name).with_suffix('.rects.json')).write_text(json.dumps({
        'palette':palette,'rects':rects,'anchor':result['anchor'],'scale':CELL,
        'outline':'external one logical cell, complete navy perimeter; interior unchanged','outlineColor':dark,'outlineWidth':1,
        'bodyBoundingBox':body_bbox,'bodyMaskShape':[h,w],
        'bodyMaskBits':base64.b64encode(np.packbits(mask).tobytes()).decode('ascii'),
        'interiorRgbaSha256':hashlib.sha256(interior.tobytes()).hexdigest(),'source':f['file'],
        'runtimeIntegrated':False,'reconstruction':'exact quantized pixels',
        'sampling':'uniform premultiplied affine, 4x supersample'},ensure_ascii=False),encoding='utf-8')
    return result,len(rects)

def main():
    cfg=json.loads((R/'work/furina_scale_registration.json').read_text(encoding='utf-8'))
    extra=json.loads((O/'missing-action-landmarks.json').read_text(encoding='utf-8'))
    feedback=json.loads((R/'work/furina_scale_feedback_registration.json').read_text(encoding='utf-8'))
    data=json.loads((O/'actions.json').read_text(encoding='utf-8'))
    source_snapshot=json.loads(json.dumps(data))
    marks=cfg['actions']
    marks.update(feedback['actions'])
    for key,label in [('forwarddash','前冲'),('backdash','后撤'),('jump','跳跃'),('defeat','败北')]:
        rows=extra[key]
        if key in ['forwarddash','backdash']:rows=[marks['待机'][0]]+rows+[marks['待机'][0]]
        marks[label]=rows
    mother=data['待机']['sourceFrames'][0]
    head=math.dist(*marks['待机'][0]['head'])*mother['scale']
    torso=math.dist(*marks['待机'][0]['torso'])*mother['scale']
    legs=[sum(math.dist(a,b) for a,b in zip(chain,chain[1:]))*mother['scale'] for chain in cfg['motherLegs']]
    palette=json.loads((R/'work/v4-handoff-20261009-partial/V4/evidence/furina-idle-review/fit.json').read_text(encoding='utf-8'))['palette']
    report={'activeBankSha256':hashlib.sha256((O/'actions.json').read_bytes()).hexdigest(),'targetHeadWorld':head,'targetTorsoWorld':torso,'targetLegChainsWorld':legs,
        'logicalCellWorld':CELL,'landmarkPolicy':cfg['policy'],'sourceFrames':[],
        'unmeasuredActions':[],'sourceArtFailures':[],'simulation':'not run',
        'device':'not observed','visualAcceptance':'not accepted','activeBankReplaced':False}
    count=0;peak=0
    anchor_changes=[]
    for ai,(label,d) in enumerate(data.items()):
        rows=marks.get(label)
        if not rows:report['unmeasuredActions'].append(label)
        for i,f in enumerate(d['sourceFrames']):
            old=f['scale'];entry={'action':label,'frame':i,'file':f['file'],'oldScale':old}
            if rows:
                m=rows[i];length=math.dist(*m['head']);f['scale']=head/length
                tw=math.dist(*m['torso'])*f['scale'];delta=tw/torso-1
                oldhead=length*old
                failed=abs(delta)>cfg['torsoTolerance']
                entry.update(oldHeadWorld=oldhead,headWorld=length*f['scale'],
                    torsoWorld=tw,torsoDeviation=delta,sourceProportionPass=not failed,
                    sourceNeedsReview=failed,landmarkConfidence='manual estimate; not art acceptance')
                if m.get('legs'):
                    # Same measurement definition as mother: hip -> knee -> ankle;
                    # optional fourth boot-tip point must not inflate leg length.
                    lw=[sum(math.dist(a,b) for a,b in zip(chain[:3],chain[1:3]))*f['scale'] for chain in m['legs']]
                    entry['legChainsWorld']=lw
                    entry['legDeviation']=[v/ref-1 for v,ref in zip(lw,legs)]
                    if any(abs(x)>.10 for x in entry['legDeviation']):entry['sourceNeedsReview']=True
                if entry['sourceNeedsReview']:report['sourceArtFailures'].append({'action':label,'frame':i,'reason':'anatomical proportions cannot be aligned by the chosen single head scale','torsoDeviation':delta,'legDeviation':entry.get('legDeviation')})
                entry['userRejected']=label in feedback['userRejectedActions']
                previous_anchor=list(f['anchor'])
                # Explicit anatomical root, independent of silhouette or weapon.
                if label in ['空轻','空重'] or (label=='被投' and i in [1,2,3]):
                    hip=m['torso'][1]
                    f['anchor']=[hip[0]-extra['mother']['hipOffsetWorldX']/f['scale'],hip[1]+extra['mother']['hipHeightWorld']/f['scale']]
                elif label in feedback['userRejectedActions']:
                    f['anchor'][0]=m['torso'][1][0]-extra['mother']['hipOffsetWorldX']/f['scale']
                if previous_anchor!=f['anchor']:
                    anchor_changes.append({'action':label,'frame':i,'old':previous_anchor,'new':list(f['anchor']),'status':'candidate; paired contact not accepted'})
                f['anatomy']={'headPoints':m['head'],'torsoPoints':m['torso'],
                    'headWorld':head,'torsoWorld':tw,'sourceNeedsReview':entry['sourceNeedsReview'],
                    'userRejected':entry['userRejected']}
                if d.get('effects',{}).get('nozzles'):
                    d['effects']['nozzles'][i]=[v*f['scale']/old for v in d['effects']['nozzles'][i]]
                count+=1
            else:entry['sourceNeedsReview']=True;entry['reason']='unmeasured, retained legacy scale; not normalized'
            usepal=list(palette)
            if d.get('heldCompanion'):
                for key in ['chevalmarin','crabaletta']:
                    extra_palette=json.loads((R/f'work/v4-handoff-20261009-partial/V4/evidence/furina-salon-side-v3/{key}/fit.json').read_text(encoding='utf-8'))['palette']
                    for c in extra_palette:
                        if c[:3] not in usepal:usepal.append(c[:3])
            fit,n=canonical_fit(f,usepal,f'unified-size-{ai}-{i}.png')
            d['frames'][i]=fit;entry['newScale']=f['scale'];entry['rectangles']=n
            report['sourceFrames'].append(entry);peak=max(peak,n)
        d['displayCalibration']={'method':'single skull scale; independent torso rejection check' if rows else 'canonical grid only; anatomy not measured','targetHeadWorld':head,'targetTorsoWorld':torso,'bboxNormalization':False,'worldCell':CELL,'candidateOnly':True}
        d['status']='尺度检查候选：'+('头尺度已登记；比例冲突姿势见失败清单，未验收' if rows else '统一拟合网格；解剖尺度尚未逐姿登记')
    # Latest user feedback puts air-heavy proportions in scope; art files stay
    # untouched, but display scale/fitting is now registered like other actions.
    assert [f['file'] for f in source_snapshot['空重']['sourceFrames']]==[f['file'] for f in data['空重']['sourceFrames']]
    # First/last dash idle must remain exactly the same object data as idle.
    for label in ['前冲','后撤']:
        for key in ['sourceFrames','frames']:
            data[label][key][0]=dict(data['待机'][key][0]);data[label][key][-1]=dict(data['待机'][key][0])
    from furina_latest_display_fixes import apply as apply_latest
    report['latestUserChanges']=apply_latest(data,O,canonical_fit,palette)
    report['sourceAuditScope']='Source landmark audit before latest display overrides; not final acceptance of replacement victory poses or corrected attack scale.'
    report.update(registeredDisplayFrames=count,sourceProportionFailures=len(report['sourceArtFailures']),peakRectangles=peak,
        userRejectedActions=feedback['userRejectedActions'],anchorChanges=anchor_changes,
        hurtFourthFrame=feedback['hurtFourthFrame'])
    (O/'actions-size-candidate.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    (O/'uniform-size-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # Same-world contact strips include baseline idle, never shrink frames to fit.
    for label in marks:
        for mode,field in [('source','sourceFrames'),('fit','frames')]:
            fs=[data['待机'][field][0]]+data[label][field]
            sheet=Image.new('RGBA',(len(fs)*320,470),'#777780');draw=ImageDraw.Draw(sheet)
            for i,f in enumerate(fs):
                im=Image.open(O/f['file']).convert('RGBA');s=f['scale']
                resized=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST)
                sheet.alpha_composite(resized,(i*320+130-round(f['anchor'][0]*s),425-round(f['anchor'][1]*s)))
                draw.text((i*320+5,5),'待机基准' if i==0 else f'{label} {i-1}',font=FONT,fill='white')
                if i and label in feedback['userRejectedActions']:draw.text((i*320+5,26),'用户指出比例待修',font=FONT,fill='#ffcccc')
                elif i and any(x['action']==label and x['frame']==i-1 for x in report['sourceArtFailures']):draw.text((i*320+5,26),'源图比例待修',font=FONT,fill='#ffcccc')
            draw.line((0,425,sheet.width,425),fill='white')
            sheet.convert('RGB').save(O/f'uniform-{list(marks).index(label)}-{mode}.jpg')
    revision=hashlib.sha256((O/'actions-size-candidate.json').read_bytes()+(R/'work/furina_air_preview.js').read_bytes()+(R/'work/furina_review_app.js').read_bytes()).hexdigest()[:12]
    app=(R/'work/furina_review_app.js').read_text(encoding='utf-8').replace('actions.json?v=repair20261011','actions-size-candidate.json?v='+revision)
    app=app.replace('y=360-75*Math.sin(t*Math.PI);','y=550-(d.airHoverWorld||100);')
    app+='\nconst scaleAuditRender=render;render=function(){scaleAuditRender();const f=frames[phase()],a=f?.anatomy;if(a?.userRejected)$("note").textContent="用户已指出比例不对：只修正显示参数，不代表源图比例通过。";if(selected==="受击与倒地"&&phase()===3)$("note").textContent="倒地最后一帧已按明确要求复用起身第1帧：同图、同倍率、同锚点。"};\n'
    app+='\n'+(R/'work/furina_air_preview.js').read_text(encoding='utf-8')
    (O/'size-review-app.js').write_text(app,encoding='utf-8')
    html=(O/'index.html').read_text(encoding='utf-8').replace('app.js?v=repair20261011','size-review-app.js?v='+revision).replace('<title>','<title>尺度检查候选 · ')
    html=html.replace('#note,#pair{display:none}', '#note,#pair{display:block}')
    html=html.replace('<div id="error"','<p>轻攻三局部试修：回收帧按头/躯干/两腿共同约束等比校准；恢复帧单张返修。<a href="light3-consistency-review.html" target="_blank">六帧前后对照与测量</a>；中段未自动缩放，整体待验收。</p><div id="error"')
    html=html.replace('<div id="error"','<p>空中检查：参考雷神峰值160、38拍曲线，映射芙芙原32拍跳跃；空攻继承高度及曲线进度。无自动横移，播放时用←/→或A/D移动。海马嘴位跟随上半身，喷水仅在有效段同步发出。独立点选空攻从参考曲线第12拍开始，非正式战斗验证。</p><div id="error"')
    html=html.replace('<div id="error"', '<p style="color:#ffcf7b">最新修正：完整深蓝1格外描边；胜利首尾同待机，中间共用倍率；轻攻三首帧已缩小。保留倒地复用、败北缩放与空中高度修正。其余人体比例未验收。<a href="raiden-comparison.html" target="_blank">同动作雷神对照</a> · <a href="outline-size-white-review.png" target="_blank">白底</a> · <a href="outline-size-dark-review.png" target="_blank">深底</a></p><div id="error"')
    (O/'size-review.html').write_text(html,encoding='utf-8')
    served=R/'work/github-review-20261009/V3/assets/action-reference/furina'
    for p in O.iterdir():
        if served.is_dir() and p.name.startswith(('unified-size-','uniform-','latest-','actions-size-candidate','size-review','light3-consistency','light3-recovery')):shutil.copy2(p,served/p.name)
    print(json.dumps({k:report[k] for k in ['registeredDisplayFrames','sourceProportionFailures','peakRectangles','latestUserChanges']},ensure_ascii=False))

if __name__=='__main__':main()
