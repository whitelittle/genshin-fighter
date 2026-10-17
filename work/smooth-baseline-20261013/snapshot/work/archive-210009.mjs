import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
const src='outputs/full-reinstall',out='outputs/archive/20261004_210009';fs.mkdirSync(out+'/交付',{recursive:true});fs.mkdirSync(out+'/归档前文档',{recursive:true});
const d=JSON.parse(fs.readFileSync(src+'/delivery.json'));
for(const f of d.files){const b=fs.readFileSync(src+'/'+f.filename);assert.equal(crypto.createHash('sha256').update(b).digest('hex'),f.sha256);fs.copyFileSync(src+'/'+f.filename,out+'/交付/'+f.filename);}
for(const f of ['delivery.json','安装说明.md','node-verification.json','selection-input-verification.json'])fs.copyFileSync(src+'/'+f,out+'/交付/'+f);
for(const f of ['AI_START.md','docs/current/README.md','docs/current/交接与中期计划.md','docs/current/技术实现与验证.md','docs/current/问题台账.md','docs/current/工作流与工具.md'])fs.copyFileSync(f,out+'/归档前文档/'+f.replaceAll('/','_'));
const record={version:'20261004_210009',date:'2026-10-04',status:'archived_baseline',userConfirmed:{interactionWorks:true,bothPlayersPreparingCharacters:true},notConfirmed:['资源加载完成与真机开战','完整三场及结算返回','手机与PC加载性能改善'],knownBlockingIssue:'PC和手机资源加载慢',verification:{nodeLogicChecks:16,simulatorPointerFlowChecks:3,officialImportAndInteraction:'用户确认本版交互无问题，双方进入准备角色；未另取得本版重导出文件'},files:d.files,sourceDirectory:src,deletedFiles:[],externalDelivery:'三个GIA、Lua及安装说明已复制千星目录；本次归档不再次安装或修改外部应用'};
fs.writeFileSync(out+'/归档记录.json',JSON.stringify(record,null,2));
fs.writeFileSync(src+'/验收状态.json',JSON.stringify(record,null,2));
const readme=`# 原神格斗1.0归档基线：210009

日期：2026-10-04。此目录冻结当前交付文件和归档时证据；后续版本另建输出目录，不覆盖这里。

用户已确认本版本交互正常，双方都进入准备角色。当前性能仍有明显问题，PC和手机加载慢；尚未确认本版本加载结束后的真机开战、完整三场及结算流程。归档表示冻结版本，不表示所有问题完成。

- [交付及安装](交付/安装说明.md)：完整A、B、Lua和含信号节点。
- [版本与哈希](交付/delivery.json)、[归档记录](归档记录.json)。
- 当前知识入口：项目docs/current/README.md；节点专题：docs/current/节点图知识与排错.md；下一阶段：docs/current/交接与中期计划.md。
- 原始美术、构建输入、样例、工具和旧文件保留在原目录；本次没有删除文件。归档前文档只用于追溯，不覆盖新验收结论。
`;
fs.writeFileSync(out+'/README.md',readme);
console.log(JSON.stringify({archive:out,filesVerified:d.files.length,status:record.userConfirmed,deleted:0}));
