"""Import latest reviewed fitted pixels and anchors; never regenerate artwork."""
from pathlib import Path
import base64,hashlib,json,struct,re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runtime'
ASSETS=ROOT/'outputs/furina-design-20261010'
GROUPS={'待机':'idle','站重':'heavy','轻攻一':'light1','轻攻二':'light2','轻攻三':'light3',
 '蹲轻':'crouchLight','蹲重':'crouchHeavy','空轻':'airLight','空重':'airHeavy','站立格挡':'block',
 '蹲防':'cblock','E · 孤心沙龙':'skill','Q · 万众狂欢':'burst','投技':'throw','被投':'thrown',
 '前走':'walk','后退':'back','跳跃':'jump','蹲下':'crouch','受击与倒地':'hurt','起身':'getup',
 '胜利':'win','前冲':'dash','后撤':'backdash','败北':'lose'}
def lua(v):
    if v is None:return 'nil'
    if isinstance(v,bool):return 'true' if v else 'false'
    if isinstance(v,str):return json.dumps(v,ensure_ascii=False)
    if isinstance(v,(int,float)):return repr(v)
    if isinstance(v,list):return '{'+','.join(lua(x) for x in v)+'}'
    return '{'+','.join('['+lua(k)+']='+lua(x) for k,x in v.items())+'}'
