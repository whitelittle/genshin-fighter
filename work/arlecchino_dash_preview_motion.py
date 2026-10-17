from pathlib import Path
p=Path('outputs/arlecchino-actions-20261011/player.js');s=p.read_text(encoding='utf-8')
if 'function rootX()' not in s:
 helper="""function rootX(){const m=active?.motion;if(!$('movement').checked)return entryRootX;if(m?.kind==='walk')return entryRootX+m.direction*m.distance*time/total;if(m?.kind==='dash'){const u=Math.min(1,Math.max(0,(time-m.beginTick)/(m.endTick-m.beginTick)));return entryRootX+m.distance*u}return entryRootX}\n"""
 s=s.replace('function rootY()',helper+'function rootY()')
 s=s.replace("return 550-active.airStartHeight*(1-u*u)}return 550}","return 550-active.airStartHeight*(1-u*u)}if(m?.kind==='dash'&&m.height){const u=Math.min(1,Math.max(0,(time-m.beginTick)/(m.endTick-m.beginTick)));return 550-m.height*Math.sin(Math.PI*u)}return 550}")
 s=s.replace("x=entryRootX+($('movement').checked&&active.motion?.kind==='walk'?active.motion.direction*active.motion.distance*time/total:0)",'x=rootX()')
 p.write_text(s,encoding='utf-8')
p=Path('outputs/arlecchino-actions-20261011')
for f in [p/'player.html',p/'index.html']:
 s=f.read_text(encoding='utf-8').replace('15组/78姿','19组/100姿');f.write_text(s,encoding='utf-8')
