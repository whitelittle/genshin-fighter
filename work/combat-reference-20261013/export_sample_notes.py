import pathlib,json,re,hashlib

root=pathlib.Path(__file__).resolve().parent
out=root.parents[1]/'docs/current'
sample=json.loads((root/'character-sample.json').read_text(encoding='utf-8'))
sample['sf3']={'player_number':18,'name':'Twelve（十二）','action_source':'plpat19.c',
               'mapping_evidence':'Ck_Pass.c Passive_AS_tbl[18] = VS_NO12_AS; PLPAT.c plxx_extra_attack_table[18] = pl19_extra_attack'}
(root/'character-sample.json').write_text(json.dumps(sample,ensure_ascii=False,indent=2),encoding='utf-8')
assets=json.loads((root/'bvn-assets-tree.json').read_text(encoding='utf-8'))
blobs={x['path']:x for x in assets['tree'] if x['type']=='blob'}
lines=['# 角色抽样时间轴与命中数据','', '2026-10-13。这是静态资源解析和符号定位附录，不是实际运行记录。主结论见[三角色战斗交互抽样研究](三角色战斗交互抽样研究_20261013.md)。', '',
       '死火资源绝对帧使用1起算。事件表中的相对帧按“绝对帧−所在标签首帧”计算，仅用于定位，不能直接视为招式总时长；跳转、循环、暂停和子动画会改变执行顺序。命中参数是资源原始值，不是最终伤害。', '']
audit=[]
for key,name in [('yoruichi','夜一'),('juggo','重吾')]:
    data=json.loads((root/f'{key}.inspection.json').read_text(encoding='utf-8'))
    raw=(root/f'{key}.swf').read_bytes();entry=blobs[f'assets/assets/fighter/{key}.swf']
    sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert sha==entry['sha']
    main=max(data['sprites'],key=lambda s:len(s['labels']));ck=main['class'].split('.')[-1]
    lines += [f'## {name}', '', f"资源Git blob：`{sha}`；SHA256：`{data['swf_sha256']}`；资源动画帧率：{data['framerate']:g}；主时间轴类：`{main['class']}`。", '',
              '源文件：['+key+'.swf](https://github.com/5DPLAY-Game-Studio/BleachVsNaruto_TagAssets/blob/29dcdc2d2aa290eee2d12feb70bbc00bec0af84f/shared/assets/assets/fighter/'+key+'.swf)。', '',
              f'解析字节码及时间轴：[`{key}.inspection.json`](../../work/combat-reference-20261013/{key}.inspection.json)；[原始指令定位](../../work/combat-reference-20261013/{key}.pcode.txt)。', '',
              '### 命中定义','', '| ID | 原始参数 |','|---|---|']
    setup=next(m for m in data['method_summaries'] if m['name']=='main_mc::frame2')
    for c in setup['calls']:
        if c['call'].endswith('defineAction'):
            lines.append('| `'+c['args'][0]+'` | `'+json.dumps(c['args'][1],ensure_ascii=False,separators=(',',':'))+'` |')
    lines += ['','### 角色初始化','']
    for s in setup['assignments']:lines.append('- `'+s['target']+' = '+json.dumps(s['value'],ensure_ascii=False)+'`')
    lines += ['','### 主时间轴事件','', '| 标签 | 首帧 | 事件定位 |','|---|---|---|']
    methods=[]
    for m in data['method_summaries']:
        match=re.search('frame([0-9]+)$',m['name'])
        if match and ck in m['name']:methods.append((int(match[1]),m))
    for idx,label in enumerate(main['labels']):
        start=label['frame'];end=main['labels'][idx+1]['frame'] if idx+1<len(main['labels']) else main['frames']+1
        ev=[]
        for frame,m in methods:
            if not start<=frame<end:continue
            calls=[c['call'].split('.')[-1]+'('+','.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in c['args'])+')' for c in m['calls']]
            assignments=[s['target']+'='+json.dumps(s['value'],ensure_ascii=False) for s in m['assignments']]
            if calls or assignments:ev.append(f"绝对{frame}/相对{frame-start}: "+'；'.join(calls+assignments)+('【含分支，须读原始指令】' if m['branches'] else ''))
        lines.append('| '+label['label']+f' | {start} | '+'<br>'.join(ev).replace('|','&#124;')+' |')
    lines += ['','### 攻击标记出现区间','', '这是显示列表中命名攻击标记的出现帧；是否真正命中还取决于空间交集、命中定义、目标状态和重复受击限制。纯检查框不一定有伤害。', '', '| 标记 | 连续出现区间（绝对帧） |','|---|---|']
    spans={}
    for snap in main['markers']:
        for o in snap['objects']:
            if 'atm' in o['name']:spans.setdefault(o['name'],set()).add(snap['frame'])
    for marker,frames in sorted(spans.items()):
        runs=[]
        for frame in sorted(frames):
            if runs and frame==runs[-1][1]+1:runs[-1][1]=frame
            else:runs.append([frame,frame])
        lines.append('| `'+marker+'` | '+', '.join(str(a) if a==b else f'{a}–{b}' for a,b in runs)+' |')
    lines.append('')
    bindings=[]
    for m in data['method_summaries']:
        for c in m['calls']:
            if c['call'].endswith('addFrameScript'):
                args=c['args'];assert len(args)%2==0
                for frame,fn in zip(args[::2],args[1::2]):
                    match=re.fullmatch(r'this.frame(\d+)',fn.get('expr','') if isinstance(fn,dict) else '')
                    if match:assert frame+1==int(match[1]);bindings.append([frame+1,fn['expr']])
    unsupported=[m['name'] for m in data['method_summaries'] if '::frame' in m['name'] and m['unsupported']]
    assert not unsupported
    audit.append({'id':key,'git_blob_matches':True,'sha256':data['swf_sha256'],'verified_frame_bindings':len(bindings),'unsupported_frame_ops':len(unsupported),'frame_methods':sum('::frame' in m['name'] for m in data['method_summaries']),'main_labels':len(main['labels'])})
(out/'角色抽样时间轴与命中数据_20261013.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(root/'sample-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