def export():
    assert 'size-review-app.js' in (ASSETS/'size-review.html').read_text(encoding='utf-8')
    assert 'actions-size-candidate.json' in (ASSETS/'size-review-app.js').read_text(encoding='utf-8')
    bank=json.loads((ASSETS/'actions-size-candidate.json').read_text(encoding='utf-8'))
    frames={};groups={};sources=[];dedup={}
    for label,id in GROUPS.items():
        group=bank[label];seq=[]
        for i,f in enumerate(group['frames']):
            image=ASSETS/f['file'];meta=image.with_suffix('.rects.json')
            data=json.loads(meta.read_text(encoding='utf-8'))
            w,h=struct.unpack('>II',image.read_bytes()[16:24])
            rects=data['rects'];ax,ay=f['anchor']
            if f.get('facingCorrection',1)==-1:
                rects=[[w-x-rw,y,rw,rh,c] for x,y,rw,rh,c in rects];ax=w-ax
            raw=struct.pack('<'+'H'*len(rects)*5,*(v for r in rects for v in r))
            pal=[c[:3]+[255] for c in data['palette']]
            packed=raw+b'\0'*((-len(raw))%3)  # Existing decoder uses complete unpadded quartets.
            img={'n':len(rects),'d':base64.b64encode(packed).decode(),'pal':pal,'ax':ax,'ay':ay,'u':f['scale'],
                 'ux':f.get('scaleX',f['scale']),'uy':f.get('scaleY',f['scale']),'w':w,'h':h}
            identity=hashlib.sha256(json.dumps(img,sort_keys=True).encode()).hexdigest()
            pose=dedup.get(identity,f'{id}_{i}')
            if identity not in dedup: frames[pose]=img;dedup[identity]=pose
            seq.append(pose)
            sources.append({'group':id,'frame':i,'pose':pose,'file':image.relative_to(ROOT).as_posix(),
                'rectsFile':meta.relative_to(ROOT).as_posix(),'imageSha256':hashlib.sha256(image.read_bytes()).hexdigest(),
                'rectsSha256':hashlib.sha256(meta.read_bytes()).hexdigest(),'anchor':f['anchor'],'scale':f['scale'],
                'scaleX':f.get('scaleX',f['scale']),'scaleY':f.get('scaleY',f['scale']),
                'facingCorrection':f.get('facingCorrection',1),'anatomy':f.get('anatomy',{})})
        groups[id]={'frames':seq,'durations':group['durations']}
        for field in ['motion','cinematic','swordMarkers','sourceFrames']:
            if field in group:groups[id][field]=group[field]
        if group.get('combatDesign'):
            groups[id]['combat']=group['combatDesign']
    body_count=len(frames);body_sources=len(sources);body_peak=max(v['n'] for v in frames.values())
    def extra_frame(f,pose):
        image=ASSETS/f['file'];meta=image.with_suffix('.rects.json')
        if not meta.exists():meta=image.with_name(image.stem.replace('-fit','')+'-rects.json')
        data=json.loads(meta.read_text(encoding='utf-8'));w,h=struct.unpack('>II',image.read_bytes()[16:24])
        rects=data['rects'];raw=struct.pack('<'+'H'*len(rects)*5,*(v for r in rects for v in r));raw+=b'\0'*((-len(raw))%3)
        frames[pose]={'n':len(rects),'d':base64.b64encode(raw).decode(),'pal':[c[:3]+[c[3] if len(c)>3 else 255] for c in data['palette']],
          'ax':f['anchor'][0],'ay':f['anchor'][1],'u':f['scale'],'ux':f.get('scaleX',f['scale']),'uy':f.get('scaleY',f['scale']),'w':w,'h':h}
        sources.append({'group':'auxiliary','pose':pose,'file':image.relative_to(ROOT).as_posix(),'rectsFile':meta.relative_to(ROOT).as_posix(),
          'imageSha256':hashlib.sha256(image.read_bytes()).hexdigest(),'rectsSha256':hashlib.sha256(meta.read_bytes()).hexdigest(),
          'anchor':f['anchor'],'scale':f['scale'],'scaleX':f.get('scaleX',f['scale']),'scaleY':f.get('scaleY',f['scale']),'facingCorrection':1})
        return pose
    for label,id in GROUPS.items():
        effect=bank[label].get('effects')
        if effect:
            groups[id]['effects']={k:v for k,v in effect.items() if k not in ['frames','fitFrames','sourceFrames']}
            groups[id]['effects']['frames']=[extra_frame(f,'fx_'+id+'_'+str(i)) for i,f in enumerate(effect.get('fitFrames',effect['frames']))]
    helpers=json.loads((ASSETS/'helpers.json').read_text(encoding='utf-8'))
    helper_data={}
    mouths=[[390,250],[410,249],[393,278],[390,250]]
    for key,h in helpers.items():
        helper_data[key]={'frames':[extra_frame(f,'helper_'+key+'_'+str(i)) for i,f in enumerate(h['fitFrames'])]}
        if key=='chevalmarin':
            helper_data[key]['mouths']=[[(q[j]-f['anchor'][j])*f['scale'] for j in range(2)] for q,f in zip(mouths,h['sourceFrames'])]
    # The air-light ribbon is procedural in the delivered page. Rasterize that same
    # quadratic path, rather than reusing an unrelated sword-effect bitmap.
    import sys,math
    sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
    from PIL import Image,ImageDraw
    derived=OUT/'derived-furina';derived.mkdir(exist_ok=True);trails={}
    air=bank['空轻']
    def point(i,key):
        f=air['sourceFrames'][i];q=air['swordMarkers'][i][key]
        return tuple((q[j]-f['anchor'][j])*f['scale'] for j in range(2))
    def bezier(a,b,c):
        return [tuple((1-u)**2*a[j]+2*(1-u)*u*b[j]+u*u*c[j] for j in range(2)) for u in [i/48 for i in range(49)]]
    for i in [2,3]:
        hand,tip,prev=point(i,'wrist'),point(i,'tip'),point(max(0,i-1),'tip')
        ribbon=[hand]+bezier(hand,prev,tip)+[(hand[0]+3,hand[1]+3)]
        line=bezier(prev,((prev[0]+tip[0])/2+10,(prev[1]+tip[1])/2),tip)
        points=ribbon+line;x0=math.floor(min(p[0] for p in points))-3;y0=math.floor(min(p[1] for p in points))-3
        w=math.ceil(max(p[0] for p in points))-x0+4;h=math.ceil(max(p[1] for p in points))-y0+4
        im=Image.new('RGBA',(w,h));draw=ImageDraw.Draw(im)
        draw.polygon([(x-x0,y-y0) for x,y in ribbon],fill=(128,221,248,255));draw.line([(x-x0,y-y0) for x,y in line],fill=(226,250,255,255),width=2)
        file=derived/f'air-trail-{i}.png';im.save(file)
        palette=[[128,221,248,255],[226,250,255,255]];rects=[];previous={}
        for y in range(h):
            runs={};x=0
            while x<w:
                color=im.getpixel((x,y))
                if not color[3]:x+=1;continue
                end=x+1
                while end<w and im.getpixel((end,y))==color:end+=1
                key=(x,end-x,palette.index(list(color)))
                if key in previous:idx=previous[key];rects[idx][3]+=1
                else:idx=len(rects);rects.append([x,y,end-x,1,key[2]])
                runs[key]=idx;x=end
            previous=runs
        file.with_suffix('.rects.json').write_text(json.dumps({'palette':palette,'rects':rects}),encoding='utf-8')
        trails[str(i+1)]=extra_frame({'file':'../../runtime/derived-furina/'+file.name,'anchor':[-x0,-y0],'scale':1},'airTrail_'+str(i+1))
    image=ASSETS/'ultimate-portrait-fit.png';w,h=struct.unpack('>II',image.read_bytes()[16:24])
    portrait=extra_frame({'file':image.name,'anchor':[0,0],'scale':310/h},'ultimatePortrait')
    aliases={id:g['frames'][0] for id,g in groups.items()}
    aliases.update(walk1=groups['walk']['frames'][0],walk2=groups['walk']['frames'][2],
        guard=groups['block']['frames'][2],crouchGuard=groups['cblock']['frames'][2],
        slash=groups['light1']['frames'][2],special=groups['skill']['frames'][2],
        qRelease=groups['burst']['frames'][2],down=groups['hurt']['frames'][3])
    data={'frames':frames,'groups':groups,'aliases':aliases,'bodyPeak':body_peak,'helpers':helper_data,'portrait':portrait,'trails':trails,
      'auxPeak':max(v['n'] for k,v in frames.items() if k.startswith(('fx_','helper_'))),
      'version':{'page':'size-review.html','bank':'actions-size-candidate.json','script':'size-review-app.js',
        'bankSha256':hashlib.sha256((ASSETS/'actions-size-candidate.json').read_bytes()).hexdigest(),
        'scriptSha256':hashlib.sha256((ASSETS/'size-review-app.js').read_bytes()).hexdigest()}}
    (OUT/'source/assets/gf_furina_data.lua').write_text("__loaders['gf_furina_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
    rules={id:{k:v for k,v in g.items() if k in ['durations','combat','cinematic']} for id,g in groups.items()}
    import math
    rules['flightHeights']=[round(16000*math.sin(math.pi*t/32)) for t in range(33)]
    rules['throwRoots']=[];rules['burstRoots']=[]
    for t in range(73):
        x,y=140,0
        if 20<=t<30:x=140-15*(t-20)/10
        elif 30<=t<38:
            u=(t-30)/8;x=125+200*u;y=100*math.sin(u*math.pi/2)
        elif 38<=t<50:
            u=(t-38)/12;x=325+60*u;y=100*(1-u)
        elif t>=50:x=385
        rules['throwRoots'].append([math.floor(x*100),math.floor(y*100)])
    for t in range(159):
        x,y=380,0
        if 56<=t<122:x=380+math.sin(t*.4)*4;y=100+math.sin(t*.2)*12
        elif t>=122:
            u=min(1,(t-122)/36);x=380+100*u;y=100*(1-u)
        rules['burstRoots'].append([math.floor(x*100),math.floor(y*100)])
    (OUT/'source/characters/gf_furina_rules_data.lua').write_text("__loaders['gf_furina_rules_data']=function() return "+lua(rules)+' end\n',encoding='utf-8')
    # Preserve established face/round/portrait assets; body comes only from latest bank.
    legacy=(ROOT/'game/lua/gen/gf_art_furina.lua').read_text(encoding='utf-8')
    pictures=re.findall(r'^(?:face|round|portrait)=\{[^\n]+\},$',legacy,re.M)
    assert len(pictures)==3,'legacy picture layout changed'
    (OUT/'source/assets/gf_art_furina.lua').write_text("__loaders['gf_art_furina']=function()\nreturn {\n"+'\n'.join(pictures)+'\n}\nend\n',encoding='utf-8')
    receipt={'candidate':True,'visualAccepted':False,'nativeDeviceTested':False,
      'bodyGroups':len(groups),'displayStates':body_sources,'uniqueBodyFrames':body_count,'auxiliaryStates':len(sources)-body_sources,'bodyPeak':data['bodyPeak'],
      'codec':'existing base64 / uint16 rectangle layout; no additional compression',
      'rules':'delivered attack timings, salon E, confirmed Q 12/56/78/100/158, paired throw 30/50/72; existing damage and combat systems adapted',
      'pending':['visual approval','device budget','Q miss and block branches are runtime adaptations because delivery only specifies confirmed branch'],
      'version':data['version'],'bankSha256':data['version']['bankSha256'],'sources':sources}
    (OUT/'furina-import.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['sources','pending']},ensure_ascii=False))
if __name__=='__main__':export()
