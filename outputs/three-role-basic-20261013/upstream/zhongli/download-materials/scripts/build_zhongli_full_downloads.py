"""Persist all round materials once, with small client ZIP exports and SHA manifest."""
from pathlib import Path
import json,hashlib,shutil,html,zipfile,re,os
from PIL import Image
from build_zhongli_downloads import deduplicate_site_pngs
ROOT=Path(__file__).resolve().parents[1];O=ROOT/'outputs/zhongli-design-20261011';F=O/'full-actions';S=Path('/workspace/sites/zhongli-action-review/dist');D=O/'downloads'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2))
def main():
 # Explicit preservation of every returned PNG, including failed spacing variants.
 originals=O/'download-materials/generated-originals'
 for p in (ROOT.parent/'generated_images').glob('*.png'):shutil.copy2(p,originals/p.name);shutil.copy2(p,S/'generated'/p.name)
 scripts=O/'download-materials/scripts'
 for pattern in ('*zhongli*.py','*zhongli*.cjs'):
  for p in (ROOT/'work').glob(pattern):shutil.copy2(p,scripts/p.name)
 shutil.copy2(ROOT/'game/tools/artlib.py',scripts/'artlib.py')
 (O/'download-materials/README.md').write_text((F/'README.md').read_text())
 for name in ['生产台账.json','生产流程与交接.md','制作记录.md','后续制作分析.md','checkpoint.json']:shutil.copy2(O/name,S/name)
 shutil.copytree(F,S/'full-actions',dirs_exist_ok=True);deduplicate_site_pngs(S)
 # Static hosting would exceed its archive limit if every PNG also appeared in a hosted ZIP.
 # Keep one durable copy. Browser ZIP exports fetch only a bounded volume's actual files.
 for p in (S/'downloads').glob('*.zip'):p.unlink()
 assets=S/'material-assets';assets.mkdir(exist_ok=True)
 canonical={sha(p):p for p in S.rglob('*') if p.is_file() and 'downloads' not in p.relative_to(S).parts and p.suffix!='.html'}
 files=sorted(p for p in O.rglob('*') if p.is_file() and not any(x in p.relative_to(O).parts for x in ['downloads','__pycache__']) and p.name not in ['manifest.json','duplicate-paths.json','下载站.html','下载交付记录.json'])
 unique=[];alias=[];seen={};manifest=[]
 for p in files:
  rel=str(p.relative_to(O));digest=sha(p);manifest.append({'path':rel,'bytes':p.stat().st_size,'sha256':digest})
  if digest in seen:alias.append({'path':rel,'source':seen[digest],'sha256':digest});continue
  seen[digest]=rel;target=canonical.get(digest)
  if target is None:target=assets/(digest+p.suffix);shutil.copy2(p,target);canonical[digest]=target
  unique.append({'path':rel,'url':str(target.relative_to(S)),'bytes':p.stat().st_size,'sha256':digest})
 write(O/'download-materials/duplicate-paths.json',alias);write(O/'download-materials/manifest.json',{'state':'25组全动作素材候选及完整历史资料','files':manifest})
 for p,rel in [(O/'download-materials/duplicate-paths.json','download-materials/duplicate-paths.json'),(O/'download-materials/manifest.json','download-materials/manifest.json')]:
  target=assets/(sha(p)+'.json');shutil.copy2(p,target);unique.append({'path':rel,'url':str(target.relative_to(S)),'bytes':p.stat().st_size,'sha256':sha(p)})
 batches=[];batch=[];size=0
 for r in unique:
  if batch and size+r['bytes']>18*1024**2:batches.append(batch);batch=[];size=0
  batch.append(r);size+=r['bytes']
 if batch:batches.append(batch)
 volumes=[{'name':f'zhongli-all-materials-{i+1:02}.zip','bytes':sum(r['bytes'] for r in b),'files':b} for i,b in enumerate(batches)]
 write(S/'downloads/volumes.json',volumes);write(S/'downloads/manifest.json',{'state':'25组全动作候选+完整历史；所有文件均为站点持久快照','files':manifest,'duplicatePaths':alias,'uniqueFiles':unique})
 # Concrete prebuilt archive for direct conversation download; no dependency on Site access.
 D.mkdir(exist_ok=True);bundle=D/'zhongli-all-actions.zip'
 with zipfile.ZipFile(bundle,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in F.rglob('*'):
   if p.is_file() and p.name!='download-record.json':z.write(p,str(p.relative_to(F)))
  for p in scripts.iterdir():
   if p.suffix in ('.py','.cjs'):z.write(p,'production-scripts/'+p.name)
  for p in (O/'download-materials/standards').rglob('*'):
   if p.is_file():z.write(p,'standards/'+str(p.relative_to(O/'download-materials/standards')))
 with zipfile.ZipFile(bundle) as z:assert z.testzip() is None
 write(F/'download-record.json',{'file':bundle.name,'bytes':bundle.stat().st_size,'sha256':sha(bundle),'zipCRC':'passed','siteVolumes':len(volumes),'generatedOriginals':len(list(originals.glob('*.png')))})
 # Fresh hub: all actions first, clear direct PNG download, bounded ZIP volumes below 18MiB.
 gallery=[]
 for p in sorted(originals.glob('*.png')):
  thumb=S/'thumbnails'/f'{p.stem}.webp';im=Image.open(p).convert('RGBA');im.thumbnail((450,350));im.save(thumb)
  gallery.append(f'<article><a href="generated/{p.name}" target="_blank"><img loading="lazy" src="thumbnails/{p.stem}.webp" alt="生成原图"></a><p>{p.name}</p><a href="generated/{p.name}" download>下载原始PNG</a></article>')
 page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>钟离 · 全动作与生产资料</title><style>body{font:16px/1.7 system-ui;margin:auto;max-width:1250px;padding:24px;background:#171c29;color:#edf0f6}h1{font-size:30px}a{color:#ffd697}nav{display:flex;gap:12px;flex-wrap:wrap}.btn,button{font:inherit;background:#755526;color:#fff;border:1px solid #bd9452;padding:10px 16px;border-radius:6px;cursor:pointer}section{background:#222a3c;padding:22px;margin:24px 0;border:1px solid #49516a;border-radius:10px}.gallery{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px}article{padding:12px;border:1px solid #59617b;border-radius:6px}article img{width:100%;height:240px;object-fit:contain;background:#323b50}article p{font-size:12px;overflow-wrap:anywhere}#progress{white-space:pre-wrap}button:disabled{opacity:.6}.preview{max-width:100%;height:auto}li{margin:8px 0}</style><h1>钟离 · 全动作与生产资料</h1><p>25组动作 · 145显示姿 · 原图、两级拟合、图元、动作卡、提示词与台账齐备。当前是美术素材候选；正式战斗、浏览器、模拟器、真机和用户验收未完成。</p><nav><a class="btn" href="full-actions/">打开全动作播放</a><a class="btn" href="full-actions/checks/all-actions.gif" download>下载全动作GIF</a><a class="btn" href="#packages">下载全部生产资料</a><a class="btn" href="#images">下载生成原图</a></nav><section><h2>全动作总览</h2><a href="full-actions/checks/all-actions.gif"><img class="preview" src="full-actions/checks/all-actions.gif" alt="钟离25组动作总览"></a><p>全动作页可切换源图／初始拟合／优化拟合、深浅背景、镜像、逐tick和慢放；E/Q独立层、Q三分支及双人投技展示齐备。离线包双击offline.html即可播放。</p></section><section id="packages"><h2>保存本轮全部资料</h2><p>各按钮从本站已保存的文件生成一个独立ZIP，每包最多18MiB；无需生图额度。请逐包保存、解压到同一目录，再运行restore-duplicates.py或restore-duplicates.ps1，恢复全部原路径。图片、失败稿、历史、规范、流程和台账均保留。</p><ul id="volumes"></ul><p id="progress" role="status"></p><a href="downloads/manifest.json" download>下载完整SHA256清单</a> · <a href="full-actions/production-ledger.json" download>生产台账</a> · <a href="full-actions/README.md" download>制作流程与交接</a> · <a href="full-actions/action-cards.json" download>动作卡</a> · <a href="full-actions/prompts.json" download>生图指令</a></section><section><h2>历史与恢复</h2><p><a href="review.html">旧库存核对</a> · <a href="batches/20261011-resume/review.html">旧9姿拟合批次</a> · <a href="batches/20261011-refinement/light1-action-review.html">旧轻攻一返修批次</a></p><p>本站保留原有访问权限。若VPN出口仍被Cloudflare拦截，请使用对话中的离线ZIP；站点发布成功不能证明该出口可访问。</p></section><section id="images"><h2>全部实际返回的生成图片</h2><p>'''+str(len(gallery))+'''张原始PNG，包含未采用与失败稿。每张均可直接下载。</p><div class="gallery">'''+''.join(gallery)+'''</div></section><script src="zip-download.js"></script></html>'''
 (S/'index.html').write_text(page);(O/'下载站.html').write_text(page.replace('<meta charset','<base href="https://zhongli-v4-action-review.cwc56154781820.chatgpt.site/"><meta charset',1))
 write(O/'下载交付记录.json',{'materialFiles':len(manifest),'uniqueFiles':len(unique),'aliases':len(alias),'volumes':len(volumes),'generatedImages':len(gallery),'siteBytes':sum(p.stat().st_size for p in S.rglob('*') if p.is_file()),'offlineZIP':str(bundle.relative_to(O)),'verification':'ZIP CRC passed; browser not observed'})
 print({'materialFiles':len(manifest),'uniqueFiles':len(unique),'volumes':len(volumes),'siteMiB':sum(p.stat().st_size for p in S.rglob('*') if p.is_file())/1024**2,'offlineMiB':bundle.stat().st_size/1024**2})
if __name__=='__main__':main()
