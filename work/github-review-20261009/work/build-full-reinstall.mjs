import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import{decode,encode,msg,str,all,replace,number as N,bytes as B,message as M}from'./node-gia-wire.mjs';
import{exportGia,importGia,validateServerGiaCompatibility}from'file:///C:/Users/Cheng/Documents/deepseek-harness/default-workspace/miliastra-beyond-simulator/studio/gia/codec.js';
const out='outputs/full-reinstall';fs.mkdirSync(out,{recursive:true});
const stamp=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(new Date()).replace(/[-: ]/g,'').replace(/^(\d{8})(\d{6})$/,'$1_$2');
const previous=JSON.parse(fs.readFileSync('outputs/midphase-final/delivery.json')),aliases=JSON.parse(fs.readFileSync('work/network-signal-bindings.json'));
const bindings=Object.fromEntries(Object.keys(aliases).map(k=>[k,'GF10'+k.slice(7)])),oldToNew=Object.fromEntries(Object.keys(aliases).map(k=>[aliases[k],bindings[k]]));
let lua=fs.readFileSync('outputs/network-node-sample5/gpt_20261004_节点图5_席位可见诊断.lua','utf8');for(const[a,b]of Object.entries(oldToNew))lua=lua.replaceAll("'"+a+"'","'"+b+"'");lua=lua.replace('SEAT-PROBE-5','GF10-FULL').replace('TX=信号_16 / RX=信号_15','TX=GF10Hello / RX=GF10Seat');
const save=JSON.parse(fs.readFileSync('outputs/midphase-final/fighter.save.json'));save.assets.scripts[0].source=lua;
const luaName='gpt_'+stamp+'_完整游戏.lua',aName='gpt_'+stamp+'_A_完整游戏.gia',bName='gpt_'+stamp+'_B_通用图元模板.gia',nodeName='gpt_'+stamp+'_联机节点_含完整信号.gia';
save.assets.scripts[0].path='lua/'+luaName;save.assets.scripts[0].filename=luaName;save.assets.server.root.name=aName.slice(0,-4);save.assets.server.meta.name=aName.slice(0,-4);save.assets.server.meta.giaFileName=aName;
const a=exportGia(save.assets.server,{scripts:save.assets.scripts});assert(validateServerGiaCompatibility(a.buffer).valid);assert(importGia(a.buffer,aName).scripts.some(s=>s.source===lua));fs.writeFileSync(out+'/'+aName,a.buffer);fs.writeFileSync(out+'/'+luaName,lua);
const oldB=previous.files.find(f=>f.kind==='client');fs.copyFileSync('outputs/midphase-final/'+oldB.filename,out+'/'+bName);
const source=fs.readFileSync('C:/Users/Cheng/Desktop/联机节点图5.gia');let root=decode(source.subarray(20,20+source.readUInt32BE(16)));
// Replace exact signal-name strings, retaining native IDs, ports and metadata.
function rename(fields){return fields.map(f=>{if(f.w!==2)return f;const text=f.v.toString('utf8');if(oldToNew[text])return B(f.f,oldToNew[text]);try{const child=decode(f.v);if(encode(child).equals(f.v))return M(f.f,rename(child));}catch{}return f;});}
root=rename(root);let unit=msg(root,1),wrap=msg(unit,13),w1=msg(wrap,1),graph=msg(w1,1);const graphId=1073741950;
graph=replace(graph,1,[M(1,replace(msg(graph,1),5,[N(5,graphId)]))]);graph=replace(graph,2,[B(2,nodeName.slice(0,-4))]);w1=replace(w1,1,[M(1,graph)]);wrap=replace(wrap,1,[M(1,w1)]);unit=replace(unit,13,[M(13,wrap)]);unit=replace(unit,1,[M(1,replace(msg(unit,1),4,[N(4,graphId)]))]);unit=replace(unit,3,[B(3,nodeName.slice(0,-4))]);root=replace(root,1,[M(1,unit)]);root=replace(root,3,[B(3,nodeName)]);
assert.equal(all(root,2).length,40);const found=new Set();for(const x of all(root,2)){const sig=msg(msg(msg(msg(decode(x.v),14),1),1),107);for(const k of[101,102,108])if(str(msg(sig,k),1))found.add(str(msg(sig,k),1));}assert.deepEqual([...found].sort(),Object.values(bindings).sort());
const payload=encode(root),header=Buffer.from(source.subarray(0,20));header.writeUInt32BE(payload.length+20,0);header.writeUInt32BE(payload.length,16);fs.writeFileSync(out+'/'+nodeName,Buffer.concat([header,payload,source.subarray(-4)]));
const files=[aName,bName,nodeName,luaName].map(filename=>{const bytes=fs.readFileSync(out+'/'+filename);return{filename,bytes:bytes.length,sha256:crypto.createHash('sha256').update(bytes).digest('hex')}});
fs.writeFileSync(out+'/delivery.json',JSON.stringify({stamp,files,bindings,pixelTemplateIndex:1073742822,embeddedSignalDefinitions:40,officialImportVerified:false,requiresPostImportSignalNameCheck:true},null,2));fs.writeFileSync(out+'/fighter.save.json',JSON.stringify(save));
const sim=JSON.parse(fs.readFileSync('outputs/midphase-final/simulator.save.json'));sim.assets.scripts[0].source=lua;function update(v){if(!v||typeof v!=='object')return;for(const[k,x]of Object.entries(v)){if(k==='signalName'&&oldToNew[x])v[k]=oldToNew[x];else update(x)}}update(sim.serverLogic);fs.writeFileSync(out+'/simulator.save.json',JSON.stringify(sim));
const instructions=`# 原神格斗1.0整套重装

本套件带全部十个信号定义，不依赖旧信号_11～20。源文件和旧交付均保留。新版诊断标记GF10-FULL。官方导入和真机尚未验证。

1. 退出试玩。先备份旧A、B及节点；停止旧A显示、取消旧联机图挂载，再导入本目录三个GIA。不要同时运行新旧界面或节点。
2. **先导入联机节点**：${nodeName}。在服务器信号管理器核对新图引用的十个信号名称。若千星自动改成信号_编号，逐个改成下表名称，并应用修改。不要只看文件名判断信号已匹配。用“查看节点图引用”确认操作的是新图引用的信号。
3. 客户端控件模板导入${bName}。读取B最外层容器实际索引。
4. 服务器控件模板导入${aName}。A的FighterDemo脚本中PIXEL_TEMPLATE_INDEX默认1073742822；如果步骤3的新B索引不同，改为新B实际索引并保存。无需另挂一份Lua，A已内嵌完整脚本；单独Lua供检查和替换。
5. A界面显示给双方玩家。联机图挂在公共控制空实体1077936129；如果你删除并新建了空实体，使用新实体，并在它上面建变量。图通过获取自身实体读写，不需把旧GUID写进客户端Lua。
6. 创建下表17个图变量。保存，退出旧试玩后重新进入双人试玩。

|含义|必须匹配的信号名|参数顺序与类型|
|---|---|---|
|请求席位|GF10Hello|无|
|席位回包|GF10Seat|Slot整数|
|提交选人|GF10Team|Slot、Role1、Role2、Role3、Ready、Stage、Epoch、Revision、Round、Wins1、Wins2，全整数|
|选人回包|GF10TeamOut|同Team，11整数|
|请求开战|GF10Join|Epoch整数|
|开战回包|GF10Joined|Epoch整数|
|帧提交|GF10Frames|Slot整数、FirstFrame整数、AckFrame整数、Payload字符串、Epoch整数|
|帧转发|GF10FramesOut|同Frames|
|流程提交|GF10Flow|Slot、Action、Epoch、Revision，全整数|
|流程回包|GF10FlowOut|同Flow，4整数|

|变量|类型|初值|
|---|---|---|
|P1、P2|实体|无初始值|
|Stage、Round、Epoch|整数|1|
|P1Revision、P2Revision|整数|-1|
|Wins1、Wins2|整数|0|
|P1Role1、P1Role2、P1Role3、P2Role1、P2Role2、P2Role3|整数|0|
|P1Ready、P2Ready|整数|0|

等待席位时，头像下方应显示GF10-FULL、Hello调用数、SeatRx回调数和Slot。Hello增加只证明调用发送API，不证明服务器收到；SeatRx为0表示回调没到。未显示GF10-FULL时核查实际显示A及其脚本。截图实机结果决定下一步，不能把本地检查当成已排除运行时问题。
`;
fs.writeFileSync(out+'/安装说明.md',instructions);console.log(JSON.stringify({out,stamp,files:files.map(f=>f.filename)}));
