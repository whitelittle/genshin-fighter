"""Move disposable packaging/dependencies to a local take-away archive, preserving hashes."""
from pathlib import Path
import hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'_takeaway_20261018'
REPORT=ROOT/'docs/maintenance'

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):h.update(block)
    return h.hexdigest()

def main():
    ARCHIVE.mkdir(exist_ok=True)
    plan=[]
    for rel in ['work/V4_HANDOFF_PARTIAL_20261009.zip','work/video-deps',
                'work/vector-research-deps','work/github-review-20261009/.git',
                'work/smooth-baseline-20261013/repository/.git',
                'outputs/prefix-rename-backup','outputs/visual-cache','outputs/video-check']:
        plan.append((ROOT/rel,'重复恢复包装、第三方依赖、仓库元数据或历史备份/缓存；非当前制作输入'))
    for p in (ROOT/'outputs').glob('*.zip'):
        plan.append((p,'旧分发压缩包；对应展开资料或冻结历史另存，非当前交付入口'))
    for p in (ROOT/'work/three-role-upstream-20261013').rglob('*'):
        if p.is_file() and (p.suffix=='.zip' or '.partial-' in p.name):
            plan.append((p,'制作方下载分卷或下载残片；有效展开素材保留 outputs/three-role-basic-20261013/upstream'))
    for p in (ROOT/'outputs').glob('tutorial-*/verification'):
        if p.parent.name!='tutorial-wind-fx-v27-20261017':
            plan.append((p,'旧候选验证记录，不改变其模拟器结论；当前 v27 证据仍在原路径'))
    for p in (ROOT/'outputs').rglob('*.save.json'):
        if 'archive' in p.parts or p.parent.name.startswith('release-'):continue
        plan.append((p,'旧模拟器运行存档/重新导入缓存；保留游戏源码、GIA 和生成资料'))
    for p in (ROOT/'assets').rglob('*'):
        if p.is_file() and p.suffix.lower() in ['.mp4','.mov']:
            plan.append((p,'研究参考视频；已取出的参考帧与来源记录保留 Git，不是游戏运行素材'))
    for base in [ROOT/'outputs',ROOT/'work/v4-handoff-20261009-partial/V4']:
        for p in base.rglob('*.png'):
            if 'archive' not in p.parts and 'rejected' in p.name.lower():
                plan.append((p,'明确标记退回的原画/检查图；修订状态与提示词保留，当前不使用'))
    entries=[]
    old=REPORT/'archive-manifest.json'
    if old.exists():entries=json.loads(old.read_text(encoding='utf8'))['files']
    known={row['archive'] for row in entries}
    for p in ARCHIVE.rglob('*'):
        if not p.is_file() or p.parent==ARCHIVE:continue
        rel=p.relative_to(ROOT).as_posix()
        if rel not in known:
            original=p.relative_to(ARCHIVE).as_posix()
            assert not (ROOT/original).exists(),original
            entries.append({'original':original,'archive':rel,'bytes':p.stat().st_size,
                'sha256':sha(p),'reason':'归档任务中断后的内容校验恢复；重复包装或历史记录'})
    for src,reason in plan:
        if not src.exists():continue
        src=src.resolve();dest=(ARCHIVE/src.relative_to(ROOT)).resolve()
        assert src.is_relative_to(ROOT) and not src.is_relative_to(ARCHIVE)
        assert dest.is_relative_to(ARCHIVE) and not dest.exists(),dest
        files=sorted(p for p in src.rglob('*') if p.is_file()) if src.is_dir() else [src]
        rows=[{'original':p.relative_to(ROOT).as_posix(),'archive':(ARCHIVE/p.relative_to(ROOT)).relative_to(ROOT).as_posix(),
               'bytes':p.stat().st_size,'sha256':sha(p),'reason':reason} for p in files]
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(src),str(dest))
        # Validate every moved file. Never remove an original without preserving identical contents.
        for row in rows:
            p=ROOT/row['archive'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256']
        entries.extend(rows)
        print(src.relative_to(ROOT).as_posix(),len(rows),sum(x['bytes']for x in rows),flush=True)
    old.write_text(json.dumps({'date':'2026-10-18','files':entries},ensure_ascii=False,indent=2),encoding='utf8')
    (ARCHIVE/'README.md').write_text('''# 待取走资料\n\n2026-10-18。原目录结构保存，无需解包。分类为重复分发/恢复包、第三方安装依赖、嵌套 Git 元数据、历史备份/缓存和旧候选验证；不表示全部是错误素材。\n\n全部移出文件的原路径、字节数、SHA256 与原因见本目录 archive-manifest.json。需要历史证据时按原相对路径恢复。当前有效源图、提示词、编排、拟合、制作工具、冻结基线、教学源码链及 v27 验证保留在工程并提交 Git。\n\n此目录不提交 Git；移动完成已逐文件核对内容一致。拿走前请保留自己的副本，项目未自动删除它。\n''',encoding='utf8')
    shutil.copy2(old,ARCHIVE/'archive-manifest.json')
    print(json.dumps({'files':len(entries),'bytes':sum(x['bytes']for x in entries)}))

if __name__=='__main__':main()
