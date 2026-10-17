"""Isolated native-UI training candidate; retain reviewed/rejected source boards."""
from pathlib import Path
import sys,json,base64,struct,hashlib,shutil
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'game/tools'))
from artlib import build_palette,apply_palette,painter,render
from export_furina import lua
OUT=ROOT/'outputs/lumine-training-20261015'
SRC=ROOT/'outputs/lumine-basic-20261015/source'

def components(mask):
    # Run connectivity, rather than equal-width cutting of nonuniform sprite sheets.
    parent=[];bounds=[];areas=[];previous=[]
    def find(i):
        while parent[i]!=i: parent[i]=parent[parent[i]];i=parent[i]
        return i
    for y,row in enumerate(mask):
        edges=np.diff(np.r_[False,row,False].astype(np.int8));starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
        current=[]
        for x0,x1 in zip(starts,ends):
            links=[find(i) for a,b,i in previous if a<=x1 and b>=x0]
            if links:
                i=links[0]
                for j in links[1:]:
                    j=find(j);i=find(i)
                    if i!=j:
                        parent[j]=i
                        a,b,c,d=bounds[j];p,q,r,s=bounds[i];bounds[i]=[min(a,p),min(b,q),max(c,r),max(d,s)];areas[i]+=areas[j]
                p,q,r,s=bounds[i];bounds[i]=[min(p,int(x0)),min(q,y),max(r,int(x1)),max(s,y+1)];areas[i]+=int(x1-x0)
            else:
                i=len(parent);parent.append(i);bounds.append([int(x0),y,int(x1),y+1]);areas.append(int(x1-x0))
            current.append((int(x0),int(x1),i))
        previous=current
    return sorted([(areas[i],bounds[i]) for i in range(len(parent)) if find(i)==i],reverse=True)

def sheet(file,count,cols,standing):
    im=Image.open(file).convert('RGBA');a=np.asarray(im);comps=components(a[:,:,3]>=128)
    bodies=comps[:count]
    assert len(bodies)==count and min(n for n,b in bodies)>1000,(file,bodies)
    # Main connected silhouettes determine each ownership ROI; use layout only for order.
    bodies.sort(key=lambda t:(round((t[1][1]+t[1][3])/2/(im.height/(count/cols))-.5),t[1][0]))
    result=[]
    for n,b in bodies:
        x0,y0,x1,y1=b
        # Include nearby detached details, but never steal a neighbouring whole body.
        for area,q in comps[count:]:
            if area<5:continue
            cx=(q[0]+q[2])/2;cy=(q[1]+q[3])/2
            if x0-5<=cx<=x1+5 and y0-5<=cy<=y1+5:
                x0=min(x0,q[0]);y0=min(y0,q[1]);x1=max(x1,q[2]);y1=max(y1,q[3])
        roi=im.crop((x0,y0,x1,y1));factor=80/standing
        roi=roi.resize((max(1,round(roi.width*factor)),max(1,round(roi.height*factor))),Image.Resampling.NEAREST)
        result.append((roi,{'source':file.relative_to(ROOT).as_posix(),'roi':[x0,y0,x1,y1],'sourceUnit':factor,'alphaComponentArea':n}))
    return result

def encode(im,pal,u,anchor=None):
    idx=apply_palette(im,pal);rects=painter(idx)
    target=render(rects,pal,im.width,im.height)
    expected=np.zeros((im.height,im.width,4),dtype=np.uint8)
    for i,c in enumerate(pal):expected[idx==i]=list(c[:3])+[255]
    assert np.array_equal(np.asarray(target),expected)
    if anchor is None:
        ys,xs=np.nonzero(idx>=0);bottom=int(ys.max()+1);feet=xs[ys>=bottom-5]
        anchor=[float(np.median(feet)),bottom]
    raw=struct.pack('<'+'H'*(len(rects)*5),*(v for r in rects for v in r));raw+=b'\0'*((-len(raw))%3)
    return {'n':len(rects),'d':base64.b64encode(raw).decode(),'pal':[list(c[:3])+[255] for c in pal],'ax':anchor[0],'ay':anchor[1],'u':u,'w':im.width,'h':im.height},target

