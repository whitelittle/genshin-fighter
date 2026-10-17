"""Export the independent GF3 preparation Lua and explicit node wiring specification."""
from pathlib import Path
import json,hashlib,shutil
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent/'outputs/multi-role-selection-20261012'
OUT.mkdir(exist_ok=True)
signals={
 'GF3Hello':[], 'GF3Seat':['Slot','Epoch'],
 'GF3Team':['Slot','Epoch','Revision','Role1','Role2','Role3','Ready'],
 'GF3Progress':['Epoch','Slot','Count','Ready','Revision'],
 'GF3Reveal':['Epoch','Revision1','Revision2','P1Role1','P1Role2','P1Role3','P2Role1','P2Role2','P2Role3'],
 'GF3Reset':['Slot','Epoch'],
}
variables=[{'name':'GF3_Epoch','type':'int','initial':1},{'name':'GF3_Locked','type':'bool','initial':False}]
for p in (1,2):
 variables.append({'name':f'GF3_P{p}','type':'entity','initial':None})
 for key,initial in [('Role1',0),('Role2',0),('Role3',0),('Count',0),('Ready',0),('Revision',-1)]:
  variables.append({'name':f'GF3_P{p}{key}','type':'int','initial':initial})
nodes=[];edges=[]
def node(id,operation,**kw):nodes.append({'id':id,'operation':operation,**kw});return id
def wire(a,b,port='next'):edges.append({'fromNode':a,'fromPort':port,'toNode':b,'toPort':'exec'})
def chain(prefix,start,actions):
 for i,action in enumerate(actions):
  id=node(f'{prefix}-{i}',**action);wire(start,id);start=id
 return start
def setv(name,value):return {'operation':'setCustomVariable','entity':'self','variable':name,'value':value}
def send(p,name,values):return {'operation':'sendClientScriptSignal','target':f'GF3_P{p}','signal':name,'params':values,'skipIfTargetEmpty':True}
def progress():
 return [send(p,'GF3Progress',['GF3_Epoch',q,f'GF3_P{q}Count',f'GF3_P{q}Ready',f'GF3_P{q}Revision']) for q in (1,2) for p in (1,2)]
def reveal():
 return [send(p,'GF3Reveal',['GF3_Epoch','GF3_P1Revision','GF3_P2Revision']+[f'GF3_P{q}Role{n}' for q in (1,2) for n in (1,2,3)]) for p in (1,2)]
node('self','getSelfEntity');node('players','getPlayersOnField');node('length','listLength',list='players')
hello=node('hello','listen',signal='GF3Hello')
one=node('has-one','branch',condition='length >= 1');wire(hello,one)
tail=chain('seat1',one,[setv('GF3_P1','players[0]'),send(1,'GF3Seat',[1,'GF3_Epoch'])]);edges[-2]['fromPort']='true'
two=node('has-two','branch',condition='length >= 2');wire(tail,two)
tail=chain('seat2',two,[setv('GF3_P2','players[1]'),send(2,'GF3Seat',[2,'GF3_Epoch'])]);edges[-2]['fromPort']='true'
tail=chain('hello-status',tail,progress());locked=node('hello-locked','branch',condition='GF3_Locked');wire(tail,locked)
chain('hello-reveal',locked,reveal());edges[-2]['fromPort']='true'
team=node('team','listen',signal='GF3Team')
route=node('team-slot','branch',condition='Slot == 1');wire(team,route)
for q in (1,2):
 conditions=[f'Slot == {q}','Epoch == GF3_Epoch','Revision >= 0',f'Revision >= GF3_P{q}Revision','Ready == 0 OR Ready == 1']
 conditions += [f'0 <= Role{n} <= 6' for n in (1,2,3)]
 conditions += ['Role1 != 0 OR (Role2 == 0 AND Role3 == 0)','Role2 != 0 OR Role3 == 0']
 conditions += [f'Role{a} == 0 OR Role{b} == 0 OR Role{a} != Role{b}' for a,b in [(1,2),(1,3),(2,3)]]
 conditions += ['Ready == 0 OR (Role1 > 0 AND Role2 > 0 AND Role3 > 0)']
 start=route
 for n,condition in enumerate(conditions):
  id=node(f'valid-{q}-{n}','branch',condition=condition);wire(start,id,('true' if q==1 else 'false') if start==route else 'true');start=id
 duplicate=node(f'duplicate-{q}','branch',condition=f'GF3_Locked OR Revision == GF3_P{q}Revision');wire(start,duplicate,'true')
 same=node(f'same-{q}','branch',condition=' AND '.join([f'{k} == GF3_P{q}{k}' for k in ['Revision','Role1','Role2','Role3','Ready']]))
 wire(duplicate,same,'true')
 retry=chain(f'retry-{q}',same,progress());edges[-len(progress())]['fromPort']='true'
 again=node(f'retry-locked-{q}','branch',condition='GF3_Locked');wire(retry,again)
 chain(f'retry-reveal-{q}',again,reveal());edges[-2]['fromPort']='true'
 actions=[setv(f'GF3_P{q}{k}',k) for k in ['Revision','Role1','Role2','Role3','Ready']]
 actions += [setv(f'GF3_P{q}Count','(Role1 > 0 ? 1 : 0) + (Role2 > 0 ? 1 : 0) + (Role3 > 0 ? 1 : 0)')]+progress()
 saved=chain(f'save-{q}',duplicate,actions);edges[-len(actions)]['fromPort']='false'
 both=node(f'both-ready-{q}','branch',condition='length >= 2 AND GF3_P1Ready == 1 AND GF3_P2Ready == 1');wire(saved,both)
 chain(f'commit-{q}',both,[setv('GF3_Locked',True)]+reveal());edges[-3]['fromPort']='true'
reset=node('reset','listen',signal='GF3Reset')
gate=node('valid-reset','branch',condition='(Slot == 1 OR Slot == 2) AND Epoch == GF3_Epoch');wire(reset,gate)
actions=[setv('GF3_Epoch','GF3_Epoch + 1'),setv('GF3_Locked',False)]
for q in (1,2):
 for key in ['Role1','Role2','Role3','Count','Ready','Revision']:actions.append(setv(f'GF3_P{q}{key}',-1 if key=='Revision' else 0))
 actions.append(send(q,'GF3Seat',[q,'GF3_Epoch']))
actions+=progress();chain('reset-state',gate,actions);edges[-len(actions)]['fromPort']='true'
graph={'format':'explicit node wiring specification; not native GIA','title':'GF3 多角色隐藏选人与准备','version':1,
 'signals':{k:[{'name':p,'type':'int'} for p in v] for k,v in signals.items()},'variables':variables,'nodes':nodes,'edges':edges,
 'expressionLowering':'AND/OR/!=/?: conditions expand to comparisons, logical operators and branches; see wiring guide',
 'identityValidation':False,'officialImportVerified':False,'battleFramesIncluded':False}
(OUT/'GF3_Server_Node_Graph.json').write_text(json.dumps(graph,ensure_ascii=False,indent=2),encoding='utf-8')
for src,name in [('dist/genshin_fighter.lua','多角色选择_客户端.lua'),('source/network/gf_team_selection.lua','GF3_客户端协议.lua'),('source/network/gf_team_server.lua','GF3_服务端逻辑参考.lua')]:shutil.copyfile(ROOT/src,OUT/name)
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.iterdir() if p.is_file() and p.name!='manifest.json'}
(OUT/'manifest.json').write_text(json.dumps({'files':files,'nativeGIA':False,'nativeVerified':False},ensure_ascii=False,indent=2),encoding='utf-8')
print('GF3 node specification, Lua and hashes exported')
