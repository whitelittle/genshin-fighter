# 战斗参考研究目录

2026-10-13。本目录用于只读研究，不是本项目的运行源码或发布包。

- `bvn-source/`：死火引擎公开文本子集，固定提交见`source-audit.json`。
- `sf3-archive/3s-decomp-main/`：街霸III主仓库归档；依赖子模块与原游戏运行数据未补齐。
- `yoruichi.swf / juggo.swf`：官方预编译角色样本，哈希与来源见`sample-audit.json`及角色研究文档。主要角色原始帧工程未公开，样本是编译资源。
- `*.abc.json / *.pcode.txt / *.inspection.json`：本地静态解析结果；没有执行SWF。摘要中的条件方法不能作为所有分支都必然执行的证据。
- `character-sample.json`：分组随机选择与角色编号映射；种子20261013。
- `source-audit.json / sample-audit.json`：文件哈希及脚本绑定校验。
- `sf3.zip`是完成且校验过的归档。`bvn.zip`、`ffdec.zip`是下载超时留下的不完整文件，不能安装、解压使用或当作完整源码。FFDec没有安装或运行；角色解析由本地只读解析器完成。
- `bvn-flash-tree.json`是首次递归读取超时留下的不完整JSON，不用于结论；后续读取的是`bvn-flash-root.json / bvn-xfl-root.json / bvn-xfl-fighters.json / bvn-fla-root.json`。

阅读入口：

- [系统研究](../../docs/current/死火与街霸战斗表现源码研究_20261013.md)
- [三角色抽样](../../docs/current/三角色战斗交互抽样研究_20261013.md)
- [角色时间轴和命中数据](../../docs/current/角色抽样时间轴与命中数据_20261013.md)

当前只有静态研究；没有两款游戏实际运行、素材播放、声音试听、模拟器或真机战斗验证，也没有改动稳定游戏。
