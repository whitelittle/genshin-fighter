from pathlib import Path
p=Path('work/arlecchino_pairing_profiles.py');s=p.read_text(encoding='utf-8').replace("['sourceFrames'][i],h,models[model][key]", "['sourceFrames'][[0,2][i]],h,models[model][key]");p.write_text(s,encoding='utf-8')
p=Path('outputs/arlecchino-actions-20261011/player-v2.js');s=p.read_text(encoding='utf-8')
s=s.replace("function root(){", "function victimOrigin(){const c=pairs.victim?.[active.model]?.['1'];if(!c)return entryX;const n=active.foeData[c.targetKey],f=active.sourceFrames[2];return entryX+220-(c.target[0]-n.ax)*n.scale-(c.caster[0]-f.anchor[0])*f.scale}\nfunction root(){")
s=s.replace("if(selected==='victim'){if(p===2){x-=70*u;y-=90*u}if(p===3){x-=70+90*u;y-=90*(1-u)}if(p>=4)x-=160}", "if(selected==='victim'){const origin=victimOrigin();if(p===2)x=origin;if(p===3){x=origin-70*u;y-=90*u}if(p===4){x=origin-70-90*u;y-=90*(1-u)}if(p>=5)x=origin-160}")
start=s.index(" if(selected==='victim'){key=");end=s.index("\n if(selected==='Q'",start)
s=s[:start]+" if(selected==='victim'){key='throw_'+[0,0,1,2,3,3][Math.min(p,5)];x=entryX+220;if(p===2){const c=pairs.victim?.[active.model]?.['1'];if(c){key=c.targetKey;const n=active.foeData[key],grip=point(c.caster,active.sourceFrames[p],actor);contact={caster:grip,target:[x-(c.target[0]-n.ax)*n.scale,550+(c.target[1]-n.ay)*n.scale],kind:c.kind}}}}"+s[end:]
s=s.replace("previous.phase===5&&previous.root[1]>=549", "previous.frameFile===(material==='source'?bank.wakeup.sourceFrames[1]:bank.wakeup.frames[1]).file&&previous.root[1]>=549")
s=s.replace("if(time>=42&&time<142)effect('wings',x,y-220,time<52?(time-42)/10:time>=132?(142-time)/10:.8);",'')
p.write_text(s,encoding='utf-8')
