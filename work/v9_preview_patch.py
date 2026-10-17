from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];N=R/'outputs/three-role-basic-20261013/neuvillette'
p=N/'player.html';s=p.read_text(encoding='utf-8')
if 'id="baseline"' not in s:s=s.replace('<label><input id="body"','<label><input id="baseline" type="checkbox" checked>待机对照</label><label><input id="body"')
p.write_text(s,encoding='utf-8')
p=N/'player.js';s=p.read_text(encoding='utf-8')
s=s.replace('root=[460,550]','root=[$("baseline").checked?670:460,550]')
needle='ctx.fillStyle=$(\'background\').value'
s=s.replace(needle,'if(active.motion&&$("movement").checked){const u=time/total;if(active.motion.kind==="jump")root[1]-=active.motion.height*Math.sin(Math.PI*u);if(active.motion.kind==="dash")root[0]+=active.motion.direction*active.motion.distance*(u*u*(3-2*u));}'+needle)
s=s.replace('if($(\'body\').checked)draw(ctx,active.images[p],f,...root);','if($(\'baseline\').checked)draw(ctx,active.idleImage,active.idleFrame,180,550);if($(\'body\').checked)draw(ctx,active.images[p],f,...root);')
s=s.replace('effectImages:Object.fromEntries(effects)}','effectImages:Object.fromEntries(effects),idleFrame:bank.idle[material==="source"?"sourceFrames":"frames"][0],idleImage:await load(bank.idle[material==="source"?"sourceFrames":"frames"][0].file)}')
s=s.replace("['material','speed','background','body','fx','loop','mirror','anchors']","['material','speed','background','body','fx','loop','mirror','anchors','movement','baseline']")
p.write_text(s,encoding='utf-8')
b=json.loads((N/'actions.json').read_text(encoding='utf-8'))
(N/'current-status.json').write_text(json.dumps({'version':'V9','character':'neuvillette','stage':'basic-movement-batch1-candidate','actions':len(b),'mainDisplayStates':sum(len(g['frames']) for g in b.values()),'newBodySources':10,'newGroups':['jump','forwarddash'],'entry':'player.html','artAccepted':False,'runtimeIntegrated':False,'simulatorVerified':False,'deviceVerified':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('Neuvillette V9 preview updated with fixed idle, jump root and dash motion')
