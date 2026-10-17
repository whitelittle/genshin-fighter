from pathlib import Path
import json,base64
root=Path(__file__).resolve().parents[1];d=root/'dist';a=d/'assets'
body=json.loads((a/'neutral-rig-v6.json').read_text());fx=json.loads((a/'light1-fx-rig-v7.json').read_text());target=json.loads((a/'v3-target-rig-v7.json').read_text())
files={g[m] for k,g in body['groups'].items() if k in ['idle','light1'] for m in ['source','initial','optimized']}|{fx['source'],fx['fit'],target['file'],'v3-target-flash-v7.png'}
assets={'assets/'+file:'data:image/png;base64,'+base64.b64encode((a/file).read_bytes()).decode() for file in files}
data={'assets/neutral-rig-v6.json':body,'assets/light1-fx-rig-v7.json':fx,'assets/v3-target-rig-v7.json':target}
app=(d/'fx-review-v7.js').read_text().replace('image.src=src;','image.src=FX_OFFLINE_ASSETS[src]||src;')
old="const fjson=url=>fetch(url).then(r=>{if(!r.ok)throw Error('数据未能加载：'+url);return r.json();});";assert old in app
app=app.replace(old,'const fjson=url=>Promise.resolve(FX_OFFLINE_DATA[url]);')
html=(d/'fx-review-v7.html').read_text().replace('<link rel="stylesheet" href="style.css">','<style>'+(d/'style.css').read_text()+'</style>').replace('<a href="index.html">回到动作制作</a>','<span>离线查看器 · 无需登录</span>')
html=html.replace('<p><a href="review/mavuika-fx-branches-v7.gif">命中／防御／挥空动图</a> · <a href="review/mavuika-fx-sheet-v7.png">特效分层对照图</a></p>','')
html=html.replace('<script src="light1-model.js"></script><script src="light1-fx-model-v7.js"></script><script src="fx-review-v7.js"></script>','<script>const FX_OFFLINE_ASSETS='+json.dumps(assets,separators=(',',':'))+';const FX_OFFLINE_DATA='+json.dumps(data,separators=(',',':'))+';</script><script>'+(d/'light1-model.js').read_text()+'</script><script>'+(d/'light1-fx-model-v7.js').read_text()+'</script><script>'+app+'</script>')
(d/'mavuika-fx-offline-v7.html').write_text(html);assert 'fetch(' not in html and '<script src=' not in html
print('Standalone FX review generated with embedded images/data; no fetch or external scripts.')
