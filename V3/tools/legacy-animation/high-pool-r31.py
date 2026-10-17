from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];p=R/'dist/projects/raiden-nahida.json';j=json.loads(p.read_text());s=j['assets']['scripts'][0]['source']
if "job.target=='lo' then\n        G.flushTrash" in s:
 print('Quality pool patch already installed');raise SystemExit
s=s.replace('batch=32, limit=20000, floor=14000','batch=32, limit=32000, floor=14000')
if 'function G.setQualityPool(q)' not in s:
 s=s.replace('function G.requestImages(target)', '''function G.setQualityPool(q)
    local baseline=q=='hi' and 24000 or 14000
    growth.floor=baseline
    growth.target=math.max(baseline,G.counts.img-(#freeImg+#freeSecond)+growth.reserve)
    growth.retiring=q~='hi' and G.counts.img>baseline
    growth.reclaimed=false
    return baseline
end
function G.requestImages(target)''',1)
s=s.replace('self.qualityLoad={target=q,entries=entries,i=0}', '''local baseline=G.setQualityPool(q)
    self.qualityLoad={target=q,entries=entries,i=0,poolStart=G.secondPoolStatus().total,poolGoal=baseline}''')
s=s.replace('local progress=job.i/math.max(1,#job.entries);local L=', '''for _=1,4 do G.growImages() end
    local pool=G.secondPoolStatus()
    local poolProgress=math.min(1,math.max(0,(pool.total-job.poolStart)/math.max(1,job.poolGoal-job.poolStart)))
    if pool.total>=job.poolGoal then poolProgress=1 end
    local progress=(job.i/math.max(1,#job.entries)+poolProgress)/2;local L=''')
s=s.replace('if job.i>=#job.entries then','if job.i>=#job.entries and pool.total>=job.poolGoal then',1)
s=s.replace('if n.dynamicExtra and not n.kids and not n.tw and not n.queued then','if not n.kids and not n.tw and not n.queued then')
s=s.replace('n.dynamicExtra=G.counts.img>=growth.floor','n.dynamicExtra=G.counts.img>=14000')
s=s.replace('for _=1,4 do G.growImages() end', '''if job.target=='lo' then
        G.flushTrash(400)
        for _=1,4 do G.manageImagePool(nil,true) end
    else
        for _=1,4 do G.growImages() end
    end''')
s=s.replace('local poolProgress=math.min(1,math.max(0,(pool.total-job.poolStart)/math.max(1,job.poolGoal-job.poolStart)))', '''local poolProgress=math.min(1,math.max(0,(pool.total-job.poolStart)/math.max(1,job.poolGoal-job.poolStart)))
    if job.target=='lo' then poolProgress=math.min(1,math.max(0,(job.poolStart-pool.total)/math.max(1,job.poolStart-job.poolGoal))) end''')
s=s.replace('if pool.total>=job.poolGoal then poolProgress=1 end', "if (job.target=='hi' and pool.total>=job.poolGoal) or (job.target=='lo' and pool.total<=job.poolGoal) then poolProgress=1 end")
s=s.replace('if job.i>=#job.entries and pool.total>=job.poolGoal then', "if job.i>=#job.entries and ((job.target=='hi' and pool.total>=job.poolGoal) or (job.target=='lo' and pool.total<=job.poolGoal)) then")
j['assets']['scripts'][0]['source']=s;p.write_text(json.dumps(j,ensure_ascii=False,separators=(',',':')));(R/'project-inputs/dual-character.lua').write_text(s)
print('HD loading prewarms 24000 primitives, low 14000; exceptional ceiling 32000')