def export():
    (OUT/'source').mkdir(parents=True,exist_ok=True);(OUT/'fit').mkdir(exist_ok=True)
    generated=Path.home()/'.codex/generated_images/01a13b51-6873-7302-b0af-bbcbe55958f7/exec-beeed6ab-99e9-4d16-8d0e-e0bf6fb6fce2.png'
    shutil.copy2(generated,OUT/'source/light-test-v1.png')
    recipes=[('idle','idle-v1.png',2,2,840),('walk','walk-forward-v1.png',6,3,473),('back','walk-back-v2.png',6,3,473),('block','guard-standing-v1.png',4,4,570),('cblock','guard-crouch-v1.png',4,4,570),('jump','jump-v1.png',6,3,473),('backdash','backstep-v1.png',4,4,570),('light1',None,4,2,480)]
    raw={};meta={}
    for group,name,count,cols,standing in recipes:
        pairs=sheet(SRC/name if name else OUT/'source/light-test-v1.png',count,cols,standing)
        for i,(im,m) in enumerate(pairs):raw[f'{group}_{i}']=im;meta[f'{group}_{i}']=m
    pal=build_palette(list(raw.values()),16,seed=21)
    frames={};groups={}
    durations={'idle':[35,35],'walk':[7]*6,'back':[8]*6,'block':[4]*4,'cblock':[4]*4,'jump':[4,3,10,8,12,4],'backdash':[4,4,5,5],'light1':[10,4,8,8]}
    for id,im in raw.items():
        frames[id],target=encode(im,pal,320/80)
        target.save(OUT/'fit'/f'lumine-{id}.png')
        group=id.rsplit('_',1)[0];groups.setdefault(group,{'frames':[],'durations':durations[group]})['frames'].append(id)
    groups['dash']={'frames':groups['walk']['frames'],'durations':[2]*6} # explicit locomotion placeholder; rejected dash sheet excluded
    groups['crouch']={'frames':['cblock_0'],'durations':[8]}
    aliases={k:g['frames'][0] for k,g in groups.items()};aliases.update(walk1='walk_0',walk2='walk_2',guard='block_1',crouchGuard='cblock_1',slash='light1_1',special='idle_0',qRelease='idle_0',hurt='idle_0',down='idle_0')
    def icons(source):
        # Standalone face data for existing HUD, never substitute another character portrait.
        a=np.asarray(source);mask=a[:,:,3]>127;ys,xs=np.nonzero(mask);x0,x1=xs.min(),xs.max();y0=ys.min()
        head=source.crop((x0,y0,x1+1,min(source.height,y0+int((ys.max()-y0)*.36))))
        head.thumbnail((32,32),Image.Resampling.NEAREST);canvas=Image.new('RGBA',(34,34));canvas.alpha_composite(head,((34-head.width)//2,(34-head.height)//2))
        data,_=encode(canvas,build_palette([canvas],16,seed=21),1,anchor=[17,34]);return data
    data={'frames':frames,'groups':groups,'aliases':aliases,'bodyPeak':max(x['n'] for x in frames.values()),'icons':icons(raw['idle_0'])}
    write_module('gf_lumine_training_data',data)
    law={};ims={name:Image.open(ROOT/f'assets/roster-v2/lawachurl-{name}.png').convert('RGBA') for name in ['idle','hurt','guard','crouch','crouchGuard','down']}
    for name,im in list(ims.items()):ims[name]=im.resize((round(im.width*.625),round(im.height*.625)),Image.Resampling.NEAREST)
    pal=build_palette(list(ims.values()),16,seed=21)
    for name,im in ims.items():law[name],target=encode(im,pal,3.5/.625);target.save(OUT/'fit'/f'lawachurl-{name}.png')
    groups={k:{'frames':[k],'durations':[20]} for k in law};groups['walk']={'frames':['idle'],'durations':[20]}
    lawdata={'frames':law,'groups':groups,'aliases':{'walk1':'idle','walk2':'idle','jump':'idle','slash':'idle','special':'idle','qRelease':'idle'},'bodyPeak':max(x['n'] for x in law.values()),'icons':icons(ims['idle'])}
    write_module('gf_lawachurl_training_data',lawdata)
    stats={key:{'uniqueFrameMean':sum(f['n'] for f in bank.values())/len(bank),'peak':max(f['n'] for f in bank.values()),'frameRects':{id:f['n'] for id,f in bank.items()}} for key,bank in [('lumine',frames),('lawachurl',law)]}
    (OUT/'import.json').write_text(json.dumps({'lumine':meta,'bodyPeak':{'lumine':data['bodyPeak'],'lawachurl':lawdata['bodyPeak']},'bodyStats':stats,'pixelReconstruction':True,'placeholder':{'dash':'walk accelerated','lumineHurt':'idle (stationary dummy does not attack)'},'excluded':['walk-back-v1','dash-forward-v1','crouch-v1']},ensure_ascii=False,indent=2),encoding='utf-8')
    assert all(s['uniqueFrameMean']<1000 for s in stats.values()),stats
    print('unique body-frame means',{k:round(v['uniqueFrameMean'],2) for k,v in stats.items()})
    return data['bodyPeak'],lawdata['bodyPeak']

def write_module(name,data):
    (OUT/'source'/f'{name}.lua').write_text("__loaders['"+name+"']=function() return "+lua(data)+' end\n',encoding='utf-8')

def export_guide():
    im=Image.open(ROOT/'outputs/tutorial-paimon-20261015/paimon-avatar-v1.png').convert('RGBA')
    im.thumbnail((48,48),Image.Resampling.NEAREST)
    canvas=Image.new('RGBA',(50,50));canvas.alpha_composite(im,((50-im.width)//2,(50-im.height)//2))
    data,target=encode(canvas,build_palette([canvas],12,seed=21),1,anchor=[25,50])
    target.save(OUT/'fit/paimon-guide.png');write_module('gf_paimon_training_avatar',data)

def export_law_attack_poses():
    # Reuse existing pixel artwork and palette; old six bodies stay byte-for-byte data-identical.
    sys.path.insert(0,str(ROOT/'work/optimization-test-deps'))
    from lupa.lua53 import LuaRuntime
    from compact_assets import python_table
    rt=LuaRuntime(unpack_returned_tuples=True)
    rt.execute('__loaders={};'+(OUT/'source/gf_lawachurl_training_data.lua').read_text(encoding='utf-8'))
    data=python_table(rt.globals().__loaders['gf_lawachurl_training_data']())
    pal=[color[:3] for color in data['frames']['idle']['pal']]
    for name,original in [('strikeHigh','special'),('strikeLow','slash')]:
        im=Image.open(ROOT/f'assets/roster-v2/lawachurl-{original}.png').convert('RGBA')
        im=im.resize((round(im.width*.625),round(im.height*.625)),Image.Resampling.NEAREST)
        data['frames'][name],target=encode(im,pal,3.5/.625)
        target.save(OUT/'fit'/f'lawachurl-{name}.png')
    data['bodyPeak']=max(f['n'] for f in data['frames'].values())
    counts={k:f['n'] for k,f in data['frames'].items()}
    mean=sum(counts.values())/len(counts);assert mean<1000,(mean,counts)
    write_module('gf_lawachurl_training_data',data)
    report=json.loads((OUT/'import.json').read_text(encoding='utf-8'))
    report['bodyStats']['lawachurl']={'uniqueFrameMean':mean,'peak':data['bodyPeak'],'frameRects':counts}
    report['bodyPeak']['lawachurl']=data['bodyPeak']
    report['lawachurlAttackArt']={'strikeHigh':'assets/roster-v2/lawachurl-special.png','strikeLow':'assets/roster-v2/lawachurl-slash.png','palette':'unchanged existing idle palette','pixelReconstruction':True}
    (OUT/'import.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

def build():
    export_law_attack_poses()
    order=json.loads((ROOT/'runtime/source/order.json').read_text(encoding='utf-8'))
    codes={p:(ROOT/'runtime'/p).read_text(encoding='utf-8') for p in order}
    def change(p,old,new):
        assert old in codes[p],(p,old[:80]);codes[p]=codes[p].replace(old,new,1)
    change('source/prefix.lua','GF_FPS_VISIBLE=true','GF_FPS_VISIBLE=false')
    change('source/app/gf_app.lua',"    intro = 'gf_scene_intro',", "    notice='gf_scene_update_notice',trainingcourses='gf_scene_training_courses',\n    intro = 'gf_scene_intro',")
    change('source/app/gf_app.lua','function App:go(name, args)',"function App:go(name, args)\n    if name=='title' and not self.initialNoticeShown and not self.env.initialNoticeShown then name='notice';args={} end")
    change('source/characters/gf_character_registry.lua',"},byKey={},providers={}}"," {key='lumine',name='荧',element='anemo',weapon='sword',attack='轻击试作',skill='暂未开放',burst='暂未开放',h=335,provider='gf_character_lumine_training'},\n {key='lawachurl',name='岩盔丘丘王',element='geo',weapon='claymore',attack='教学陪练',skill='暂未开放',burst='暂未开放',h=440,provider='gf_character_lawachurl_training'},\n},byKey={},providers={}}")
    change('source/characters/gf_art.lua','local function picture(key, which)','local function picture(key, which)\n    if key==\'lumine\' or key==\'lawachurl\' then return Registry.provider(key).image(\'hud\') end')
    change('source/characters/gf_kits.lua',"require('gf_element_rules')(K)","require('gf_element_rules')(K)\nK.en.lumine='LUMINE';K.en.lawachurl='STONEHIDE LAWACHURL'\nK.characterWeapons=K.characterWeapons or {}\nK.characterWeapons.lumine={reach=1,light1={pose='slash',startup=10,active=4,recovery=16,damage=32,hitstun=24,blockstun=12,push=5,box={x=40,y=110,w=190,h=130},energy=0,cancel={}}}\nK.characterWeapons.lawachurl={reach=1}\nK.body.lawachurl={walk=3,back=2.5,dash=10,health=1500,weight=1.3}")
    change('source/menu/gf_scene_menu.lua',"elseif id == 'tutorial' then self:tutorialMenu()","elseif id == 'tutorial' then app:travel('trainingcourses')")
    change('source/characters/gf_kits.lua',"K.characterWeapons.lumine={reach=1,light1={pose='slash',startup=10,active=4,recovery=16,damage=32,hitstun=24,blockstun=12,push=5,box={x=40,y=110,w=190,h=130},energy=0,cancel={}}}","require('gf_lumine_training_rules')(K)")
    change('source/characters/gf_kits.lua','K.characterWeapons.lawachurl={reach=1}',"K.characterWeapons.lawachurl={reach=1,light1={pose='slash',startup=54,active=5,recovery=110,damage=24,hitstun=18,blockstun=12,push=1,level='high',box={x=10,y=100,w=350,h=220},cancel={}},crouchHeavy={pose='slash',startup=60,active=5,recovery=74,damage=24,hitstun=18,blockstun=12,push=1,level='low',box={x=10,y=20,w=350,h=100},cancel={}}}")
    change('source/battle/gf_battle_pause.lua',"items[#items + 1] = {id = 'select', label = '重新选择角色'}","items[#items + 1] = self.lesson and {id='courses',label='返回课程选择'} or {id = 'select', label = '重新选择角色'}")
    change('source/battle/gf_battle_pause.lua',"    elseif id == 'quit' then app:travel('menu')","    elseif id == 'courses' then app:travel('trainingcourses')\n    elseif id == 'quit' then app:travel('menu')")
    change('source/battle/gf_scene_fight.lua','    local menu = app.input:menu()',"    local menu = app.input:menu()\n    if self.lesson and self.lesson:isSpeaking() and self.sim.phase=='fight' and not self.pauseMenu and not self.showMoves then for _,a in ipairs(menu)do if a=='pause' then self:openPause();return end end;self.lesson:dialogueInput(menu);return end\n    if self.lesson and self.lesson.completeMenu then self.lesson:menuTick();self.lesson.completeMenu:input(menu);return end")
    change('source/battle/gf_scene_fight.lua','    return ins[1], ins[2]',"    if self.lesson and self.lesson:isBriefing() then return 0,0 end\n    if self.chars[1].key=='lumine' then ins[1]=ins[1] & (1|2|4|8|16|32|64|128|256|512|1024) end\n    if self.lesson and self.lesson.coach then ins[2]=self.lesson.coach:input() end\n    if self.lesson and self.lesson.extended then ins[2]=self.lesson.extended:input() end\n    if self.chars[1].key=='lumine' and app.input:device()=='pad' and ins[1]&(32|256)==(32|256) then ins[1]=(ins[1]&~(32|256))|1024 end\n    return ins[1], ins[2]")
    change('source/input/gf_touch.lua','    local inp = app.input',"    if self.f.key=='lumine' then local keep={};for _,b in ipairs(self.buttons) do keep[#keep+1]=b end;keep[#keep+1]={id='TH',bit=512,label='投',x=W/2-450,y=-H/2+190,r=42};keep[#keep+1]={id='AS',bit=1024,label='援',x=W/2-440,y=-H/2+85,r=42};self.buttons=keep end\n    local inp = app.input")
    change('source/input/gf_touch.lua','    inp:area(0, H / 2 - 238, 100, 110,',"    inp:area(self.f.key=='lumine' and W/2-65 or 0, self.f.key=='lumine' and H/2-250 or H/2-238, 100, 110,")
    change('source/input/gf_touch.lua','    local py = app.H / 2 - 222',"    local px=self.f.key=='lumine' and app.W/2-65 or 0\n    local py = app.H / 2 - (self.f.key=='lumine' and 250 or 222)")
    for old,new in [('G.ELLIPSE, 0, py','G.ELLIPSE, px, py'),('G.RING, 0, py','G.RING, px, py'),('L:rect(-7, py','L:rect(px-7, py'),('L:rect(7, py','L:rect(px+7, py'),("L:label('菜单',0,py-42","L:label('菜单',px,py-42")]:change('source/input/gf_touch.lua',old,new)
    change('source/battle/gf_scene_fight.lua','    self.loadStep = 0',"    if args.tutorial and chars[1].key=='lumine' then self.lesson=require('gf_training_lesson').new(self) end\n    if chars[1].key=='lumine' and not (self.lesson and self.lesson.extended) then self.trainingView=require('gf_training_extended').new({scene=self}) end\n    self.loadStep = 0")
    change('source/battle/gf_scene_fight.lua','        self:events()','        self:events()\n        if self.lesson then self.lesson:tick() end')
    change('source/battle/gf_scene_fight.lua','    self.hud:draw()',"    if self.lesson then self.hud.root:on(not self.lesson:isSpeaking());if not self.lesson:isSpeaking() then self.hud:draw() end;self.lesson:draw() else self.hud:draw() end")
    change('source/battle/gf_scene_fight.lua','    if self.hud then self.hud:free() end','    if self.hud then self.hud:free() end\n    if self.lesson then self.lesson:free() end\n    if self.trainingView then self.trainingView:free() end')
    change('source/battle/gf_scene_fight.lua','    self:drawBanners()',"    if self.lesson then self.annL:clear() else self:drawBanners() end")
    change('source/battle/gf_scene_fight.lua','self.sim = Sim.new({',"self.sim = (chars[1].key=='lumine' and require('gf_sim_lumine_training') or Sim).new({")
    change('source/battle/gf_scene_fight.lua','    G.endBitmapBudget()',"    if self.lesson and self.lesson.extended then G.bitmapOwner(1000);self.lesson.extended:drawWorld() elseif self.trainingView then G.bitmapOwner(1000);self.trainingView:drawWorld() end\n    G.endBitmapBudget()")
    change('source/input/gf_input.lua',"    {ck('U'), 1, B.DA}, {ck('L'), 1, B.TH},","    {ck('U'), 1, B.DA}, {ck('L'), 1, B.TH}, {ck('G'),1,1024},")
    extra=[]
    for key in ['lumine','lawachurl']:
        p=OUT/'source'/f'gf_character_{key}_training.lua';extra.append(p.read_text(encoding='utf-8'))
    extra=[(OUT/'source/gf_lumine_training_data.lua').read_text(encoding='utf-8'),(OUT/'source/gf_lawachurl_training_data.lua').read_text(encoding='utf-8')]+extra
    extra.append((OUT/'source/gf_aether_support_data.lua').read_text(encoding='utf-8'))
    extra.extend([(OUT/'source/gf_paimon_training_avatar.lua').read_text(encoding='utf-8'),(ROOT/'runtime/source/modes/gf_training_lesson.lua').read_text(encoding='utf-8')])
    for file in ['characters/gf_lumine_training_rules.lua','modes/gf_training_attack.lua','battle/gf_sim_lumine_training.lua','modes/gf_training_extended.lua','characters/gf_aether_support.lua','modes/gf_training_courses.lua','modes/gf_training_coach.lua','menu/gf_scene_training_courses.lua','menu/gf_update_notice_data.lua','menu/gf_scene_update_notice.lua']:
        p=ROOT/'runtime/source'/file;extra.append(p.read_text(encoding='utf-8'));shutil.copy2(p,OUT/'source'/p.name)
    shutil.copy2(ROOT/'runtime/source/modes/gf_training_lesson.lua',OUT/'source/gf_training_lesson.lua')
    parts=[]
    for p in order:
        if p=='source/bootstrap.lua':parts.extend(extra)
        parts.append(codes[p])
        dest=OUT/'candidate'/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(codes[p],encoding='utf-8')
    path=OUT/'candidate.lua';path.write_text('\n'.join(parts),encoding='utf-8');print('candidate',hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument('--build-only',action='store_true');a=ap.parse_args()
    if not a.build_only:print('body peaks',export())
    export_guide()
    build()
