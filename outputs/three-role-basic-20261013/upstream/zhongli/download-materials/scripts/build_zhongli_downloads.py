"""Package this round's evidence and original generated images for download."""
from pathlib import Path
import hashlib,json,shutil,zipfile,html,re,os
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
SCRATCH=ROOT.parent
OUT=ROOT/'outputs/zhongli-design-20261011'
SITE=Path('/workspace/sites/zhongli-action-review/dist')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def deduplicate_site_pngs(site):
    # Preserve every original filename in generated/. Only replace duplicate serving copies.
    canonical={sha(p):p.resolve() for p in (site/'generated').glob('*.png')}
    aliases={p.resolve():canonical[sha(p)] for p in site.rglob('*.png') if p.parent.name!='generated' and sha(p) in canonical}
    def remap(value,parent):
        if isinstance(value,dict):return {k:remap(v,parent) for k,v in value.items()}
        if isinstance(value,list):return [remap(v,parent) for v in value]
        if isinstance(value,str) and not value.startswith(('http:','https:','data:')):
            try:target=(parent/value).resolve()
            except (ValueError,OSError):return value
            if target in aliases:return os.path.relpath(aliases[target],parent)
        return value
    for p in site.rglob('*'):
        if p.suffix=='.json' and 'downloads' not in p.parts:
            try:data=json.loads(p.read_text())
            except (UnicodeDecodeError,json.JSONDecodeError):continue
            mapped=remap(data,p.parent)
            if mapped!=data:p.write_text(json.dumps(mapped,ensure_ascii=False,indent=2))
        elif p.suffix=='.html':
            source=p.read_text()
            def link(m):return m.group(1)+remap(m.group(2),p.parent)+m.group(3)
            source=re.sub(r'((?:src|href)=")([^"]+)(")',link,source)
            def embedded(m):
                try:data=json.loads(m.group(2))
                except json.JSONDecodeError:return m.group(0)
                return m.group(1)+json.dumps(remap(data,p.parent),ensure_ascii=False).replace('<','\\u003c')+m.group(3)
            source=re.sub(r'(<script[^>]*type="application/json"[^>]*>)(.*?)(</script>)',embedded,source,flags=re.S)
            p.write_text(source)
    saved=sum(p.stat().st_size for p in aliases)
    for p in aliases:p.unlink()
    print('Serving-copy bytes deduplicated:',saved)

