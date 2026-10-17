from pathlib import Path
import json
r=Path('runtime');s=r/'source'
def edit(p,a,b):
 p=s/p;t=p.read_text(encoding='utf-8');assert a in t,(p,a);p.write_text(t.replace(a,b),encoding='utf-8')
p=r/'tools/export_ayaka.py';t=p.read_text(encoding='utf-8').replace("'ux':f.get('scaleX',f['scale']),'uy':f.get('scaleY',f['scale'])","'ux':f['scale'],'uy':f['scale']")
p.write_text(t,encoding='utf-8')
provider=(s/'characters/gf_character_furina.lua').read_text(encoding='utf-8').replace('gf_character_furina','gf_character_ayaka').replace('gf_furina_data','gf_ayaka_data')
provider=provider.replace("if st=='dash' or st=='backdash' then return sample(st,t) end","if st=='dash' or st=='backdash' then return sample(st,t/(st=='dash' and 14 or 18)*total(D.groups[st])) end")
provider=provider.replace("return sample('jump',f.flightT or t)","return sample('jump',t/32*total(D.groups.jump))")
provider=provider.replace("f.foe.key=='furina' and f.foe.t or t/30*total(D.groups.thrown)","f.foe.key=='kamisatoayaka' and f.foe.t or t/30*total(D.groups.thrown)")
provider=provider.replace("P.groundedFrames=true",'''function P.rootOffset(v)
 if v.f.state~='thrown' then return 0 end
 local _,phase=sample('thrown',v.f.foe.key=='kamisatoayaka' and v.f.foe.t or v.f.t/30*total(D.groups.thrown))
 return ({0,140,100,90,0,0})[phase]
end
P.groundedFrames=true''')
(s/'characters/gf_character_ayaka.lua').write_text(provider,encoding='utf-8')
rules=(s/'characters/gf_character_furina_rules.lua').read_text(encoding='utf-8').replace('gf_character_furina_rules','gf_character_ayaka_rules').replace('gf_furina_rules_data','gf_ayaka_rules_data').replace('furina','kamisatoayaka')
rules=rules[:rules.index(' K.skills.kamisatoayaka=')]+''' K.skills.kamisatoayaka={style='iceBloomDelivered',startup=12,active=8,recovery=18,damage=85,cd=150,hitstun=28,fx='iceBloom'}
 K.bursts.kamisatoayaka={style='soumetsuCinematic',damage=290,hits=3,range=380,fx='soumetsu',confirm=52,finish=152}
 K.body.kamisatoayaka=copy(K.body.default);K.body.kamisatoayaka.getupTicks=40
end
end
'''
(s/'characters/gf_character_ayaka_rules.lua').write_text(rules,encoding='utf-8')
edit(Path('characters/gf_character_registry.lua'),"},byKey={},providers={}}"," {key='kamisatoayaka',name='神里绫华',element='cryo',weapon='sword',attack='神里流·倾',skill='神里流·冰华',burst='神里流·霜灭',h=335,candidate=true,provider='gf_character_ayaka'},\n},byKey={},providers={}}")
edit(Path('characters/gf_kits.lua'),"require('gf_character_furina_rules')(K)","require('gf_character_furina_rules')(K)\nrequire('gf_character_ayaka_rules')(K)")
edit(Path('battle/gf_sim.lua'),"require('gf_sim_furina')(S,ctx)","require('gf_sim_furina')(S,ctx)\nrequire('gf_sim_ayaka')(S,ctx)")
edit(Path('network/gf_online.lua'),'O.VERSION = 3','O.VERSION = 4')
# Share the bounded double-buffer bitmap publisher, but character-specific effect selection stays separate.
p=s/'characters/gf_character_furina_view.lua';t=p.read_text(encoding='utf-8');start=t.index(' local function publish(');end=t.index(' function P.extras(',start)
publisher=t[start:end].replace(' local function publish','local function publish',1).replace('local img=P.image(id)','local img=P.image(id)',1)
shared="__loaders['gf_character_effect_channel']=function()\nreturn function(P)\n"+publisher+"return publish\nend\nend\n"
(s/'characters/gf_character_effect_channel.lua').write_text(shared,encoding='utf-8');p.write_text(t[:start]+" local publish=require('gf_character_effect_channel')(P)\n"+t[end:],encoding='utf-8')
view='''__loaders['gf_character_ayaka_view']=function()
local G=require('gf_gfx')
return function(P,D)
 local publish=require('gf_character_effect_channel')(P)
 function P.newView(v,layers)
  local ch={slots={G.bitmap(layers.fx),G.bitmap(layers.fx)},capacity=D.auxPeak}
  for _,b in ipairs(ch.slots) do b.pinned=true;b.node:on(false) end
  v.characterChannels={ch}
 end
 function P.reserveExtras(v,budget)
  for _,b in ipairs(v.characterChannels[1].slots) do
   if #b.kids<D.auxPeak then b:ensure(math.min(D.auxPeak,#b.kids+budget));return false end
  end
  return true
 end
 function P.extras(v)
  local f=v.f;local id,t=f.moveId,f.t
  if f.airMove then id,t=f.airMoveId,f.airT or 0
  elseif f.state=='skill' then id='skill'
  elseif f.state=='burst' then id='burst'
  elseif f.state~='attack' then id=nil end
  local e=id and D.groups[id] and D.groups[id].effects
  if not e or t<e.startTick or t>=e.startTick+e.duration then return {} end
  local age=t-e.startTick;local i=math.min(3,1+math.floor(age/e.duration*3))
  local x,y,face=f.x/100,f.y/100,f.face;local scale,alpha=1,1
  local dx,dy=e.worldOffset[1],-e.worldOffset[2]
  if id=='burst' then
   i=1+math.floor(age/10)%3;dx,dy=230+math.min(145,age*3),205;scale=1.4
   alpha=math.min(1,age/8,math.max(0,(e.duration-age)/14));y=0
  elseif not e.followActor then x=(f.actionX or f.x)/100;y=0 end
  return {{id=e.frames[i],x=x+face*dx,y=y+dy,face=face,scale=scale,alpha=alpha}}
 end
 function P.drawExtras(v)
  local a=P.extras(v)[1];local ch=v.characterChannels[1]
  if a then publish(ch,a.id,a.x,a.y,a.face,a.scale,a.alpha,0,320) else publish(ch) end
 end
 function P.freeView(v)for _,b in ipairs(v.characterChannels[1].slots) do b:free() end end
end
end
'''
(s/'characters/gf_character_ayaka_view.lua').write_text(view,encoding='utf-8')
# Ayaka owns her delivered E/Q/throw clocks; wrappers leave every other character untouched.
t=(s/'battle/gf_sim_furina.lua').read_text(encoding='utf-8').replace('gf_sim_furina','gf_sim_ayaka').replace('gf_furina_rules_data','gf_ayaka_rules_data').replace("'furina'","'kamisatoayaka'")
t=t.replace('a.t<50','a.t<44').replace('a.t<158','a.t<152').replace('385*C','180*C').replace("'fanfare'","'soumetsu'").replace("'salonCinematic'","'soumetsuCinematic'")
t=t.replace('p.t>=18 and p.t<24','p.t>=12 and p.t<20').replace('{x=70,y=100,w=280,h=150}','{x=60,y=0,w=220,h=230}').replace('damage=70,hitstun=24','damage=85,hitstun=28').replace('p.t>=48','p.t>=38')
t=t.replace('t==12','t==52').replace("'furinaCinematic'","'ayakaCinematic'").replace('t==56 or t==78 or t==100','t==70 or t==94 or t==118').replace('damage=t==100 and 88 or 86','damage=t==118 and 96 or 97').replace('math.min(159,t+1)','math.min(153,t+1)').replace('t>=158','t>=152').replace('t>=42','t>=72')
t=t.replace('t<=50','t<=44').replace('t==30','t==34').replace('t==50','t==44')
t=t[:t.index("  if p.key=='kamisatoayaka' and p.state=='air'")]+''' end
 function S:physics(p)
  if locked(p) then return end
  return oldPhysics(self,p)
 end
end
end
'''
(s/'battle/gf_sim_ayaka.lua').write_text(t,encoding='utf-8')
# Generic victim presentation before falling back to each fighter's own provider.
p=s/'render/gf_fview.lua';t=p.read_text(encoding='utf-8');pos=t.index("    local provider=Registry.provider(self.key)",t.index('function V:poseFor()'))
t=t[:pos]+'''    if a and a.key=='kamisatoayaka' and not Registry.provider(self.key) then
        if self.f.state=='thrown' and a.state=='throw' then
            local phase=a.t<10 and 0 or a.t<24 and 1 or a.t<34 and 2 or a.t<44 and 3 or 4
            return frameName(phase<4 and 'victim' or 'hurt',math.min(3,phase))
        end
        if a.state=='burst' and a.cinematicConfirmed then return frameName(a.t>=144 and 'hurt' or 'victim',3) end
    end
'''+t[pos:]
t=t.replace("f.foe.key=='furina' and ((st==", "(f.foe.key=='furina' or f.foe.key=='kamisatoayaka') and ((st==")
t=t.replace("        self.tilt,self.sx,self.sy,self.ox,self.oy=tilt,sx,sy,ox,oy","        if provider and provider.rootOffset then oy=provider.rootOffset(self) end\n        self.tilt,self.sx,self.sy,self.ox,self.oy=tilt,sx,sy,ox,oy")
p.write_text(t,encoding='utf-8')
# Ayaka and Furina both use their own hurt frames when captured by an authored cinematic.
for name in ['furina','ayaka']:
 p=s/f'characters/gf_character_{name}.lua';t=p.read_text(encoding='utf-8');pos=t.index(' if f.airMove then')
 t=t[:pos]+" if f.foe.key=='kamisatoayaka' and f.foe.state=='burst' and f.foe.cinematicConfirmed then return D.groups.hurt.frames[f.foe.t>=144 and 4 or 3] end\n"+t[pos:];p.write_text(t,encoding='utf-8')
