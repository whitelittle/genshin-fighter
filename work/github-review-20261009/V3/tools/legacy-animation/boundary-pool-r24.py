from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if 'function G.requestImageRetirement()' not in s:
 s=s.replace('batch=32, limit=18000','batch=32, limit=20000, floor=14000, warning=2000, reserve=3500, destroyed=0, emergencies=0, warnings=0, retiring=false')
 s=s.replace('        n.pool, n.secondPool, n.act = true, true, false', '        n.pool, n.secondPool, n.act = true, true, false\n        n.dynamicExtra=G.counts.img>=growth.floor')
 s=s.replace("    if not n then error('image pool exhausted; capacity='..G.counts.img, 2) end", """    if not n and G.emergencyImages and G.emergencyImages() then n=table.remove(freeSecond) end
    if not n then error('image pool exhausted; capacity='..G.counts.img, 2) end""")
 start=s.index('function G.secondPoolStatus()');end=s.index('\nreturn G',start)
 s=s[:start]+'''function G.emergencyImages()
    if not growth.templateIndex or G.counts.img>=growth.limit then return false end
    growth.target=math.min(growth.limit,math.max(growth.target,G.counts.img+64))
    G.growImages();G.growImages();growth.emergencies=growth.emergencies+1
    return #freeSecond>0
end
function G.requestImageRetirement()
    growth.retiring=true;growth.reclaimed=false
end
function G.manageImagePool(phase, safeBoundary)
    if not growth.templateIndex or G.counts.img<growth.floor then return end
    local free=#freeImg+#freeSecond
    if free<growth.warning then
        growth.target=math.min(growth.limit,math.max(growth.target,G.counts.img-free+growth.reserve))
        growth.warnings=growth.warnings+1
    end
    -- A warning creates immediately; remaining growth is spread across frames.
    if G.counts.img<growth.target then G.growImages();G.growImages() end
    -- Shrink is impossible during combat, even when all extra controls are idle.
    if not growth.retiring or phase=='fight' or not safeBoundary or G.pending()>0 then return end
    if not growth.reclaimed then G.reclaimDormant();growth.reclaimed=true end
    free=#freeImg+#freeSecond
    local removable=math.min(32,G.counts.img-growth.floor,math.max(0,free-growth.reserve))
    if removable<=0 then
        if G.counts.img<=growth.floor then growth.retiring=false end
        return
    end
    local removed=0
    for i=#freeSecond,1,-1 do
        local n=freeSecond[i]
        -- Destroy only surplus leaf controls; group hierarchies are retained.
        if n.dynamicExtra and not n.kids and not n.tw and not n.queued then
            local ok=pcall(game.DestroyClientUIControl,n.c)
            if ok then
                table.remove(freeSecond,i);n.dead=true;n.c=nil
                G.counts.img=G.counts.img-1;growth.destroyed=growth.destroyed+1;removed=removed+1
            end
            if removed>=removable then break end
        end
    end
    growth.target=math.max(growth.floor,G.counts.img)
    if G.counts.img<=growth.floor then growth.retiring=false end
end
function G.secondPoolStatus()
    return {first=growth.first, created=growth.created, total=G.counts.img,
            target=growth.target, batch=growth.batch, templateIndex=growth.templateIndex,
            floor=growth.floor,limit=growth.limit,warning=growth.warning,reserve=growth.reserve,
            destroyed=growth.destroyed,emergencies=growth.emergencies,warnings=growth.warnings,
            retiring=growth.retiring,freeFirst=#freeImg, freeSecond=#freeSecond}
end
''' +s[end:]
 s=s.replace('function App:update(dt)\n    if self:advanceScenePool() then return end', '''function App:update(dt)
    if self:advanceScenePool() then return end
    local sim=self.scene and self.scene.sim
    local phase=sim and sim.phase
    local safeBoundary=not sim or phase=='over' or (phase=='ko' and sim.phaseT>=90)
    G.manageImagePool(phase,safeBoundary)''')
 s=s.replace("        elseif ty == 'roundEnd' then\n            self:roundEndFx(e)", "        elseif ty == 'roundEnd' then\n            G.requestImageRetirement()\n            self:roundEndFx(e)")
 s=s.replace("        elseif ty == 'matchEnd' then", "        elseif ty == 'matchEnd' then\n            G.requestImageRetirement()")
 s=s.replace("GF_RELEASE_ID='nahida-preview-pool-r23'", "GF_RELEASE_ID='preview-boundary-pool-r24'")
 j['meta']['name']='雷电与纳西妲 · 预警扩容与回合回收 r24';j['assets']['scripts'][0]['source']=s
 p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
print('r24: warning creates immediately; retirement only after round/match; baseline 14000')
