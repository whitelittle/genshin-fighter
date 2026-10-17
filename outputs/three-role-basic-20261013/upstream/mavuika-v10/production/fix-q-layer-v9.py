from pathlib import Path
import json
r=Path(__file__).resolve().parents[1];d=r/'dist';a=d/'assets'
rig=json.loads((a/'rig.json').read_text());(r/'production/q-rig-before-v9.json').write_text(json.dumps(rig))
for pose,anchor in [('ride',[155,501]),('brake',[650,510])]:
 rig['poses'][pose]['anchor']=anchor
 for mode,b in rig['materials'].items():b['poses'][pose]['anchor']=anchor if mode=='source' else [v*.42/4 for v in anchor]
(a/'rig.json').write_text(json.dumps(rig,ensure_ascii=False,indent=2)+'\n')
p=d/'q-model.js';s=p.read_text();s=s.replace("const p=clamp((t-74)/24);return {x:mix(o.x+330,o.x,p),y:mix(o.y-40,o.y,p),pose:t>=98?'idle':'slash'};", "const p=clamp((t-74)/24);return {x:mix(o.x+330,o.x,p),y:o.y,pose:t>=98?'idle':'slash'};")
# Touchdown at frame 74: feet on floor; Q returns on foot with sword, never a bike.
p.write_text(s)
s=(d/'q-fx-model-v8.js').read_text();s=s.replace("ride:{wheel:[155,488]},brake:{wheel:[645,500]},windup:{grip:[413,24],tip:[15,80]},slash:{grip:[413,357],tip:[733,487]}","ride:{wheel:[155,501],contact:[700,280]},brake:{wheel:[650,510],contact:[680,450]},windup:{grip:[413,24],guard:[333,28],tip:[15,80]},slash:{grip:[386,350],guard:[433,360],tip:[734,486]}")
s=s.replace('ride:[280,496],brake:[645,500]', 'ride:[155,501],brake:[650,510]')
s=s.replace("const add=(id,p,alpha=1,bank='q',mult=1)=>layers.push({id,...p,alpha,bank,mult});", "const add=(id,p,alpha=1,bank='q',mult=1,plane='rear',rotation=0)=>layers.push({id,...p,alpha,bank,mult,plane,rotation});\n const blade=(body)=>{const g=point(body,'guard'),tip=point(body,'tip');return {g,rotation:Math.atan2(tip.y-g.y,tip.x-g.x)-Math.atan2(290,340)};};")
s=s.replace("add('charge',point(c,'grip'),.4+(t-36)/19*.5)","add('charge',point(c,'guard'),.35+(t-36)/19*.35,'q',.65,'front')")
# Anticipation is at overhead blade guard, does not shoot down-right out of lifted grip.
s=s.replace("add('blade-prepare',point(c,'grip'),.5)","add('charge',point(c,'guard'),.3,'q',.85,'front')")
s=s.replace("if(t>=55&&t<62)add('slash',point(c,'grip'),.85-(t-55)*.07);", "if(t>=55&&t<62){const b=blade(c);add('slash',b.g,.65-(t-55)*.06,'q',.50,'rear',b.rotation);}")
s=s.replace("add('slash-residue',point(start,'grip'),(74-t)/12*.5);", "const b=blade(start);add('slash-residue',b.g,(74-t)/12*.3,'q',.5,'rear',b.rotation);")
s=s.replace("add('wheel-trail',wheel,.65)","add('wheel-trail',wheel,.55,'q',.72)").replace("add('wheel-trail',point(c,'wheel'),.72)","add('wheel-trail',point(c,'wheel'),.55,'q',.72)")
s=s.replace("add('brake-sparks',wheel,.7-(t-12)*.03)","add('brake-sparks',wheel,.6-(t-12)*.03,'q',.75,'ground')").replace("add('skid-residue',wheel,(42-t)/17*.45)","add('skid-residue',wheel,(42-t)/17*.35,'q',.75,'ground')")
start=s.index("const p=s.action==='q'&&contact.kind==='hit'?");end=s.index('\n   if(age',start)
s=s[:start]+"const at=Q.choreography(Q.seek('hit',contact.tick,s.action,s.origin));const p=s.action==='q'&&contact.kind==='hit'?point(at,'tip'):point(at,'contact');"+s[end:]
s=s.replace("p,(10-age)/10,'light')", "p,(10-age)/10*.75,'light',.8,'front')").replace("p,(10-age)/10,'q',s.action==='q'?1:.7)","p,(10-age)/10*.65,'q',s.action==='q'?.55:.4,'front')")
# Full receiver white flash masked by selecting restrained overlay alpha in renderer.
s=s.replace("root.QFX=api", "root.QFX=api")
(d/'q-fx-model-v9.js').write_text(s)
# renderer explicit rear / ground / actor depth / front ordering
p=d/'app.js';s=p.read_text().replace('function drawFx(){for',"function drawFx(plane){for").replace("const bank=l.bank==='light'?", "if(l.plane!==plane)continue;const bank=l.bank==='light'?")
s=s.replace("stamp(l.bank==='light'?lightFxArt:fxArt,p,l.x,l.y,p.scale*l.mult,l.alpha*($('reduced').checked?.55:1));", "ctx.save();ctx.translate(l.x,l.y);ctx.rotate(l.rotation||0);stamp(l.bank==='light'?lightFxArt:fxArt,p,0,0,p.scale*l.mult,l.alpha*($('reduced').checked?.55:1));ctx.restore();")
s=s.replace('p.scale,.45)', 'p.scale,.2)')
s=s.replace('  drawTarget(t);','  drawFx(\'rear\');\n  drawFx(\'ground\');\n  const presentation=QFX.frame(model),targetInFront=presentation.receiver.x>=presentation.body.x;\n  if(!targetInFront)drawTarget(t);')
s=s.replace('  drawFx();', "  if(targetInFront)drawTarget(t);\n  drawFx('front');")
s=s.replace('V8 独立太阳／刀光／轮胎火尾／接触特效','V9 后景太阳与火尾／剑身刀光／低位接触层／徒步落地')
p.write_text(s)
p=d/'index.html';s=p.read_text().replace('候选 · 08','候选 · 09').replace('q-fx-model-v8.js','q-fx-model-v9.js').replace('mavuika-q-fx-offline-v8','mavuika-q-fx-offline-v9').replace('mavuika-q-fx-v8.gif','mavuika-q-fx-v9.gif').replace('mavuika-bike-fx-v8.gif','mavuika-bike-fx-v9.gif');p.write_text(s)