order=json.loads((s/'order.json').read_text(encoding='utf-8'))
for file in ['assets/gf_ayaka_data.lua','assets/gf_art_kamisatoayaka.lua','characters/gf_ayaka_rules_data.lua','characters/gf_character_ayaka.lua','characters/gf_character_ayaka_rules.lua','characters/gf_character_ayaka_view.lua','characters/gf_character_effect_channel.lua','battle/gf_sim_ayaka.lua']:
 order.insert(-1,'source/'+file)
(s/'order.json').write_text(json.dumps(order,indent=2),encoding='utf-8')
p=r/'tools/preview.py';t=p.read_text(encoding='utf-8');t=t[:t.index("    if '--scene' not in sys.argv:")]+"    if '--scene' not in sys.argv:sys.argv.extend(['--scene','intro'])\n    if '--device' not in sys.argv:sys.argv.extend(['--device','Mobile'])\n    preview.main()\n";p.write_text(t,encoding='utf-8')
p=r/'tools/index.html';t=p.read_text(encoding='utf-8').replace('整理版·芙宁娜模拟器','整理版·四角色全流程模拟器').replace('value="Mobile"','value="Mobile" selected');p.write_text(t,encoding='utf-8')
p=r/'tests/run.py';t=p.read_text(encoding='utf-8').replace('O.VERSION==3','O.VERSION==4').replace('version=2','version=3').replace('lobby.version=3','lobby.version=4');p.write_text(t,encoding='utf-8')
p=r/'tests/mock_flow.py';t=p.read_text(encoding='utf-8').replace('built==3','built==4');p.write_text(t,encoding='utf-8')
