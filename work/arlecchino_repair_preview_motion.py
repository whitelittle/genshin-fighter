from pathlib import Path
p=Path('outputs/arlecchino-actions-20261011/player.js');s=p.read_text(encoding='utf-8');s=s.replace("kind==='jump'&&.checked", "kind==='jump'&&$('movement').checked");p.write_text(s,encoding='utf-8')
