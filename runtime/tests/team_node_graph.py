"""Execute the exported semantic node edges and compare with the Lua server reference."""
import ast,json,re
from run import runtime,ROOT
graph=json.loads((ROOT.parent/'outputs/multi-role-selection-20261012/GF3_Server_Node_Graph.json').read_text(encoding='utf-8'))
nodes={n['id']:n for n in graph['nodes']};edges={}
for e in graph['edges']:
    assert e['fromNode'] in nodes and e['toNode'] in nodes
    edges.setdefault((e['fromNode'],e['fromPort']),[]).append(e['toNode'])
state={v['name']:v['initial'] for v in graph['variables']}
rt=runtime(ROOT);server=rt.eval("GF_REQUIRE('gf_team_server').new()")
def value(v,env):
    if not isinstance(v,str):return v
    if v in env:return env[v]
    s=v.replace(' AND ',' and ').replace(' OR ',' or ')
    s=re.sub(r'\((Role[123]) > 0 \? 1 : 0\)',r'(1 if \1 > 0 else 0)',s)
    tree=ast.parse(s,mode='eval')
    for node in ast.walk(tree):
        assert isinstance(node,(ast.Expression,ast.BoolOp,ast.And,ast.Or,ast.Compare,ast.Eq,ast.NotEq,ast.Gt,ast.GtE,ast.Lt,ast.LtE,ast.Name,ast.Load,ast.Constant,ast.BinOp,ast.Add,ast.Subscript,ast.IfExp)),type(node)
    return eval(compile(tree,'graph','eval'),{'__builtins__':{}},env)
def execute(signal,params):
    decl=graph['signals'].get(signal)
    if decl is None or len(params)!=len(decl) or any(type(v)!=int for v in params):return []
    env={**state,'length':2,'players':[1,2],**{p['name']:v for p,v in zip(decl,params)}}
    out=[];steps=0
    def run(id):
        nonlocal steps
        steps+=1;assert steps<1000
        n=nodes[id];op=n['operation'];port='next'
        if op=='branch':port='true' if value(n['condition'],env) else 'false'
        elif op=='setCustomVariable':state[n['variable']]=env[n['variable']]=value(n['value'],env)
        elif op=='sendClientScriptSignal':
            target=env[n['target']]
            if target:out.append((target,n['signal'],[value(v,env) for v in n['params']]))
        elif op!='listen':raise AssertionError(op)
        for to in edges.get((id,port),[]):run(to)
    start=next(n['id'] for n in nodes.values() if n['operation']=='listen' and n['signal']==signal)
    run(start);return out
def compare(name,p):
    actual=execute(name,p)
    result=server.handle(server,name,rt.table_from(p),2)
    expected=[(o['slot'],o['signal'],list(o['params'].values())) for o in result.values()]
    assert actual==expected,(name,p,actual,expected)
compare('GF3Hello',[])
for p in ([1,1,0,1,0,0,0],[2,1,0,2,4,1,0],[1,1,1,1,3,4,1],[1,1,1,1,3,4,1],
          [1,1,1,4,3,1,1],[1,1,0,1,0,0,0],[2,1,1,2,4,1,1],[1,1,99,1,1,4,1],
          [1,1,99,1,0,4,0],[2,1,1,2,4,1,1]):compare('GF3Team',p)
compare('GF3Hello',[]);compare('GF3Reset',[1,1]);compare('GF3Reset',[2,1]);compare('GF3Team',[1,1,9,1,3,4,1])
compare('GF3Team',[1,2,0,5,6,1,1]);compare('GF3Team',[2,2,0,6,4,2,1])
print('Exported GF3 node graph edges vs Lua reference PASS')