def main():
    bundle=OUT/'download-materials';bundle.mkdir(exist_ok=True)
    originals=bundle/'generated-originals';originals.mkdir(exist_ok=True)
    for p in sorted((SCRATCH/'generated_images').glob('*.png')):shutil.copy2(p,originals/p.name)
    standards=bundle/'standards';standards.mkdir(exist_ok=True)
    paths=['AGENTS.md','AI_START.md','docs/双人下一版实施与动作交接.md','docs/current/双角色素材提交与修复交接_20261011.md','docs/current/工作流与工具.md','outputs/dual-character-reference-20261011/ART_STANDARD.md','outputs/dual-character-reference-20261011/CHARACTER_STANDARD.md','outputs/v4-one-character-20261010/ayaka-armed-v2/制作总结与完成标准.md','outputs/furina-design-20261010/角色尺度处理方案_20261011.md','outputs/v4-one-character-20261010/基线动作参数与逐角色接入.md','game/tools/artlib.py','assets/roster-v2/zhongli-frames.json','assets/roster-v2/zhongli-official-head.png']
    for rel in paths:
        p=ROOT/rel
        if not p.exists():raise FileNotFoundError(p)
        dest=standards/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    refs=bundle/'user-reference';refs.mkdir(exist_ok=True)
    for p in (SCRATCH/'upload').iterdir():
        if p.suffix.lower() in ['.png','.jpg','.jpeg']:shutil.copy2(p,refs/p.name)
        elif p.suffix=='.html':
            text=p.read_text();text=re.sub(r'<!--.*?-->','',text,flags=re.S)
            text=re.sub(r'[A-Za-z]:[\\/][^\s<>"\']+',r'%USERPROFILE%/reference',text)
            (refs/p.name).write_text(text)
    scripts=bundle/'scripts';scripts.mkdir(exist_ok=True)
    for p in (ROOT/'work').glob('build_zhongli*.py'):shutil.copy2(p,scripts/p.name)
    notes='''# 钟离本轮完整资料

入口：制作检查.html；最新动作页为batches/20261011-refinement/light1-action-review.html。最新局部返修与7姿轻攻独立候选已登记，25组动作未验收。
generated-originals 是本轮实际返回的全部生成PNG，包含失败稿、返修稿和未采用稿。sources、history、reuse、review 保留各阶段来源；生成图片不自动等于动作已采用。
standards 为本轮使用的最新仓库规范；旧资料只作为历史源图证据。scripts 中全量动作构建器尚未完成，现有 app.js / index.html 为工作材料，不能作为正式25组动作交付。
下载分包是独立ZIP，各包在同一目录解压。内容完全相同的文件只保存一次；解压后运行 restore-duplicates.py 或 restore-duplicates.ps1 即可按台账恢复所有原路径，不需要再次联网。manifest.json 登记每个文件大小与SHA256。
网页公开给当前站点原有访问对象；本资料不包含Git凭据、站点令牌或完整Git目录。
浏览器嵌入与设备效果未实测。访问遭Cloudflare IP拦截时，登录并不保证解除；用户已确认受拦IP为VPN出口。资料可通过全部ZIP离线恢复。
'''
    (bundle/'README.md').write_text(notes)
    allfiles=sorted(p for p in OUT.rglob('*') if p.is_file() and 'downloads' not in p.relative_to(OUT).parts and p.name not in ['manifest.json','下载站.html','下载交付记录.json','duplicate-paths.json','restore-duplicates.py','restore-duplicates.ps1'])
    manifest=[{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in allfiles]
    (bundle/'manifest.json').write_text(json.dumps({'sourceCommit':'1c21eb57ffb1b8d88b41cbb743c46a34864849df','state':'checkpoint; full action delivery unfinished','files':manifest},ensure_ascii=False,indent=2))
    allfiles.append(bundle/'manifest.json')
    seen={};unique=[];aliases=[]
    for p in allfiles:
        digest=sha(p)
        if digest in seen:aliases.append({'path':str(p.relative_to(OUT)),'source':str(seen[digest].relative_to(OUT)),'sha256':digest})
        else:seen[digest]=p;unique.append(p)
    (bundle/'duplicate-paths.json').write_text(json.dumps(aliases,ensure_ascii=False,indent=2))
    restore='''from pathlib import Path
import json,shutil,hashlib
root=Path(__file__).resolve().parent
for item in json.loads((root/'download-materials/duplicate-paths.json').read_text(encoding='utf-8')):
    src=root/item['source'];dst=root/item['path']
    assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256'],str(src)
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
print('All duplicate paths restored.')
'''
    (OUT/'restore-duplicates.py').write_text(restore)
    (OUT/'restore-duplicates.ps1').write_text('''$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$items = Get-Content -LiteralPath (Join-Path $root 'download-materials/duplicate-paths.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($item in $items) {
    $src = Join-Path $root $item.source
    $dst = Join-Path $root $item.path
    if ((Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLower() -ne $item.sha256) { throw "Hash mismatch: $src" }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
}
Write-Output 'All duplicate paths restored.'
''')
    # Include restoration metadata after deduplication, without stale prior-run copies.
    unique=[p for p in unique if p.name not in ['duplicate-paths.json','restore-duplicates.py','restore-duplicates.ps1']]
    unique += [bundle/'duplicate-paths.json',OUT/'restore-duplicates.py',OUT/'restore-duplicates.ps1']
    downloads=SITE/'downloads';downloads.mkdir(exist_ok=True)
    for p in downloads.glob('*'):p.unlink()
    # Each ZIP remains below 20MiB for static hosting, including ZIP headers.
    batches=[];batch=[];size=0
    for p in unique:
        if batch and size+p.stat().st_size>18*1024*1024:batches.append(batch);batch=[];size=0
        batch.append(p);size+=p.stat().st_size
    if batch:batches.append(batch)
    volumes=[]
    for i,batch in enumerate(batches,1):
        p=downloads/f'zhongli-materials-{i:02}.zip'
        with zipfile.ZipFile(p,'w',compression=zipfile.ZIP_DEFLATED) as z:
            for f in batch:z.write(f,str(f.relative_to(OUT)))
        assert p.stat().st_size<20*1024*1024
        with zipfile.ZipFile(p) as z:assert z.testzip() is None
        volumes.append({'file':p.name,'bytes':p.stat().st_size,'sha256':sha(p),'entries':len(batch)})
    with zipfile.ZipFile(downloads/'generated-image-index.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        z.write(bundle/'README.md','README.md');z.write(bundle/'manifest.json','manifest.json')
    shutil.copy2(bundle/'manifest.json',downloads/'manifest.json')
    (downloads/'volumes.json').write_text(json.dumps(volumes,indent=2))
    imgs=SITE/'generated';thumbs=SITE/'thumbnails';imgs.mkdir(exist_ok=True);thumbs.mkdir(exist_ok=True)
    for p in originals.glob('*.png'):shutil.copy2(p,imgs/p.name)
    reverse={}
    for row in manifest:
        if row['path'].startswith(('sources/','history/','batches/')):reverse.setdefault(row['sha256'],[]).append(row['path'])
    gallery=[]
    for p in sorted(originals.glob('*.png')):
        im=Image.open(p).convert('RGBA');im.thumbnail((560,400));im.save(thumbs/(p.stem+'.webp'))
        matches=reverse.get(sha(p),[])
        label=' / '.join(matches) if matches else '已返回的生成候选；未映射到当前源图'
        gallery.append(f'<article class="card"><a href="generated/{p.name}" target="_blank" rel="noopener"><img loading="lazy" src="thumbnails/{p.stem}.webp" alt="生成图片预览"></a><p>{html.escape(label)}</p><p class="filename">{p.name}</p><a class="button" href="generated/{p.name}" download="{p.name}">下载原始PNG</a></article>')
    vol=''.join(f'<li><a href="downloads/{p["file"]}" download>{p["file"]}</a> · {p["bytes"]/1024**2:.1f} MB · {p["entries"]}文件</li>' for p in volumes)
    page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>钟离 · 本轮资料下载</title><style>
body{font:16px/1.7 system-ui;margin:auto;padding:24px;max-width:1200px;background:#f4f6fa;color:#202a3e}h1{font-size:30px}a{color:#315da6}.button{display:inline-block;padding:9px 16px;background:#946824;color:white;border-radius:6px;text-decoration:none}nav{display:flex;flex-wrap:wrap;gap:12px}section{margin:26px 0;padding:20px;background:white;border:1px solid #ccd3df;border-radius:10px}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px}.card{padding:14px;border:1px solid #ccd3df;border-radius:8px;overflow:hidden}.card img{width:100%;height:280px;object-fit:contain;background:#e5e8ee}.card p{font-size:14px;overflow-wrap:anywhere}.filename{font-family:monospace;color:#637084}.notice{border-left:4px solid #b67b25;padding:12px 18px;background:#fff0d4}summary{cursor:pointer}iframe{display:none}</style></head><body>
<h1>钟离 · 本轮资料下载</h1><p class="notice">已恢复制作：去晕染母版、待机／行走和轻攻一动作候选。新生成图片含失败稿和未采用稿；25组动作尚未完成验收。</p><nav><a class="button" href="batches/20261011-refinement/light1-slow.gif">直接查看慢放GIF</a><a class="button" href="batches/20261011-refinement/comparison.png">前后对照图</a><a class="button" href="batches/20261011-refinement/light1-action-review.html">最新轻攻一动作检查</a><a class="button" href="batches/20261011-resume/review.html">9姿拟合对照</a><a class="button" href="review.html" target="_blank" rel="noopener">打开制作检查</a><a class="button" href="#generated">浏览／下载生成图片</a><a class="button" href="#packages">下载全部资料分包</a></nav>
<section><h2>访问与下载</h2><p>请在独立浏览器标签页打开本站，并使用站点所有者账户登录。若出现Cloudflare封禁页，可按既有支持建议切换可信网络；登录本身不保证解除IP拦截。本站保留原有访问权限。检查页使用直接链接，不通过内嵌框架打开。</p><p>点击“下载原始PNG”即可保存生成原图。每个ZIP可独立解压；把全部分包解压到同一目录，再运行 restore-duplicates.py 或 restore-duplicates.ps1，即可恢复完整原目录。同内容副本只存一份，不丢失原图，也无需再次联网。</p></section>
<section id="packages"><h2>本轮全部资料</h2><p>含生成原图、旧源图复用证据、返修历史、拟合结果、提示词、制作记录、规范、用户参考、代码与未完成工作材料。</p><ul>'''+vol+'''</ul><a href="downloads/manifest.json" download>下载全部文件哈希清单</a> · <a href="downloads/volumes.json" download>下载分包哈希清单</a></section>
<section id="generated"><h2>生成图片 · '''+str(len(gallery))+'''张原始PNG</h2><p>展示所有实际返回的生成图，不丢弃失败稿。路径对应提示当前源图或历史保存位置；“当前源图”仍不代表已经验收。</p><div class="gallery">'''+''.join(gallery)+'''</div></section></body></html>'''
    shutil.copy2(OUT/'制作检查.html',SITE/'review.html')
    shutil.copy2(OUT/'制作检查.html',SITE/'制作检查.html')
    shutil.copytree(OUT/'batches',SITE/'batches',dirs_exist_ok=True)
    for name in ['生产流程与交接.md','生产台账.json','制作记录.md','后续制作分析.md']:
        shutil.copy2(OUT/name,SITE/name)
    page=page.replace('<section id="packages">','<section><h2>生产流程与台账</h2><p><a href="生产流程与交接.md" download>下载流程与交接</a> · <a href="生产台账.json" download>下载25组生产台账</a> · <a href="制作记录.md" download>下载制作记录</a> · <a href="后续制作分析.md" download>下载后续制作分析</a></p><p>本站为本轮发布快照，可直接下载保存；以后生产批次需要同步更新。</p></section><section id="packages">')
    (SITE/'index.html').write_text(page)
    # Snapshot of the hosted hub; links target the deployed site's assets.
    (OUT/'下载站.html').write_text(page.replace('<head>','<head><base href="https://zhongli-v4-action-review.cwc56154781820.chatgpt.site/">'))
    report={'generatedImages':len(gallery),'materialFiles':len(allfiles),'uniquePackagedFiles':len(unique),'duplicatePaths':len(aliases),'totalBytes':sum(p.stat().st_size for p in allfiles),'volumes':volumes,'verification':'ZIP CRC checked; manifest SHA256 and links checked; browser unverified'}
    (OUT/'下载交付记录.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    deduplicate_site_pngs(SITE)
    print(json.dumps({k:v for k,v in report.items() if k!='volumes'},ensure_ascii=False))

if __name__=='__main__':main()
