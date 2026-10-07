from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'dist/projects/raiden-nahida.json';project=json.loads(p.read_text());s=project['assets']['scripts'][0]['source']
if "GF_RELEASE_ID='dual-burst-polish-r21'" not in s:
    s=s.replace('function S:setState(p, st, move, moveId)\n', "function S:setState(p, st, move, moveId)\n    if st~='burst' then p.cinematicConfirmed=false end\n")
    s=s.replace('p.cinematicConfirmed=true;p.invul=160', """p.cinematicConfirmed=true;p.invul=160
                    -- Reserve space for the victim even at the stage wall.
                    p.x=math.max(-WALL+400*C,math.min(WALL-400*C,p.x))
                    d.x=p.x+p.face*330*C""")
    s=s.replace('if t<70 then d.y=math.max(d.y,130*C);d.vx=0 end', 'if t<70 then d.x=p.x+p.face*330*C;d.y=math.max(d.y,130*C);d.vx=0 end')
    s=s.replace("local beat=(t-16)%35;return frameName('qburst',beat<12 and 2 or 3)", """if t<24 or (t>=35 and t<44) or (t>=70 and t<85) then return frameName('qburst',3) end
            return frameName('qburst',t>=85 and 0 or 2)""")
    s=s.replace('elseif t<76 then idx,width,offset,up=9,640,200,10', """elseif t<24 or (t>=35 and t<44) or (t>=70 and t<85) then idx,width,offset,up=9,640,200,10
                elseif t<70 then idx,width,offset,up=5,230,0,110""")
    s=s.replace('local W,H=self.app.W,self.app.H\n        L:rect(0,0,W+40,H+40,{10,5,28},0.94)', """local W,H=self.app.W,self.app.H
        local fade=p.t<85 and 1 or math.max(0,(100-p.t)/15)
        local pulse=(p.t<8 or (p.t>=35 and p.t<44) or (p.t>=70 and p.t<85)) and 1 or 0
        L:rect(0,0,W+40,H+40,{10,5,28},0.94*fade)""")
    s=s.replace('W*0.8,H*0.7,{88,35,150},0.7,0,0.4', 'W*0.8,H*0.7,{88,35,150},(0.55+0.15*pulse)*fade,0,0.4')
    s=s.replace('600,190,{120,58,205},0.7)', '600,190,{120,58,205},(0.5+0.2*pulse)*fade)')
    s=s.replace('150,150,{205,155,255},0.8)', '150,150,{205,155,255},0.8*fade)')
    s=s.replace('55,120,{25,8,50},1)', '55,120,{25,8,50},fade)')
    s=s.replace('5,H,{165,95,250},0.3,-22', '5,H,{165,95,250},(0.2+0.1*pulse)*fade,-22')
    s=s.replace("GF_RELEASE_ID='dual-burst-cinema-r20'", "GF_RELEASE_ID='dual-burst-polish-r21'")
project['meta']['name']='雷电与纳西妲 · 三段演出优化 r21';project['assets']['scripts'][0]['source']=s
p.write_text(json.dumps(project,ensure_ascii=False,separators=(',',':')))
(ROOT/'project-inputs/dual-character.lua').write_text(s)
print('Prepared r21: distinct strikes, victim spacing, cleanup and backdrop fade')
