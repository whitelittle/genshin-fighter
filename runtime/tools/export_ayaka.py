"""Import the Ayaka delivery page's exact frames, transforms and event metadata."""
from pathlib import Path
import base64,hashlib,json,math,re,struct
from export_furina import lua,GROUPS
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runtime'
ASSETS=ROOT/'outputs/v4-one-character-20261010/ayaka-armed-v2'
def export():
    mapping={**GROUPS};del mapping['E · 孤心沙龙'];del mapping['Q · 万众狂欢']
    mapping.update({'E · 冰华':'skill','Q · 霜灭':'burst'})
    bank=json.loads((ASSETS/'actions.json').read_text(encoding='utf-8'))
    assert 'actions.json' in (ASSETS/'app.js').read_text(encoding='utf-8')
    frames={};sources=[];groups={};dedup={}
    def image(f,id,group):
        path=ASSETS/f['file'];meta=path.with_suffix('.rects.json')
        if not meta.exists():meta=path.with_name(path.stem+'-rects.json')
        data=json.loads(meta.read_text(encoding='utf-8'));w,h=struct.unpack('>II',path.read_bytes()[16:24]);rects=data['rects']
        raw=struct.pack('<'+'H'*(len(rects)*5),*(v for r in rects for v in r));raw+=b'\0'*((-len(raw))%3)
        img={'n':len(rects),'d':base64.b64encode(raw).decode(),'pal':[c[:3]+[c[3] if len(c)>3 else 255] for c in data['palette']],
          'ax':f['anchor'][0],'ay':f['anchor'][1],'u':f['scale'],'ux':f['scale'],'uy':f['scale'],'w':w,'h':h}
        identity=hashlib.sha256(json.dumps(img,sort_keys=True).encode()).hexdigest();pose=dedup.get(identity,id)
        if identity not in dedup:frames[pose]=img;dedup[identity]=pose
        sources.append({'group':group,'pose':pose,'file':path.relative_to(ROOT).as_posix(),'rectsFile':meta.relative_to(ROOT).as_posix(),
          'imageSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rectsSha256':hashlib.sha256(meta.read_bytes()).hexdigest(),
          'anchor':f['anchor'],'scale':f['scale'],'scaleX':img['ux'],'scaleY':img['uy'],'facingCorrection':1})
        return pose
    for label,id in mapping.items():
        g=bank[label];groups[id]={'frames':[image(f,id+'_'+str(i),id) for i,f in enumerate(g['frames'])],'durations':g['durations']}
        for src,dst in [('combatDesign','combat'),('cinematic','cinematic')]:
            if src in g:groups[id][dst]=g[src]
    body_count=len(frames);body_states=len(sources);peak=max(f['n'] for f in frames.values())
    for label,id in mapping.items():
        e=bank[label].get('effects')
        if e:
            groups[id]['effects']={k:v for k,v in e.items() if k not in ['frames','sourceFrames','fitFrames']}
            groups[id]['effects']['frames']=[image(f,'fx_'+id+'_'+str(i),'auxiliary') for i,f in enumerate(e['fitFrames'])]
    path=ASSETS/'ultimate-portrait-fit.png';w,h=struct.unpack('>II',path.read_bytes()[16:24])
    portrait=image({'file':path.name,'anchor':[0,0],'scale':310/h},'ultimatePortrait','portrait')
    aliases={id:g['frames'][0] for id,g in groups.items()}
    aliases.update(walk1=groups['walk']['frames'][0],walk2=groups['walk']['frames'][2],guard=groups['block']['frames'][1],
      crouchGuard=groups['cblock']['frames'][1],slash=groups['light1']['frames'][2],special=groups['skill']['frames'][2],
      qRelease=groups['burst']['frames'][3],down=groups['hurt']['frames'][3])
    version={'page':'index.html','bank':'actions.json','script':'app.js'}
    for k in ['bank','script']:version[k+'Sha256']=hashlib.sha256((ASSETS/version[k]).read_bytes()).hexdigest()
    data={'frames':frames,'groups':groups,'aliases':aliases,'bodyPeak':peak,'auxPeak':max(f['n'] for id,f in frames.items() if id.startswith('fx_')),'portrait':portrait,'version':version}
    (OUT/'source/assets/gf_ayaka_data.lua').write_text("__loaders['gf_ayaka_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
    rules={id:{k:v for k,v in g.items() if k in ['durations','combat','cinematic']} for id,g in groups.items()}
    roots=[];ends=[];n=0
    for d in groups['throw']['durations']:n+=d;ends.append(n)
    for t in range(n+1):
        phase=next((i for i,end in enumerate(ends) if t<end),5);start=0 if phase==0 else ends[phase-1];u=min(1,(t-start)/groups['throw']['durations'][phase]);x,y=145,0
        if phase==1:y=180*u
        elif phase==2:y=220
        elif phase==3:x+=35*u;y=220*(1-u)
        elif phase>=4:x=180
        roots.append([math.floor(x*100),math.floor(y*100)])
    rules['throwRoots']=roots;rules['burstRoots']=[]
    for t in range(153):
        x,y=380,0
        if 52<=t<132:x+=math.sin(t*.3)*4;y=105+math.sin(t*.14)*14
        elif t>=132:u=min(1,(t-132)/20);x+=100*u;y=105*(1-u)
        rules['burstRoots'].append([math.floor(x*100),math.floor(y*100)])
    (OUT/'source/characters/gf_ayaka_rules_data.lua').write_text("__loaders['gf_ayaka_rules_data']=function() return "+lua(rules)+' end\n',encoding='utf-8')
    legacy=(ROOT/'game/lua/gen/gf_art_kamisatoayaka.lua').read_text(encoding='utf-8')
    pictures=re.findall(r'^(?:face|round|portrait)=\{[^\n]+\},$',legacy,re.M);assert len(pictures)==3
    (OUT/'source/assets/gf_art_kamisatoayaka.lua').write_text("__loaders['gf_art_kamisatoayaka']=function() return {\n"+'\n'.join(pictures)+'\n} end\n',encoding='utf-8')
    receipt={'version':version,'bodyGroups':len(groups),'displayStates':body_states,'uniqueBodyFrames':body_count,'bodyPeak':peak,
      'auxiliaryStates':len(sources)-body_states,'sources':sources,'nativeDeviceTested':False,
      'adaptations':['damage and cancellation use existing combat system','Q confirmation at release 52; miss/block short recovery','movement follows existing game physics','radial gradient uses native UI ellipses']}
    (OUT/'ayaka-import.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ['sources','adaptations']},ensure_ascii=False))
if __name__=='__main__':export()
