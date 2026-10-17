from pathlib import Path
import json,base64,re
r=Path(__file__).resolve().parents[1];d=r/'dist';a=d/'assets';rig=json.loads((a/'rig.json').read_text());fx=json.loads((a/'q-fx-rig-v8.json').read_text());lfx=json.loads((a/'light1-fx-rig-v7.json').read_text());target=json.loads((a/'v3-target-rig-v7.json').read_text());data={'rig.json':rig,'q-fx-rig-v8.json':fx,'light1-fx-rig-v7.json':lfx,'v3-target-rig-v7.json':target};files={b['file'] for b in rig['materials'].values()}|{'mavuika-idle-original.png',fx['fit'],lfx['fit'],target['file'],'v3-target-flash-v7.png'}
assets={'assets/'+f:'data:image/png;base64,'+base64.b64encode((a/f).read_bytes()).decode() for f in files};data={'assets/'+k:v for k,v in data.items()}
app=(d/'app.js').read_text().replace('i.src=src;','i.src=OFFLINE_ASSETS[src]||src;')
app=re.sub(r"fetch\('assets/rig.json'\)\.then\(r=>\{if\(!r.ok\)throw Error\('动作锚点未能加载'\);return r.json\(\);\}\)","Promise.resolve(OFFLINE_DATA['assets/rig.json'])",app)
app=app.replace("fetch('assets/'+f).then(r=>{if(!r.ok)throw Error('特效数据加载失败');return r.json();})","Promise.resolve(OFFLINE_DATA['assets/'+f])")
html=(d/'index.html').read_text();html=html.replace('<link rel="stylesheet" href="style.css">','<style>'+(d/'style.css').read_text()+'</style>');html=re.sub(r'<p><a href="(?:neutral-review|review/|fx-review|mavuika-q-fx-offline)[\s\S]*?</p>','',html)
html=html.replace('<script src="q-model.js"></script><script src="q-fx-model-v8.js"></script><script src="app.js"></script>','<script>const OFFLINE_ASSETS='+json.dumps(assets,separators=(',',':'))+';const OFFLINE_DATA='+json.dumps(data,separators=(',',':'))+';</script><script>'+(d/'q-model.js').read_text()+'</script><script>'+(d/'q-fx-model-v8.js').read_text()+'</script><script>'+app+'</script>')
assert 'fetch(' not in html and '<script src=' not in html
(d/'mavuika-q-fx-offline-v8.html').write_text(html);print('Offline images and data embedded')
