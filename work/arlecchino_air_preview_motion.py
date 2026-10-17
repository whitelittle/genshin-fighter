from pathlib import Path
p=Path('outputs/arlecchino-actions-20261011/player.js');s=p.read_text(encoding='utf-8')
if 'function rootY()' not in s:
 s=s.replace("let selected='idle'", "let entryRootX=520;\nlet selected='idle'")
 start=s.index('const i=phase(),jump=');end=s.index(';ctx.save()',start)
 s=s[:start]+"const i=phase(),y=rootY(),x=entryRootX+($('movement').checked&&active.motion?.kind==='walk'?active.motion.direction*active.motion.distance*time/total:0)"+s[end:]
 helper="""function rootY(){const m=active?.motion;if(!$('movement').checked)return 550;if(m?.kind==='jump'){const u=Math.min(1,Math.max(0,(time-m.takeoffTick)/(m.landingTick-m.takeoffTick)));return 550-m.height*Math.sin(Math.PI*u)}if(m?.kind==='air'){const u=Math.min(1,Math.max(0,time/m.landingTick));return 550-active.airStartHeight*(1-u*u)}return 550}\n"""
 s=s.replace('function render()',helper+'function render()')
 s=s.replace('async function choose(key){const v=++version;',"async function choose(key){const previousActive=active,previousState=active?JSON.parse($('cv').dataset.preview):null;const v=++version;")
 s=s.replace('active={...d,sequence,images};selected=key;',"const inheritAir=d.motion?.kind==='air'&&previousState?.selected==='jump'&&previousState.root[1]<549;entryRootX=previousState?.selected===key?entryRootX:inheritAir?previousState.root[0]:520;active={...d,sequence,images,airStartHeight:previousState?.selected===key?(previousActive.airStartHeight||d.motion?.height):inheritAir?550-previousState.root[1]:(d.motion?.height||0),airRootSource:inheritAir?'jump-current-root':'standalone-demo'};selected=key;")
 s=s.replace('root:[x,y]','root:[x,y],airRootSource:active.airRootSource')
 p.write_text(s,encoding='utf-8')
p=Path('outputs/arlecchino-actions-20261011')
for f in [p/'player.html',p/'index.html']:
 s=f.read_text(encoding='utf-8').replace('12组/58姿','15组/78姿');f.write_text(s,encoding='utf-8')
