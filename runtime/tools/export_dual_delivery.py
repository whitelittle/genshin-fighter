"""Import Clorinde/Arlecchino's 25-action deliveries, retaining independent banks."""
from pathlib import Path
import json,base64,struct,hashlib,math,sys,re
from export_furina import lua
R=Path(__file__).resolve().parents[2];RT=R/'runtime'
MAP={'backwalk':'back','forwarddash':'dash','standguard':'block','crouchguard':'cblock','crouchlight':'crouchLight','crouchheavy':'crouchHeavy','airlight':'airLight','airheavy':'airHeavy','E':'skill','Q':'burst','victim':'thrown','hit_knockdown':'hurt','wakeup':'getup','victory':'win','defeat':'lose'}
for key in ['clorinde','arlecchino']:
 src=R/f'outputs/{key}-actions-20261011';bank=json.loads((src/'actions.json').read_text(encoding='utf-8'));effects=json.loads((src/'effects.json').read_text(encoding='utf-8'))
 frames={};groups={};receipt=[];dedup={}
 def image(f,id,kind):
  path=src/f['file'];obj=json.loads((src/f['rectData']).read_text(encoding='utf-8'));w,h=struct.unpack('>II',path.read_bytes()[16:24]);raw=struct.pack('<'+'H'*(len(obj['rects'])*5),*(v for r in obj['rects'] for v in r));raw+=b'\0'*((-len(raw))%3)
  img={'n':len(obj['rects']),'d':base64.b64encode(raw).decode(),'pal':[c[:3]+[c[3] if len(c)>3 else 255] for c in obj['palette']],
       'w':w,'h':h,'ax':f['anchor'][0],'ay':f['anchor'][1],'u':f['scale'],'ux':f['scale'],'uy':f['scale']}
  identity=hashlib.sha256(json.dumps(img,sort_keys=True).encode()).hexdigest();pose=dedup.get(identity,id)
  if identity not in dedup:frames[pose]=img;dedup[identity]=pose
  receipt.append({'pose':pose,'kind':kind,'file':path.relative_to(R).as_posix(),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rectsFile':(src/f['rectData']).relative_to(R).as_posix(),'anchor':f['anchor'],'scale':f['scale']})
  return pose
 for label,g in bank.items():
  id=MAP.get(label,label);groups[id]={'frames':[image(f,id+'_'+str(i),'body') for i,f in enumerate(g['frames'])],'durations':g['durations'],'sourceFrames':[{k:f[k] for k in ['file','anchor','scale'] if k in f} for f in g['sourceFrames']],'events':g.get('events',[])}
  for name,variant in g.get('variants',{}).items():groups[id].setdefault('variants',{})[name]=[image(f,id+'_'+name+'_'+str(i),'body') for i,f in enumerate(variant['frames'])]
 peak=max(f['n'] for f in frames.values())
 effect_ids={name:image(f['fit'],'fx_'+name,'effect') for name,f in effects.items()}
 portrait=json.loads((src/'portrait-fit.json').read_text(encoding='utf-8'));portrait_id=image(portrait,'ultimatePortrait','portrait')
 aliases={id:g['frames'][0] for id,g in groups.items()};aliases.update(walk1=groups['walk']['frames'][0],walk2=groups['walk']['frames'][2],guard=groups['block']['frames'][1],crouchGuard=groups['cblock']['frames'][1],slash=groups['light1']['frames'][2],special=groups['skill']['frames'][2],qRelease=groups['burst']['frames'][3],down=groups['hurt']['frames'][-1])
 data={'frames':frames,'groups':groups,'aliases':aliases,'bodyPeak':peak,'auxPeak':max(frames[id]['n'] for id in effect_ids.values()),'effectIds':effect_ids,'portrait':portrait_id,'version':{'page':'player.html','bank':'actions.json','sha256':hashlib.sha256((src/'actions.json').read_bytes()).hexdigest()}}
 (RT/f'source/assets/gf_{key}_data.lua').write_text(f"__loaders['gf_{key}_data']=function() return "+lua(data)+' end\n',encoding='utf-8')
 rules={'skillTotal':sum(groups['skill']['durations']),'getupTotal':sum(groups['getup']['durations'])}
 for id in ['light1','light2','light3','heavy','crouchLight','crouchHeavy','airLight','airHeavy']:
  group=groups[id];cd=bank[next(k for k in bank if MAP.get(k,k)==id)].get('combatDesign',{});events=group['events']
  start=cd.get('startup',next((e['tick'] for e in events if e.get('tick')),6));active=cd.get('active',4)
  total=sum(group['durations']);rules[id]={'startup':start,'active':active,'recovery':max(1,total-start-active),'level':cd.get('attackLevel','low' if id.startswith('crouch') else 'high' if id.startswith('air') else 'mid'),'damage':cd.get('damage')}
 rules['throwRoots']=[[14500+(17000*min(max(t-32,0),10)//10),max(0,6500*(10-min(max(t-32,0),10))//10) if t>=32 else 0] for t in range(51)]
 rules['burstRoots']=[[38000+(10000*max(0,t-132)//30),0 if t<52 or t>=162 else (10500 if t<132 else 10500*(162-t)//30)] for t in range(163)]
 (RT/f'source/characters/gf_{key}_rules_data.lua').write_text(f"__loaders['gf_{key}_rules_data']=function() return "+lua(rules)+' end\n',encoding='utf-8')
 # Independent per-character view and rule adapters, no new extraction of shared choreography.
 provider=(RT/'source/characters/gf_character_ayaka.lua').read_text(encoding='utf-8').replace('gf_character_ayaka',f'gf_character_{key}').replace('gf_ayaka_data',f'gf_{key}_data').replace('kamisatoayaka',key)
 provider=re.sub(r'function P.rootOffset\(v\).*?\nend','function P.rootOffset(v) return 0 end',provider,flags=re.S)
 provider=provider.replace("if st=='throw' then return sample('throw',t) end", "if st=='throw' then local pose,phase=sample('throw',t);local low=D.groups.throw.variants and D.groups.throw.variants.nahida;return f.foe.key=='nahida' and low and low[phase] or pose end")
 provider=provider.replace("if st=='thrown' then return sample('thrown',f.foe.key=='"+key+"' and f.foe.t or t/30*total(D.groups.thrown)) end", "if st=='thrown' then local pose,phase=sample('thrown',f.foe.key=='"+key+"' and f.foe.t or t/30*total(D.groups.thrown));local low=D.groups.thrown.variants and D.groups.thrown.variants.nahida;return f.foe.key=='nahida' and low and low[phase] or pose end")
 (RT/f'source/characters/gf_character_{key}.lua').write_text(provider,encoding='utf-8')
 sim=(RT/'source/battle/gf_sim_ayaka.lua').read_text(encoding='utf-8').replace('gf_sim_ayaka',f'gf_sim_{key}').replace('gf_ayaka_rules_data',f'gf_{key}_rules_data').replace('kamisatoayaka',key).replace('ayakaCinematic',key+'Cinematic')
 sim=sim.replace('a.t<44','a.t<42').replace('a.t<152','a.t<162').replace('if t==52 then','if t==6 then').replace('if t>=152 then','if t>=162 then').replace('elseif t>=72 then','elseif t>=24 then').replace('math.min(153,t+1)','math.min(163,t+1)').replace('math.min(73,t+1)','math.min(51,t+1)').replace('t<=44','t<42').replace('if t==34 then','if t==32 then').replace('if t==44 then','if t==42 then').replace('if t>=72 then','if t>=50 then').replace("p.invul=24","p.invul=6")
 skill=f""" function S:skillUpdate(p)
  if p.key~='{key}' then return oldSkillUpdate(self,p) end
  p.vx=0
  local t=p.t;local window={'(t>=8 and t<10 and 1 or t>=18 and t<22 and 2 or 0)' if key=='clorinde' else '(t>=18 and t<24 and 1 or 0)'}
  if window>0 and ((p.skillHitMask or 0)&(1<<window))==0 then
   local x0,x1,y0,y1=ctx.boxOf(p,{{x=60,y=0,w=220,h=230}},1);local a,b,c,d=self:hurtbox(p.foe)
   if a and ctx.overlap(x0,x1,y0,y1,a,b,c,d) then
    self:hit(p,p.foe,{{damage={'window==1 and 35 or 50' if key=='clorinde' else '85'},hitstun=28,blockstun=16,push=8,level='mid',energy=8,shake=8}},'skill')
    p.skillHitMask=(p.skillHitMask or 0)|(1<<window)
   end
  end
  if p.t>=D.skillTotal then self:setState(p,p.y>0 and 'air' or 'idle') end
 end
 local oldStartSkill=S.startSkill
 function S:startSkill(p)
  local ok=oldStartSkill(self,p)
  if ok and p.key=='{key}' then p.skillHitMask=0 end
  return ok
 end
"""
 sim=re.sub(r' function S:skillUpdate\(p\).*?\n end\n(?= function S:burstUpdate)',skill,sim,flags=re.S)
 (RT/f'source/battle/gf_sim_{key}.lua').write_text(sim,encoding='utf-8')
 rule=f"""__loaders['gf_character_{key}_rules']=function()
local D=require('gf_{key}_rules_data')
return function(K)
 local function copy(t)local r={{}};for k,v in pairs(t)do r[k]=v end;return r end
 local w=copy(K.weapons.{'sword' if key=='clorinde' else 'polearm'});w.reach=1
 for _,id in ipairs({{'light1','light2','light3','heavy','crouchLight','crouchHeavy','airLight','airHeavy'}})do local m=copy(w[id]);local d=D[id]
 m.startup,m.active,m.recovery=d.startup,d.active,d.recovery;m.level=d.level;m.damage=d.damage or m.damage;m.projectile=nil;m.fx=nil;m.airPush=nil;w[id]=m end
 K.characterWeapons=K.characterWeapons or {{}};K.characterWeapons.{key}=w
 K.skills.{key}={{style='delivered',startup=12,active=8,recovery=18,damage=85,cd=150,hitstun=28,fx='{'lastlight' if key=='clorinde' else 'balemoon'}'}}
 K.bursts.{key}={{style='deliveredCinematic',damage=290,hits=3,range=380,confirm=6,finish=162}}
 K.body.{key}=copy(K.body.{key} or K.body.default);K.body.{key}.getupTicks=D.getupTotal
end
end
"""
 (RT/f'source/characters/gf_character_{key}_rules.lua').write_text(rule,encoding='utf-8')
 (RT/f'{key}-import.json').write_text(json.dumps({'key':key,'groups':len(groups),'bodyPeak':peak,'sources':receipt,'nativeTested':False,'runtimeAdaptations':['existing weapon boxes pending fine tuning','independent delivered body clock','Q confirm 6/full162/miss24','throw release32/finish50']},ensure_ascii=False,indent=2),encoding='utf-8')
 print(key,len(groups),len(frames),peak)
