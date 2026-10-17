from pathlib import Path
import re,shutil
r=Path.cwd();o=r/'outputs/arlecchino-actions-20261011';c=r/'outputs/clorinde-actions-20261011'
html=(c/'player.html').read_text(encoding='utf-8').replace('克洛琳德','阿蕾奇诺').replace('25组动作候选','制作中 · 2组/8姿候选').replace('交付说明.md','制作与交付.md').replace('body-review.html','evidence/mother-extracted-light-dark.jpg').replace('verification.json','fitting-verification.json').replace('<script src="effect-data.js"></script>','')
for name in ['fx','opponent','enemyModel','branch']:html=re.sub(r'<label>[^<]*(?:<input id="'+name+r'"[^>]*>[^<]*|<select id="'+name+r'">.*?</select>)</label>','',html)
(o/'player.html').write_text(html,encoding='utf-8');(o/'index.html').write_text(html,encoding='utf-8');shutil.copy2(c/'player.css',o/'player.css')
