"""Build isolated, editable two-role prototypes; preserve the current runtime source."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT.parent / 'outputs/nahida-raiden-rework-20261015'

def replace(code, old, new):
    assert code.count(old) == 1, old[:100]
    return code.replace(old, new)

def build():
    OUT.mkdir(exist_ok=True)
    order = json.loads((ROOT / 'source/order.json').read_text(encoding='utf-8'))
    original = {p: (ROOT / p).read_text(encoding='utf-8') for p in order}
    perf = dict(original)
    p = 'source/render/gf_gfx.lua'
    # Hoist callback invariants, instead of allocating geometry caches per frame.
    # Budget left/used remain mutable on this same table inside the loop.
    perf[p] = replace(perf[p], '    local processed=i\n', '    local processed=i\n    local frameBudget=self.budgeted and G.bitmapBudget\n    local seam=img.seam or SEAM\n')
    perf[p] = replace(perf[p], '        local frameBudget=self.budgeted and G.bitmapBudget\n', '')
    perf[p] = replace(perf[p], '        local seam=img.seam or SEAM\n', '')
    p = 'source/characters/gf_art.lua'
    # The alias map is immutable; avoid allocating it every body image lookup.
    aliases="    local aliases={idle='basic_0',walk1='basic_2',walk2='basic_4',jump='move_1',crouch='guard_1',crouchGuard='guard_7',guard='guard_6',slash='light_2',special='skill_2',qRelease=key=='raidenshogun' and 'qburst_3' or 'skill_6',hurt='hurt_0',down='hurt_3'}\n"
    perf[p] = replace(perf[p], aliases, "    local resolved=pose=='qRelease' and (key=='raidenshogun' and 'qburst_3' or 'skill_6') or animationAliases[pose] or pose\n")
    perf[p] = replace(perf[p], 'local animations\n', "local animationAliases={idle='basic_0',walk1='basic_2',walk2='basic_4',jump='move_1',crouch='guard_1',crouchGuard='guard_7',guard='guard_6',slash='light_2',special='skill_2',hurt='hurt_0',down='hurt_3'}\nlocal animations\n")
    perf[p] = perf[p].replace('aliases[pose] or pose', 'resolved')
    candidate = dict(perf)
    p = 'source/characters/gf_character_rules.lua'
    candidate[p] = replace(candidate[p], "nahida = {walk = 4.8, back = 4.0, dash = 14, health = 950, weight = 0.9}", "nahida = {walk = 4.8, back = 4.0, dash = 18, dashDecay = 96, dashTicks = 16, dashCancel = 4, health = 950, weight = 0.9}")
    candidate[p] = replace(candidate[p], 'K.body = {', "K.body = {\n    raidenshogun = {walk = 4.4, back = 3.6, dash = 19, dashDecay = 96, dashTicks = 16, dashCancel = 4, health = 1000, weight = 1.0},")
    p = 'source/battle/gf_sim_fighter.lua'
    candidate[p] = replace(candidate[p], "if p.t >= 14 then self:setState(p, 'idle') end\n        p.vx = p.vx * 92 // 100\n        if p.t >= 5", "if p.t >= (p.kit.body.dashTicks or 14) then self:setState(p, 'idle') end\n        p.vx = p.vx * (p.kit.body.dashDecay or 92) // 100\n        if p.t >= (p.kit.body.dashCancel or 5)")
    p = 'source/characters/gf_kits.lua'
    candidate[p] = replace(candidate[p], 'return K\n', "require('gf_duo_rework_rules')(K)\nreturn K\n")
    candidate['source/characters/gf_duo_rework_rules.lua'] = '''__loaders['gf_duo_rework_rules']=function()
return function(K)
 local function copy(t) local c={};for k,v in pairs(t) do c[k]=v end;return c end
 K.characterWeapons=K.characterWeapons or {}
 for _,row in ipairs({{'nahida','catalyst'},{'raidenshogun','polearm'}}) do
  local key,base=row[1],K.weapons[row[2]];local w=copy(base)
  local function move(id,from,values)
   local m=copy(base[from]);for k,v in pairs(values) do m[k]=v end;w[id]=m
  end
  if key=='nahida' then
   move('upLight','light1',{startup=6,active=3,recovery=10,damage=25,lunge=0,push=3,box={x=15,y=140,w=135,h=170},fx='burstSmall',cancel={'upHeavy','skill','burst'},reworkSheet='light',reworkFrames={4,5,6,7}})
   move('crouchLight','crouchLight',{startup=5,active=3,recovery=9,damage=23,lunge=0,push=4,box={x=35,y=0,w=145,h=60},fx='burstLow',cancel={'crouchHeavy','skill','burst'},reworkSheet='air',reworkFrames={0,0,1,0}})
   move('crouchHeavy','crouchHeavy',{startup=14,active=5,recovery=23,damage=54,lunge=0,push=4,hitstun=28,box={x=65,y=0,w=205,h=105},fx='burstLow',reworkSheet='air',reworkFrames={2,2,3,2}})
   move('forwardLight','light2',{damage=34,startup=8,recovery=13,lunge=38,box={x=50,y=100,w=190,h=100},reworkSheet='light',reworkFrames={4,5,6,7}})
   move('upHeavy','heavy',{projectile=false,startup=12,active=4,recovery=20,damage=62,launch=22,box={x=20,y=100,w=150,h=240},fx='rise',reworkSheet='heavy',reworkFrames={4,5,6,7}})
   move('light3','light2',{damage=45,startup=9,recovery=17,push=13,box={x=70,y=100,w=190,h=150},cancel={'heavy','skill','burst'},reworkSheet='heavy',reworkFrames={0,1,2,3}})
   w.light2=copy(base.light2);w.light2.cancel={'light3','heavy','skill','burst'}
  else
   move('upLight','light1',{startup=7,active=3,recovery=11,damage=29,lunge=8,push=6,box={x=25,y=160,w=150,h=155},fx='rise',cancel={'upHeavy','skill','burst'},reworkSheet='light',reworkFrames={4,5,6,7}})
   move('crouchLight','crouchLight',{startup=6,active=3,recovery=11,damage=28,lunge=12,push=7,box={x=60,y=0,w=215,h=45},fx='thrustLow',cancel={'crouchHeavy','skill','burst'},reworkSheet='air',reworkFrames={0,0,1,0}})
   move('crouchHeavy','crouchHeavy',{startup=12,active=4,recovery=25,damage=65,lunge=24,push=10,box={x=50,y=0,w=245,h=65},fx='sweep',reworkSheet='air',reworkFrames={2,2,3,2}})
   move('forwardLight','light1',{startup=8,recovery=14,damage=40,lunge=72,box={x=65,y=140,w=215,h=65},reworkSheet='light',reworkFrames={0,1,2,3}})
   move('upHeavy','heavy',{startup=12,recovery=22,damage=70,launch=28,lunge=10,box={x=15,y=100,w=165,h=270},reworkSheet='heavy',reworkFrames={4,5,6,7}})
  end
  K.characterWeapons[key]=w
 end
 K.duoSkillVariants={
  nahida={
   down={style='zone',startup=13,recovery=19,damage=55,cd=140,delay=20,w=160,h=210,fx='capture',hitstun=24,blockstun=14,push=6,level='mid',energy=5,reworkVariant='seed',fixedOffset=240},
   up={style='projectile',startup=10,recovery=20,damage=52,cd=140,speed=10,w=90,h=100,y=230,life=35,fx='orb',hitstun=22,blockstun=14,push=6,level='mid',energy=5,reworkVariant='leaf'},
  },
  raidenshogun={
   down={style='zone',startup=14,recovery=20,damage=65,cd=150,delay=12,w=180,h=260,fx='eye',hitstun=25,blockstun=15,push=7,level='mid',energy=5,reworkVariant='thunder',fixedOffset=180},
   forward={style='rush',startup=10,recovery=22,damage=72,cd=150,speed=22,dur=8,w=160,h=210,fx='eye',hitstun=24,launch=16,reworkVariant='lunge'},
  },
 }
end
end
'''
    p = 'source/battle/gf_sim_actions.lua'
    candidate[p] = replace(candidate[p], "self:startMove(p, nowIn & B.D ~= 0 and 'crouchHeavy' or 'heavy') return", "self:startMove(p, nowIn & B.D ~= 0 and 'crouchHeavy' or (nowIn & B.U ~= 0 and p.kit.weapon.upHeavy) and 'upHeavy' or 'heavy') return")
    candidate[p] = replace(candidate[p], "self:startMove(p, nowIn & B.D ~= 0 and 'crouchLight' or 'light1') return", "self:startMove(p, nowIn & B.D ~= 0 and 'crouchLight' or (nowIn & B.U ~= 0 and p.kit.weapon.upLight) and 'upLight' or (nowIn & f ~= 0 and p.kit.weapon.forwardLight) and 'forwardLight' or 'light1') return")
    candidate[p] = replace(candidate[p], "want = (p.inNow & B.D ~= 0) and 'crouchHeavy' or (p.y > 0 and 'airHeavy' or 'heavy')", "want = (p.inNow&B.D~=0) and 'crouchHeavy' or (p.y>0 and 'airHeavy' or (p.inNow&B.U~=0 and p.kit.weapon.upHeavy and 'upHeavy') or 'heavy')")
    p = 'source/battle/gf_sim_combat.lua'
    candidate[p] = replace(candidate[p], '    local sk = p.kit.skill\n', '''    local variants=K.duoSkillVariants and K.duoSkillVariants[p.key]
    local input=p.inNow or 0
    local sk = variants and p.y<=0 and (input&B.D~=0 and variants.down or input&B.U~=0 and variants.up or input&fwdBit(p)~=0 and variants.forward) or p.kit.skill
''')
    p = 'source/battle/gf_sim_actions.lua'
    candidate[p] = replace(candidate[p], '            pr.x = d.x\n', '            pr.x = sk.fixedOffset and p.x+p.face*sk.fixedOffset*C or d.x\n')
    p = 'source/render/gf_fview.lua'
    candidate[p] = replace(candidate[p], "function V:attackFrames(m,t,id)\n", "function V:attackFrames(m,t,id)\n    if m.reworkSheet then return self:sequence(m.reworkSheet,m.reworkFrames,{math.ceil(m.startup/2),m.startup,m.startup+m.active,m.startup+m.active+m.recovery},t) end\n")
    candidate[p] = replace(candidate[p], "if st=='dash' then return self:sequence('move',{4,5},{5,14},t) end", "if st=='dash' then return self:sequence('move',{4,5},{5,f.kit.body.dashTicks or 14},t) end")
    candidate[p] = replace(candidate[p], "    if st=='skill' then\n        if f.key=='nahida' then", "    if st=='skill' then\n        if f.move.reworkVariant then local su=f.move.startup;return self:sequence('skill',{0,1,2,3},{math.ceil(su/2),su,su+(f.move.dur or 4),su+(f.move.dur or 0)+f.move.recovery},t) end\n        if f.key=='nahida' then")
    candidate[p] = replace(candidate[p], '    local f=self.f;local t,st=f.t,f.state;local idx,width,offset,up\n', "    local f=self.f;local t,st=f.t,f.state;local idx,width,offset,up\n    if st=='skill' and f.move.reworkVariant then self.animFx.node:on(false);self.animFxBack.node:on(false);return end\n")
    candidate[p] = replace(candidate[p], "if f.state~='skill' or f.t<4 then", "if f.state~='skill' or f.t<4 or f.move.reworkVariant then")
    p = 'source/battle/gf_battle_pause.lua'
    candidate[p] = replace(candidate[p], "    L:label(f.char.name, px + 120", "    if K.duoSkillVariants[f.key] then\n        table.insert(rows,4,{'上轻 / 上重',f.key=='nahida' and '叶托 / 草柱；上方向＋轻 / 重' or '枪拨 / 枪挑；上方向＋轻 / 重'})\n        table.insert(rows,5,{'下轻 / 下重',f.key=='nahida' and '草芽 / 根阵；下方向＋轻 / 重' or '低刺 / 扫腿；下方向＋轻 / 重'})\n        table.insert(rows,7,{'战技分支',f.key=='nahida' and '下＋E草种；上＋E叶光；共享冷却' or '下＋E雷区；前＋E突进；共享冷却'})\n    end\n    L:label(f.char.name, px + 120")
    p = 'source/network/gf_online.lua'
    candidate[p] = replace(candidate[p], 'O.VERSION = 8', 'O.VERSION = 10')
    for name,bank in [('before',original),('geometry',perf),('candidate',candidate)]:
        paths=list(order)
        if name=='candidate':paths.insert(-1,'source/characters/gf_duo_rework_rules.lua')
        changed={p:s for p,s in bank.items() if original.get(p)!=s}
        for p,s in changed.items():
            target=OUT/name/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s,encoding='utf-8')
        # Overrides are editable, and every unchanged input is identified by hash.
        code=''.join(bank[p] for p in paths)
        target=OUT/(name+'.lua');target.write_text(code,encoding='utf-8')
        manifest={'kind':name,'offlineCandidate':True,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
                  'overrides':list(changed),'inputs':[{'path':p,'sha256':hashlib.sha256(bank[p].encode()).hexdigest()} for p in paths]}
        (OUT/(name+'-build.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Built baseline, isolated geometry comparison, and protocol 10 two-role prototype.')

if __name__=='__main__':build()
