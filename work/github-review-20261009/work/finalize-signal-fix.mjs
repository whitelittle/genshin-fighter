import fs from 'node:fs';
const out='outputs/midphase-final', nodeDir='outputs/network-import-fix';
const d=JSON.parse(fs.readFileSync(out+'/delivery.json')),n=JSON.parse(fs.readFileSync(nodeDir+'/delivery.json'));
d.requiredNodeGraph=n.filename;d.onlyUpdateA=false;d.updateFiles=[d.files.find(f=>f.kind==='server').filename,n.filename];d.nodeGraph={path:nodeDir+'/'+n.filename,sha256:n.sha256,sameProjectOnly:true,officialImportVerified:false};
fs.writeFileSync(out+'/delivery.json',JSON.stringify(d,null,2));
fs.copyFileSync('outputs/network-node-sample4/verification.json',nodeDir+'/verification.json');
const text=`# 等待席位修订安装说明

更新：2026-10-04。当前需要更新以下两个文件，不使用旧压缩包。

1. 服务器控件模板导入 **${d.updateFiles[0]}**，双方显示新版A，停用旧A界面。
2. 在当前同一个关卡导入 **${n.filename}**。新节点引用现有信号，不删除或重新创建信号_11～信号_20。
3. 将新图挂到控制空实体 **1077936129**，取消旧联机图的挂载。保留旧图文件。B不用重导，模板索引保持 **1073742822**。
4. 保留原17个被图引用的变量。P1/P2是实体；Stage、Round、Epoch整数初值1；P1Revision、P2Revision初值-1；Wins和角色、Ready初值0。不要同时运行两张联机图。
5. 退出旧试玩后重新启动双人试玩。应先显示玩家1/2席位，再各选三人并准备。

## 本次定位

实机导出的联机节点图4显示：信号名称已变成信号_11～信号_20，而旧Lua仍使用Fighter名称；部分整数常量导入后变成0，影响第二玩家索引、Slot、范围比较和Revision重置。已修正生成器的整数编码，并让A使用实际信号名称。这属于生成与导入适配问题。

|协议含义|当前关卡信号|
|---|---|
${Object.entries(n.signalBindings).map(([k,v])=>'|'+k+'|'+v+'|').join('\n')}

## 验证边界与异常处理

本地：新版A通过双方真实指针选角、准备、开战三项检查；新节点二进制解释检查16项通过，包含整数格式和端口引用检查。

官方导入和真机：尚未验证。新节点仅适用于提供节点图4的当前关卡，因为引用的是该关卡已有信号资源。如果导入报缺失信号，或出现红色信号端口，先不要重建或重命名信号；保留旧图，导出刚导入的新图和错误提示再核查。不能把本地通过视为真机已修复。

若能正常导入但仍等待席位，核对控制实体只挂新图、两端都显示新版A，再导出实际挂载的新图；B索引不会解决服务器席位回包问题。
`;
fs.writeFileSync(out+'/选人修订安装说明.md',text);fs.writeFileSync(nodeDir+'/安装说明.md',text);
for(const name of ['GIA安装说明.md','节点安装说明.md']){const p=out+'/'+name,old=fs.readFileSync(p,'utf8');const marker='<!-- CURRENT_SIGNAL_FIX -->';const body=old.includes(marker)?old.slice(old.indexOf('<!-- HISTORICAL_INSTALL -->')+'<!-- HISTORICAL_INSTALL -->'.length):old;fs.writeFileSync(p,marker+'\n当前20261004_191454界面与191546节点的更新步骤，以[选人修订安装说明](选人修订安装说明.md)为准。当前B已安装，不重导。下方保留通用安装历史参考，旧文件名不作为本次更新依据。\n\n<!-- HISTORICAL_INSTALL -->\n'+body);}
let start=fs.readFileSync('AI_START.md','utf8').replace('时间戳 20261004_165353','界面时间戳 20261004_191454，节点时间戳 20261004_191546');start+='\n最新席位修订：实机节点图4确认信号被改名及整数常量清零。当前A与 outputs/network-import-fix 新节点一起更新，B保持1073742822。新节点引用同关卡现有信号；本地16项检查通过，官方导入及真机待验。旧165104/165353修订是历史版本，不作为当前安装依据。用户要求直接导出GIA，不打压缩包。\n';fs.writeFileSync('AI_START.md',start);
fs.appendFileSync('docs/current/问题台账.md','\n2026-10-04实机节点图4核验：确认信号自动改为信号_11～20，以及部分整数常量清零。修订A191454与引用已有信号的节点191546，本地点击流程3项、节点解释16项通过。官方引用导入支持和真机席位回包仍是P0待验；旧修订不视为已解决。\n');
fs.writeFileSync('docs/share/GIA信号与整数常量导入注意事项.md',`# GIA信号与整数常量导入注意事项

依据：本项目官方导出样例及导入后的节点图对照；不作为平台完整格式规范。

- 信号导入可能复制定义并改名。客户端字符串必须匹配当前关卡实际信号名称；节点显示名不能证明客户端仍绑定原名称。
- 整数直接型使用literal.102；泛型使用literal.110.2.102。不要同时填写两条整数路径。
- 已填写的泛型整数需要正确的字面量状态field2=1；忽略状态可能导致导入清零。负数按有符号32位处理，避免Number精度损失。
- 本地解释器必须读取实际交付二进制，并检查oneof、字面量状态、端口及引用。只读编译器中间逻辑不能发现序列化错误。
- 引用已有信号资源的GIA只能用于同关卡，官方导入是否支持仍需验证；不能把省略信号定义视作已验证的跨关卡方案。
- 验收分开记录：设计意图、二进制本地检查、模拟器流程、官方导入、双端真机。保留导入前后文件用于对照。
`);
console.log(JSON.stringify({updateFiles:d.updateFiles,officialImportVerified:false}));
