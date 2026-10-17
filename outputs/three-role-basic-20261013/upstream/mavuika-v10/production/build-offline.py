from pathlib import Path
import json,base64
root=Path(__file__).resolve().parents[1];d=root/'dist'
rig=json.loads((d/'assets/rig.json').read_text());files={bank['file'] for bank in rig['materials'].values()}|{'mavuika-idle-original.png'}
assets={'assets/'+f:'data:image/png;base64,'+base64.b64encode((d/'assets'/f).read_bytes()).decode() for f in files}
app=(d/'app.js').read_text().replace('i.src=src;', 'i.src=OFFLINE_ASSETS[src]||src;')
start="fetch('assets/rig.json').then(r=>{if(!r.ok)throw Error('动作锚点未能加载');return r.json();})"
assert start in app;app=app.replace(start,'Promise.resolve('+json.dumps(rig,separators=(',',':'))+')')
html=(d/'index.html').read_text().replace('<link rel="stylesheet" href="style.css">','<style>'+(d/'style.css').read_text()+'</style>')
html=html.replace('<script src="q-model.js"></script><script src="app.js"></script>','<script>const OFFLINE_ASSETS='+json.dumps(assets,separators=(',',':'))+';</script><script>'+(d/'q-model.js').read_text()+'</script><script>'+app+'</script>')
(d/'offline.html').write_text(html)
print('Offline HTML created; assets embedded, no fetch required.')
