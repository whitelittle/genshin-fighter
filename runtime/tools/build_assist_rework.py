"""Editable assist overlay on the two-role prototype, with explicit 2nd/4th selection."""
from pathlib import Path
import hashlib,json
from build_duo_rework import build,replace,ROOT,OUT

def main():
 build()
 manifest=json.loads((OUT/'candidate-build.json').read_text(encoding='utf-8'))
 paths=[q['path'] for q in manifest['inputs']]
 bank={p:(OUT/'candidate'/p if (OUT/'candidate'/p).exists() else ROOT/p).read_text(encoding='utf-8') for p in paths}
 original=dict(bank)
 def patch(p,old,new):bank[p]=replace(bank[p],old,new)
 # Restore upward input to jumping / aerial moves, and keep character-specific lows.
 p='source/characters/gf_duo_rework_rules.lua'
 bank[p]='\n'.join(line for line in bank[p].split('\n') if "move('upLight'" not in line and "move('upHeavy'" not in line)
 p='source/battle/gf_sim_actions.lua'
 bank[p]=bank[p].replace("or (nowIn & B.U ~= 0 and p.kit.weapon.upHeavy) and 'upHeavy' ",'')
 bank[p]=bank[p].replace("or (nowIn & B.U ~= 0 and p.kit.weapon.upLight) and 'upLight' ",'')
 patch(p,'    -- burst > skill > throw > attacks > dash > jump > move', '''    if nowIn&B.U~=0 and pr&(B.LP|B.HP)~=0 and pr&(B.SK|B.BU|B.TH)==0 then
        self:setState(p,'jumpsq');p.jumpAttack=pr&B.HP~=0 and 'airHeavy' or 'airLight'
        p.jumpDir=nowIn&f~=0 and 1 or nowIn&bk~=0 and -1 or 0
        return
    end
    -- burst > skill > throw > attacks > dash > jump > move''')
 p='source/battle/gf_sim_fighter.lua'
 patch(p,"            self:setState(p, 'air')\n            p.vy = 24 * C", "            local queued=p.jumpAttack\n            self:setState(p, 'air')\n            p.jumpAttack=nil\n            p.vy = 24 * C")
 patch(p,"            self:emit({type = 'jump', p = p.id})", "            self:emit({type = 'jump', p = p.id})\n            if queued then self:startMove(p,queued) end")
 # The 11th bit is a new action, never aliased to a throw or another skill.
 for p in ['source/input/gf_input.lua','source/battle/gf_sim.lua']:
  patch(p,'DA = 256, TH = 512}', 'DA = 256, TH = 512, AS = 1024}')
 p='source/input/gf_input.lua'
 patch(p,"    {ck('U'), 1, B.DA}, {ck('L'), 1, B.TH},", "    {ck('U'), 1, B.DA}, {ck('L'), 1, B.TH}, {ck('G'),1,B.AS}, {ck('V'),2,B.AS},")
 patch(p,'        pad.pulse = 0', "        if self.dev=='pad' and now&(B.DA|B.HP)==(B.DA|B.HP) then now=(now&~(B.DA|B.HP))|B.AS end\n        pad.pulse = 0")
 p='source/network/gf_net.lua'
 patch(p,'N.BITS = 10', 'N.BITS = 11')
 patch(p,'N.PER_INT = 3', 'N.PER_INT = 2')
 p='source/battle/gf_sim.lua'
 patch(p,'p.releaseMask=ins[i] & 1008', 'p.releaseMask=ins[i] & 2032')
 patch(p,"    p.state, p.t = st, 0", "    if st~='jumpsq' then p.jumpAttack=nil end\n    p.state, p.t = st, 0")
 patch(p,'    -- super freeze: only the caster', "    if self.phase=='fight' and self.freeze<=0 then\n        for i,p in ipairs(self.f)do if p.inPressed&B.AS~=0 then self:callAssist(i) end end\n    end\n    -- super freeze: only the caster")
 patch(p,'    self:updateProj()', '    self:updateAssists()\n    self:updateProj()')
 patch(p,"S.C = C", "require('gf_sim_assist')(S,ctx)\nS.C = C")
 # Packet remains 24 integers; widened inputs use two 11-bit masks per integer.
 p='source/network/gf_online.lua'
 patch(p,'O.VERSION = 10','O.VERSION = 11')
 patch(p,'function O.lobbyWord(char, ready, selecting, teamMode)', 'function O.lobbyWord(char, ready, selecting, teamMode,assist)')
 patch(p,'| (O.VERSION << 8)', '| (O.VERSION << 8) | (((assist or 0)&31)<<12)')
 patch(p,'version = (w >> 8) & 15}', 'version = (w >> 8) & 15,assist=(w>>12)&31}')
 patch(p,'function O.rosterWord(sa, sb, ca, cb) return', 'function O.rosterWord(sa, sb, ca, cb, aa, ab) return')
 patch(p,'((cb & 31) << 13) end','((cb & 31) << 13) | (((aa or 0)&31)<<18) | (((ab or 0)&31)<<23) end')
 patch(p,'chars = {(w >> 8) & 31, (w >> 13) & 31}}','chars = {(w >> 8) & 31, (w >> 13) & 31},assists={(w>>18)&31,(w>>23)&31}}')
 patch(p,'o.me.selecting,o.me.teamMode)', 'o.me.selecting,o.me.teamMode,o.me.assist)')
 patch(p,'local simOpts = makeSimOpts(r.chars, setup, seed)', "local simOpts = makeSimOpts(r.chars, setup, seed)\n    local R=require('gf_roster')\n    simOpts.assistChars=simOpts.assistChars or {R[r.assists[1]],R[r.assists[2]]}")
 patch(p,'math.max(1, o.peers[opp].lobby.char))','math.max(1, o.peers[opp].lobby.char),o.me.assist,o.peers[opp].lobby.assist)')
 patch(p,'    local rw = O.rosterWord', "    local revealed=o.teamDraft and o.teamDraft.reveal\n    if revealed then o.me.assist=revealed[o.slot][4];o.peers[opp].lobby.assist=revealed[opp][4] end\n    local rw = O.rosterWord")
 # Local and online single-character selection gets a second pick per side.
 p='source/menu/gf_scene_select.lua'
 patch(p,'local mine = self.roster[self.cur[1]].key', 'local mine = self.roster[self.mainChoice[1] or self.cur[1]].key')
 patch(p,'chars = {mine, self.roster[self.cur[2]].key}', 'chars = {mine, self.roster[self.mainChoice[2] or self.cur[2]].key},assistChars={self.roster[self.assistChoice[1]].key,self.roster[self.assistChoice[2]].key}')
 patch(p,'self.net.me.char=self.cur[1]', 'self.net.me.char=self.mainChoice[1] or self.cur[1]')
 patch(p,'elseif self.done[2] and not self.twoP then self.done[2] = false\n                elseif self.done[1] then self.done[1] = false', 'elseif self:undoAssistPick() then')
 patch(p,"self.net.me.ready=false; self.done[1]=false; self.phase='chars'", "self.net.me.ready=false;self:undoAssistPick();self.phase='chars'")
 patch(p,"    L:label('选择角色', headerX", "    local pickTitle=self.teams and (#self.teams[1]==3 and '第4选 · 协同角色' or '选择出战阵容') or ((self.pickCount[infoPlayer or self:activePlayer() or 1] or 0)==1 and '第2选 · 协同角色' or '第1选 · 主角色')\n    L:label(pickTitle, headerX")
 patch(p,"    L:finish()\nend\n\nfunction S:exit()", "    if not self.teams then local p=self:activePlayer() or 1;local main=self.mainChoice[p];local assist=self.assistChoice[p];L:label((main and ('主角色 '..self.roster[main].name) or '先选主角色')..'  ·  '..(assist and ('协同 '..self.roster[assist].name) or '再选协同角色'),0,H/2-132,900,32,20,UI.GOLD,'c') end\n    L:finish()\nend\n\nfunction S:exit()")
 patch(p,'return S\nend', "require('gf_select_assist')(S)\nreturn S\nend")
 # Four selection entries; only the first three become carrousel fighters.
 p='source/menu/gf_scene_team_select.lua'
 patch(p,'    local originalArgs=self.args', "    local originalArgs=self.args\n    if originalArgs.teamOnline and not originalArgs.teamMatched then self.app:travel('online',{teamOnline=true});return end")
 for old,new in [('<3','<4'),('==3','==4'),('>=3','>=4'),('for n=1,3','for n=1,4'),('/3','/4')]:bank[p]=bank[p].replace(old,new)
 bank[p]=bank[p].replace("L:label(tostring(n),sx", "L:label(n==4 and '协' or tostring(n),sx")
 bank[p]=bank[p].replace("('选择第'..(#self.teams[1]+1)..'位')", "(#self.teams[1]==3 and '第4选：协同角色' or ('选择第'..(#self.teams[1]+1)..'位'))")
 bank[p]=bank[p].replace('220+3*step','220+4*step')
 bank[p]=bank[p].replace('self.built<6','self.built<8').replace('self.built==6','self.built==8')
 bank[p]=bank[p].replace('(self.built-1)//3+1','(self.built-1)//4+1').replace('(self.built-1)%3+1','(self.built-1)%4+1').replace('(p-1)*3+n','(p-1)*4+n')
 bank[p]=bank[p].replace('(W/2-180)/3','(W/2-180)/4').replace('(n-2)*step','(n-2.5)*step')
 patch(p,'for side=1,2 do for n,id in ipairs(self.teams[side])do teams[side][n]=R[id] end end', 'local assists={}\n    for side=1,2 do for n=1,3 do teams[side][n]=R[self.teams[side][n]] end;assists[side]=R[self.teams[side][4]] end')
 patch(p,'local args={mode=\'team\',teamMode=true,teamRoster=teams,', "local args={mode='team',teamMode=true,teamRoster=teams,assistChars={assists[1].key,assists[2].key},")
 patch(p,'net.me.char=self.teams[net.slot][1];', 'net.me.assist=self.teams[net.slot][4];net.me.char=self.teams[net.slot][1];')
 patch(p,'return {teams=teams,chars=', 'return {teams=teams,assistChars=assists,chars=')
 patch(p,"L:label(tostring(n),x,y-120", "L:label(n==4 and '协同' or tostring(n),x,y-120")
 # Only the new GFV2 match-first team lobby is extended. Old GF3 graphs stay historical.
 p='source/network/gf_team_lobby.lua'
 for old,new in [('#team>3','#team>4'),('#team~=3','#team~=4'),('flags>11','flags>12'),('count>3','count>4'),('count~=3','count~=4'),('roles(p[F.seed],3)','roles(p[F.seed],4)')]:bank[p]=bank[p].replace(old,new)
 # Visible call key, readiness and remaining cooldown.
 p='source/input/gf_touch.lua'
 patch(p,'BU = 128, DA = 256}', 'BU = 128, DA = 256, AS = 1024}')
 patch(p,"        {id = 'LP',", "        {id = 'AS',bit=B.AS,label='协同',x=rx-300,y=ry+200,r=48},\n        {id = 'LP',")
 patch(p,"if btn.id == 'SK' or btn.id == 'BU' then", "if btn.id == 'SK' or btn.id == 'BU' or btn.id=='AS' then")
 patch(p,"        if b.id == 'BU' then", "        if b.id=='AS' then\n            local sim=app.scene.sim;ready=sim:assistPartner(self.f.id)~=nil and sim.assistCd[self.f.id]<=0\n            txt=ready and nil or sim:assistPartner(self.f.id)==nil and '无队友' or ('协同\\n%.1f'):format(sim.assistCd[self.f.id]/60)\n        elseif b.id == 'BU' then")
 p='source/render/gf_hud.lua'
 patch(p,"state='当前动作不能释放'", "state='当前动作不能释放',assistState='当前状态不能呼叫',assistCooldown='协同冷却中',noPartner='未选择协同角色'")
 patch(p,'for _, bit in ipairs({64, 128})', 'for _, bit in ipairs({64, 128, 1024})')
 patch(p,'        app.input:moveArea(self.skillAreas[2],', '        app.input:moveArea(self.skillAreas[3],self.skillSide*300,gy+80,180,64)\n        app.input:moveArea(self.skillAreas[2],')
 patch(p,'        -- combo counter', "        local ally=sim:assistPartner(i);local cd=sim.assistCd[i]\n        local text=ally and ('协同 '..ally.name..(cd>0 and (' · %.1f秒'):format(cd/60) or ' · 就绪')) or '未选协同角色'\n        local ax,ay=side*300,cm and (barY-200) or (-Hh/2+150)\n        UI.parallelogram(L,ax,ay,320,38,UI.NAVY,.8,UI.GOLD)\n        L:label(text,ax,ay,320,38,18,UI.CREAM,'c')\n        if not cm then L:label(i==1 and 'G 呼叫' or 'V 呼叫',ax,ay+36,180,28,17,UI.GOLD,'c') end\n        -- combo counter")
 p='source/battle/gf_scene_fight.lua'
 patch(p,'infinite = args.infinite,teams=args.teamRoster}', 'infinite = args.infinite,teams=args.teamRoster,assistChars=args.assistChars}')
 patch(p,'    G.endBitmapBudget()', "    G.bitmapOwner(480);require('gf_assist_view').draw(self)\n    G.endBitmapBudget()")
 patch(p,"    if self.views then for _, v in ipairs(self.views) do v:free() end end", "    require('gf_assist_view').free(self)\n    if self.views then for _, v in ipairs(self.views) do v:free() end end")
 p='source/battle/gf_battle_loading.lua'
 patch(p,'    -- App may run four simulation ticks per host update.', '    if G.retiredPending()>0 then return false end\n    -- App may run four simulation ticks per host update.')
 patch(p,'        self:camera(true)', "        if not require('gf_assist_view').prepare(self,240) then reserved=false end\n        self:camera(true)")
 p='source/battle/gf_battle_events.lua'
 patch(p,"            if e.kind == 'burst' then au:hit", "            if e.kind=='assist' then au:hit(e.element,'elem')\n            elseif e.kind == 'burst' then au:hit")
 p='source/battle/gf_battle_pause.lua'
 start=bank[p].index('    if K.duoSkillVariants[f.key] then')
 end=bank[p].index('    L:label(f.char.name',start)
 bank[p]=bank[p][:start]+'''    table.insert(rows,4,{'协同攻击',mobile and '协同按钮；8秒冷却' or pad and '冲刺＋重攻；8秒冷却' or '1P G / 2P V；8秒冷却'})
    if K.duoSkillVariants[f.key] then
        table.insert(rows,5,{'角色招式','上＋攻击起跳空攻；下＋攻击低段'})
        table.insert(rows,7,{'战技分支',f.key=='nahida' and '下＋E草种；上＋E叶光；共享冷却' or '下＋E雷区；前＋E突进；共享冷却'})
    end
''' + bank[p][end:]
 # Store all editable overrides, then assemble new modules before the bootstrap.
 addons=['source/characters/gf_assist_rules.lua','source/battle/gf_sim_assist.lua','source/render/gf_assist_view.lua','source/menu/gf_select_assist.lua']
 for p in addons:bank[p]=(ROOT/p).read_text(encoding='utf-8');paths.insert(-1,p)
 dest=OUT/'assist'
 for p,s in bank.items():
  if original.get(p)!=s:
   target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(s,encoding='utf-8')
 code=''.join(bank[p] for p in paths);target=OUT/'assist.lua';target.write_text(code,encoding='utf-8')
 report={'protocol':11,'inputBits':11,'integersPerPacket':24,'framesPerInputInteger':2,
         'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'inputs':[{'path':p,'sha256':hashlib.sha256(bank[p].encode()).hexdigest()} for p in paths]}
 (OUT/'assist-build.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('Built explicit assist selection and 11-bit deterministic call input, protocol 11.')

if __name__=='__main__':main()
